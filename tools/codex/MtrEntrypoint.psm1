Set-StrictMode -Version Latest

function New-MtrParentDirectory {
    param([Parameter(Mandatory=$true)][string]$Path)

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
}

function ConvertTo-MtrCliArgument {
    [CmdletBinding()]
    param([AllowNull()][object]$Argument)

    $text = if ($null -eq $Argument) { "" } else { [string]$Argument }
    if ($text.Length -eq 0) { return '""' }
    if ($text -notmatch '[\s"]') { return $text }

    # Windows CreateProcess receives one command-line string. Start-Process with
    # an object array can split paths with spaces incorrectly for some targets,
    # so we apply the standard CommandLineToArgvW-compatible quoting rule.
    $builder = [System.Text.StringBuilder]::new()
    [void]$builder.Append('"')
    $backslashCount = 0

    foreach ($character in $text.ToCharArray()) {
        if ($character -eq [char]92) {
            $backslashCount += 1
            continue
        }

        if ($character -eq [char]34) {
            if ($backslashCount -gt 0) {
                [void]$builder.Append(('\' * ($backslashCount * 2)))
            }
            [void]$builder.Append('\"')
            $backslashCount = 0
            continue
        }

        if ($backslashCount -gt 0) {
            [void]$builder.Append(('\' * $backslashCount))
            $backslashCount = 0
        }
        [void]$builder.Append($character)
    }

    if ($backslashCount -gt 0) {
        [void]$builder.Append(('\' * ($backslashCount * 2)))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function ConvertTo-MtrArgumentString {
    [CmdletBinding()]
    param([object[]]$ArgumentList = @())

    return (@($ArgumentList) | ForEach-Object { ConvertTo-MtrCliArgument $_ }) -join ' '
}

function Resolve-MtrExecutable {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$FilePath)

    $expanded = [Environment]::ExpandEnvironmentVariables($FilePath)
    if (Test-Path -LiteralPath $expanded -PathType Leaf) {
        return (Resolve-Path -LiteralPath $expanded).Path
    }

    $command = Get-Command -Name $expanded -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command -and $command.Source) {
        return $command.Source
    }

    throw "Entrypoint executable not found: $FilePath"
}

function Get-MtrRedactedArguments {
    [CmdletBinding()]
    param([object[]]$ArgumentList = @())

    $result = [System.Collections.Generic.List[string]]::new()
    $redactNext = $false
    foreach ($argument in @($ArgumentList)) {
        $text = if ($null -eq $argument) { "" } else { [string]$argument }
        if ($redactNext) {
            $result.Add('<redacted>')
            $redactNext = $false
            continue
        }

        if ($text -match '(?i)(token|secret|password|passwd|api[_-]?key|authorization)') {
            if ($text -match '=') {
                $result.Add(($text -replace '=(.*)$', '=<redacted>'))
            } else {
                $result.Add($text)
                $redactNext = $true
            }
            continue
        }

        $result.Add($text)
    }

    return @($result)
}

function Write-MtrEntrypointLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$LogPath,
        [Parameter(Mandatory=$true)][hashtable]$Record
    )

    New-MtrParentDirectory -Path $LogPath
    $Record.timestampUtc = (Get-Date).ToUniversalTime().ToString('o')
    ($Record | ConvertTo-Json -Depth 24 -Compress) | Add-Content -LiteralPath $LogPath -Encoding UTF8
}

function Stop-MtrProcessTree {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][int]$ProcessId)

    try {
        $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue)
        foreach ($child in $children) {
            Stop-MtrProcessTree -ProcessId ([int]$child.ProcessId)
        }
    } catch {
        # Process tree cleanup is best-effort; the caller still verifies the main process state.
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Get-MtrSha256Hex {
    [CmdletBinding()]
    param([AllowNull()][string]$Text)

    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($(if ($null -eq $Text) { '' } else { $Text }))
        $hash = $sha256.ComputeHash($bytes)
        return ([BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha256.Dispose()
    }
}

function Test-MtrSuccessPattern {
    [CmdletBinding()]
    param(
        [string[]]$Path = @(),
        [string[]]$Pattern = @(),
        [AllowNull()][System.Collections.IDictionary]$StateByPath,
        [ValidateRange(1024, 1048576)][int]$MaxNewBytes = 1048576,
        [ValidateRange(128, 8192)][int]$TailCharacters = 4096
    )

    foreach ($candidate in @($Path)) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }

        $text = ''
        $state = if ($null -ne $StateByPath -and $StateByPath.Contains($candidate)) {
            $StateByPath[$candidate]
        } else {
            [pscustomobject]@{ offset = 0L; tail = '' }
        }
        $startOffset = [int64]$state.offset
        try {
            $stream = [System.IO.File]::Open(
                $candidate,
                [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::Read,
                [System.IO.FileShare]::ReadWrite
            )
            try {
                # Snapshot length after opening and read exactly that bounded
                # byte range; concurrent appends remain for the next cursor.
                $endOffset = [int64]$stream.Length
                if ($endOffset -lt $startOffset) {
                    # The producer replaced or truncated the log after launch.
                    $startOffset = 0L
                    $state.offset = 0L
                    $state.tail = ''
                }
                if ($endOffset -le $startOffset) { continue }
                $newByteCount = $endOffset - $startOffset
                if ($newByteCount -gt $MaxNewBytes) {
                    return [pscustomobject]@{
                        matched = $false
                        overflowed = $true
                        path = $candidate
                        pattern = $null
                        startOffset = $startOffset
                        endOffset = $endOffset
                        maxNewBytes = $MaxNewBytes
                    }
                }
                [void]$stream.Seek($startOffset, [System.IO.SeekOrigin]::Begin)
                $buffer = [byte[]]::new([int]$newByteCount)
                $bytesRead = 0
                while ($bytesRead -lt $buffer.Length) {
                    $read = $stream.Read($buffer, $bytesRead, $buffer.Length - $bytesRead)
                    if ($read -le 0) { break }
                    $bytesRead += $read
                }
                $text = [string]$state.tail + [Text.Encoding]::UTF8.GetString($buffer, 0, $bytesRead)
            } finally {
                $stream.Dispose()
            }
            $state.offset = $startOffset + $bytesRead
            $state.tail = if ($text.Length -gt $TailCharacters) {
                $text.Substring($text.Length - $TailCharacters)
            } else { $text }
        } catch {
            $text = ''
        }

        if ([string]::IsNullOrWhiteSpace($text)) { continue }
        foreach ($patternText in @($Pattern)) {
            if ([string]::IsNullOrWhiteSpace($patternText)) { continue }
            if ($text -match $patternText) {
                return [pscustomobject]@{
                    matched = $true
                    overflowed = $false
                    path = $candidate
                    pattern = $patternText
                    startOffset = $startOffset
                    endOffset = $state.offset
                }
            }
        }
    }

    return [pscustomobject]@{
        matched = $false
        overflowed = $false
        path = $null
        pattern = $null
        startOffset = $null
        endOffset = $null
        maxNewBytes = $MaxNewBytes
    }
}

function Invoke-MtrEntrypoint {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [object[]]$ArgumentList = @(),
        [string]$WorkingDirectory = (Get-Location).Path,
        [string]$LogPath = (Join-Path (Get-Location).Path ("logs\entrypoint-router-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd'))),
        [string]$RedirectStandardOutput,
        [string]$RedirectStandardError,
        [System.Diagnostics.ProcessWindowStyle]$WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden,
        [switch]$Wait,
        [switch]$PassThru,
        [int]$TimeoutSeconds = 0,
        [string[]]$SuccessLogPath = @(),
        [string[]]$SuccessPattern = @(),
        [int]$SuccessPollIntervalMilliseconds = 1000,
        [ValidateRange(1024, 1048576)][int]$SuccessScanChunkLimitBytes = 1048576
    )

    $resolvedFilePath = Resolve-MtrExecutable -FilePath $FilePath
    if (-not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
        throw "Entrypoint working directory not found: $WorkingDirectory"
    }
    $resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory).Path
    $argumentString = ConvertTo-MtrArgumentString -ArgumentList $ArgumentList
    $redactedArguments = Get-MtrRedactedArguments -ArgumentList $ArgumentList

    $autocorrections = [System.Collections.Generic.List[string]]::new()
    $autocorrections.Add('argument-array-to-safe-command-line')
    if (@($ArgumentList | Where-Object { ([string]$_) -match '[\s"]' }).Count -gt 0) {
        $autocorrections.Add('quoted-whitespace-or-quote-arguments')
    }
    $successLogStates = [System.Collections.Hashtable]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($candidate in @($SuccessLogPath)) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        $baselineLength = if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            [int64](Get-Item -LiteralPath $candidate).Length
        } else { 0L }
        $successLogStates[$candidate] = [pscustomobject]@{
            offset = $baselineLength
            tail = ''
        }
    }
    if ($resolvedFilePath -ne $FilePath) {
        $autocorrections.Add('resolved-executable')
    }

    if ($RedirectStandardOutput) { New-MtrParentDirectory -Path $RedirectStandardOutput }
    if ($RedirectStandardError) { New-MtrParentDirectory -Path $RedirectStandardError }

    $startRecord = @{
        event = 'entrypoint.start'
        tool = 'mtr-entrypoint-router'
        filePath = $resolvedFilePath
        originalFilePath = $FilePath
        workingDirectory = $resolvedWorkingDirectory
        argumentCount = @($ArgumentList).Count
        arguments = $redactedArguments
        argumentStringSha256 = Get-MtrSha256Hex -Text $argumentString
        redirects = @{
            stdout = $RedirectStandardOutput
            stderr = $RedirectStandardError
        }
        autocorrections = @($autocorrections)
        wait = [bool]$Wait
        timeoutSeconds = $TimeoutSeconds
        successLogPath = @($SuccessLogPath)
        successPatternCount = @($SuccessPattern).Count
    }
    Write-MtrEntrypointLog -LogPath $LogPath -Record $startRecord

    $process = $null
    $stdoutTask = $null
    $stderrTask = $null
    $completedBySuccessPattern = $false
    $successMatch = $null
    $successEvidenceOverflow = $false
    if ($Wait) {
        $processInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $processInfo.FileName = $resolvedFilePath
        $processInfo.WorkingDirectory = $resolvedWorkingDirectory
        $processInfo.Arguments = $argumentString
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = ($WindowStyle -eq [System.Diagnostics.ProcessWindowStyle]::Hidden)

        if ($RedirectStandardOutput) { $processInfo.RedirectStandardOutput = $true }
        if ($RedirectStandardError) { $processInfo.RedirectStandardError = $true }

        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $processInfo
        try {
            [void]$process.Start()
            if ($RedirectStandardOutput) { $stdoutTask = $process.StandardOutput.ReadToEndAsync() }
            if ($RedirectStandardError) { $stderrTask = $process.StandardError.ReadToEndAsync() }
        } catch {
            Write-MtrEntrypointLog -LogPath $LogPath -Record @{
                event = 'entrypoint.failed'
                tool = 'mtr-entrypoint-router'
                filePath = $resolvedFilePath
                workingDirectory = $resolvedWorkingDirectory
                error = $_.Exception.Message
            }
            throw
        }
    } else {
        $startParams = @{
            FilePath = $resolvedFilePath
            WorkingDirectory = $resolvedWorkingDirectory
            WindowStyle = $WindowStyle
            PassThru = $true
        }
        if ($argumentString.Length -gt 0) { $startParams.ArgumentList = $argumentString }
        if ($RedirectStandardOutput) { $startParams.RedirectStandardOutput = $RedirectStandardOutput }
        if ($RedirectStandardError) { $startParams.RedirectStandardError = $RedirectStandardError }

        try {
            $process = Start-Process @startParams
        } catch {
            Write-MtrEntrypointLog -LogPath $LogPath -Record @{
                event = 'entrypoint.failed'
                tool = 'mtr-entrypoint-router'
                filePath = $resolvedFilePath
                workingDirectory = $resolvedWorkingDirectory
                error = $_.Exception.Message
            }
            throw
        }
    }

    $timedOut = $false
    if ($Wait) {
        if ($TimeoutSeconds -gt 0) {
            $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
            $exited = $false
            $pollMs = [Math]::Max(250, $SuccessPollIntervalMilliseconds)
            do {
                $exited = $process.WaitForExit($pollMs)
                if ($exited -and $process.ExitCode -ne 0) { break }
                if (@($SuccessPattern).Count -gt 0 -and @($SuccessLogPath).Count -gt 0) {
                    $match = Test-MtrSuccessPattern `
                        -Path $SuccessLogPath `
                        -Pattern $SuccessPattern `
                        -StateByPath $successLogStates `
                        -MaxNewBytes $SuccessScanChunkLimitBytes
                    if ($match.overflowed) {
                        $successEvidenceOverflow = $true
                        $successMatch = $match
                        Write-MtrEntrypointLog -LogPath $LogPath -Record @{
                            event = 'entrypoint.success-log-overflow'
                            tool = 'mtr-entrypoint-router'
                            filePath = $resolvedFilePath
                            workingDirectory = $resolvedWorkingDirectory
                            processId = $process.Id
                            successMatch = $successMatch
                            action = 'stop-process-tree-fail-closed'
                        }
                        if (-not $exited) {
                            Stop-MtrProcessTree -ProcessId $process.Id
                            [void]$process.WaitForExit(10000)
                        }
                        break
                    }
                    if ($match.matched) {
                        $completedBySuccessPattern = $true
                        $successMatch = $match
                        Write-MtrEntrypointLog -LogPath $LogPath -Record @{
                            event = 'entrypoint.success-pattern'
                            tool = 'mtr-entrypoint-router'
                            filePath = $resolvedFilePath
                            workingDirectory = $resolvedWorkingDirectory
                            processId = $process.Id
                            successMatch = $successMatch
                            action = 'stop-process-tree-after-success-log'
                        }
                        if (-not $exited) {
                            Stop-MtrProcessTree -ProcessId $process.Id
                            [void]$process.WaitForExit(10000)
                        }
                        break
                    }
                }
                if ($exited) { break }
            } while ((Get-Date) -lt $deadline)

            if (-not $exited -and -not $completedBySuccessPattern -and -not $successEvidenceOverflow) {
                $process.Refresh()
                $timedOut = $true
                Stop-MtrProcessTree -ProcessId $process.Id
            }
        } else {
            $process.WaitForExit()
        }
        if ($process.HasExited) {
            $process.WaitForExit()
        }
        $process.Refresh()
    }

    if ($stdoutTask -and $RedirectStandardOutput) {
        [System.IO.File]::WriteAllText($RedirectStandardOutput, $stdoutTask.Result, [Text.Encoding]::UTF8)
    }
    if ($stderrTask -and $RedirectStandardError) {
        [System.IO.File]::WriteAllText($RedirectStandardError, $stderrTask.Result, [Text.Encoding]::UTF8)
    }

    $exitCode = $null
    if ($process.HasExited) { $exitCode = $process.ExitCode }
    $logicalExitCode = if ($completedBySuccessPattern) { 0 } else { $exitCode }

    $result = [pscustomobject]@{
        filePath = $resolvedFilePath
        workingDirectory = $resolvedWorkingDirectory
        processId = $process.Id
        hasExited = $process.HasExited
        exitCode = $exitCode
        logicalExitCode = $logicalExitCode
        timedOut = $timedOut
        completedBySuccessPattern = $completedBySuccessPattern
        successMatch = $successMatch
        successEvidenceOverflow = $successEvidenceOverflow
        logPath = $LogPath
        stdout = $RedirectStandardOutput
        stderr = $RedirectStandardError
        autocorrections = @($autocorrections)
    }

    Write-MtrEntrypointLog -LogPath $LogPath -Record @{
        event = if ($timedOut) { 'entrypoint.timeout' } elseif ($process.HasExited) { 'entrypoint.completed' } else { 'entrypoint.detached' }
        tool = 'mtr-entrypoint-router'
        filePath = $resolvedFilePath
        workingDirectory = $resolvedWorkingDirectory
        processId = $process.Id
        hasExited = $process.HasExited
        exitCode = $exitCode
        logicalExitCode = $logicalExitCode
        timedOut = $timedOut
        completedBySuccessPattern = $completedBySuccessPattern
        successMatch = $successMatch
        successEvidenceOverflow = $successEvidenceOverflow
        stdout = $RedirectStandardOutput
        stderr = $RedirectStandardError
        autocorrections = @($autocorrections)
    }

    if ($timedOut) {
        throw "Entrypoint timed out after $TimeoutSeconds seconds: $resolvedFilePath"
    }
    if ($successEvidenceOverflow) {
        throw "Entrypoint success log exceeded the bounded scan chunk: $($successMatch.path)"
    }

    return $result
}

function Test-MtrEntrypointQuoting {
    [CmdletBinding()]
    param(
        [string]$LogPath = (Join-Path (Get-Location).Path ("logs\entrypoint-router-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd')))
    )

    $tempRoot = Join-Path $env:TEMP ("mtr entrypoint quoting {0}" -f ([Guid]::NewGuid().ToString('N')))
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
    $payloadPath = Join-Path $tempRoot 'payload path with spaces.txt'
    $stdoutPath = Join-Path $tempRoot 'stdout.txt'
    $stderrPath = Join-Path $tempRoot 'stderr.txt'
    $successLogPath = Join-Path $tempRoot 'success.log'
    $python = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $python -or -not $python.Source) {
        throw 'Python executable is required for MTR entrypoint quoting self-test.'
    }
    $script = "import pathlib, sys; pathlib.Path(sys.argv[1]).write_text('ok:path-with-spaces', encoding='utf-8')"

    try {
        $run = Invoke-MtrEntrypoint `
            -FilePath $python.Source `
            -ArgumentList @('-c', $script, $payloadPath) `
            -WorkingDirectory (Get-Location).Path `
            -LogPath $LogPath `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -Wait `
            -TimeoutSeconds 30 `
            -PassThru

        'MTR_CURRENT_SUCCESS' | Set-Content -LiteralPath $successLogPath -Encoding UTF8
        $staleOnlyRun = Invoke-MtrEntrypoint `
            -FilePath $python.Source `
            -ArgumentList @('-c', 'import time; time.sleep(0.35)') `
            -WorkingDirectory (Get-Location).Path `
            -LogPath $LogPath `
            -Wait `
            -TimeoutSeconds 5 `
            -SuccessLogPath @($successLogPath) `
            -SuccessPattern @('MTR_CURRENT_SUCCESS') `
            -SuccessPollIntervalMilliseconds 100 `
            -PassThru

        $appendSuccessScript = "import pathlib, sys, time; time.sleep(0.2); pathlib.Path(sys.argv[1]).open('a', encoding='utf-8').write('MTR_CURRENT_SUCCESS\n'); time.sleep(1)"
        $currentSuccessRun = Invoke-MtrEntrypoint `
            -FilePath $python.Source `
            -ArgumentList @('-c', $appendSuccessScript, $successLogPath) `
            -WorkingDirectory (Get-Location).Path `
            -LogPath $LogPath `
            -Wait `
            -TimeoutSeconds 5 `
            -SuccessLogPath @($successLogPath) `
            -SuccessPattern @('MTR_CURRENT_SUCCESS') `
            -SuccessPollIntervalMilliseconds 100 `
            -PassThru

        $appendThenFailScript = "import pathlib, sys; pathlib.Path(sys.argv[1]).open('a', encoding='utf-8').write('MTR_CURRENT_SUCCESS\n'); raise SystemExit(7)"
        $nonzeroAfterSuccessRun = Invoke-MtrEntrypoint `
            -FilePath $python.Source `
            -ArgumentList @('-c', $appendThenFailScript, $successLogPath) `
            -WorkingDirectory (Get-Location).Path `
            -LogPath $LogPath `
            -Wait `
            -TimeoutSeconds 5 `
            -SuccessLogPath @($successLogPath) `
            -SuccessPattern @('MTR_CURRENT_SUCCESS') `
            -SuccessPollIntervalMilliseconds 100 `
            -PassThru

        $overflowRejected = $false
        $overflowScript = "import pathlib, sys, time; pathlib.Path(sys.argv[1]).open('a', encoding='utf-8').write('X' * 2048); time.sleep(1)"
        try {
            Invoke-MtrEntrypoint `
                -FilePath $python.Source `
                -ArgumentList @('-c', $overflowScript, $successLogPath) `
                -WorkingDirectory (Get-Location).Path `
                -LogPath $LogPath `
                -Wait `
                -TimeoutSeconds 5 `
                -SuccessLogPath @($successLogPath) `
                -SuccessPattern @('MTR_CURRENT_SUCCESS') `
                -SuccessPollIntervalMilliseconds 100 `
                -SuccessScanChunkLimitBytes 1024 `
                -PassThru | Out-Null
        } catch {
            $overflowRejected = $_.Exception.Message -match 'bounded scan chunk'
        }

        $content = if (Test-Path -LiteralPath $payloadPath) { Get-Content -LiteralPath $payloadPath -Raw } else { '' }
        $passed = (
            $run.exitCode -eq 0 -and
            $content.Trim() -eq 'ok:path-with-spaces' -and
            -not $staleOnlyRun.completedBySuccessPattern -and
            $staleOnlyRun.logicalExitCode -eq 0 -and
            $currentSuccessRun.completedBySuccessPattern -and
            $currentSuccessRun.logicalExitCode -eq 0 -and
            -not $nonzeroAfterSuccessRun.completedBySuccessPattern -and
            $nonzeroAfterSuccessRun.exitCode -eq 7 -and
            $nonzeroAfterSuccessRun.logicalExitCode -eq 7 -and
            $overflowRejected
        )
        Write-MtrEntrypointLog -LogPath $LogPath -Record @{
            event = 'entrypoint.selftest'
            tool = 'mtr-entrypoint-router'
            name = 'path-with-spaces'
            passed = $passed
            exitCode = $run.exitCode
            payloadPath = $payloadPath
            staleSuccessRejected = -not $staleOnlyRun.completedBySuccessPattern
            currentSuccessAccepted = [bool]$currentSuccessRun.completedBySuccessPattern
            nonzeroExitPrecedence = ($nonzeroAfterSuccessRun.logicalExitCode -eq 7)
            boundedSuccessLogOverflowRejected = $overflowRejected
        }

        return [pscustomobject]@{
            passed = $passed
            exitCode = $run.exitCode
            payloadPath = $payloadPath
            logPath = $LogPath
            staleSuccessRejected = -not $staleOnlyRun.completedBySuccessPattern
            currentSuccessAccepted = [bool]$currentSuccessRun.completedBySuccessPattern
            nonzeroExitPrecedence = ($nonzeroAfterSuccessRun.logicalExitCode -eq 7)
            boundedSuccessLogOverflowRejected = $overflowRejected
        }
    } finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Export-ModuleMember -Function ConvertTo-MtrCliArgument, ConvertTo-MtrArgumentString, Resolve-MtrExecutable, Invoke-MtrEntrypoint, Test-MtrEntrypointQuoting
