[CmdletBinding()]
param(
    [string]$Serial = 'emulator-5554',
    [ValidateRange(1, 99)]
    [int]$Cycle = 1,
    [string]$OutputDir = 'docs\qa\evidence\android_emulator_interaction',
    [ValidateRange(1, 100)]
    [int]$RestartIterations = 10,
    [ValidateRange(30, 1800)]
    [int]$SoakSeconds = 300,
    [ValidateRange(10, 120)]
    [int]$MarkerTimeoutSeconds = 35
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($Serial -notmatch '^emulator-\d+$') {
    throw "Emulator-only guard rejected serial '$Serial' before any ADB call."
}

$adbPath = (Get-Command adb -ErrorAction Stop).Source
$component = 'com.martyskin.trudrunner/com.cocos.game.AppActivity'
$packageName = 'com.martyskin.trudrunner'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$resolvedOutputDir = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputDir))
[System.IO.Directory]::CreateDirectory($resolvedOutputDir) | Out-Null
$runStartedAt = Get-Date
$currentQaPhase = 'bootstrap'

function Invoke-MtrAdb {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = @(& $adbPath -s $Serial @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    $text = $output -join "`n"
    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "adb failed ($exitCode): $($Arguments -join ' ')`n$text"
    }
    return $text
}

function Disable-MtrEmulatorAudio {
    $setOutput = Invoke-MtrAdb -Arguments @(
        'shell', 'cmd', 'media_session', 'volume', '--stream', '3', '--set', '0'
    )
    $state = Invoke-MtrAdb -Arguments @(
        'shell', 'cmd', 'media_session', 'volume', '--stream', '3', '--get'
    )
    $volumeMatch = [regex]::Match($state, 'volume is (?<volume>\d+)\b')
    if (-not $volumeMatch.Success -or [int]$volumeMatch.Groups['volume'].Value -ne 0) {
        throw "Emulator audio mute precondition failed: $state"
    }
    return [pscustomobject]@{
        policy = 'host-no-audio-plus-media-stream-zero'
        startup_argument_required = '-no-audio'
        media_stream = 3
        volume = 0
        set_output = $setOutput
        verification = $state
    }
}

function Write-MtrUtf8 {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Text
    )

    [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

function Read-MtrLogcat {
    return Invoke-MtrAdb -Arguments @('logcat', '-d', '-v', 'threadtime')
}

function Read-MtrRecentCocosLog {
    return Invoke-MtrAdb -Arguments @('logcat', '-d', '-t', '1200', '-v', 'brief', 'Cocos:D', '*:S')
}

function Wait-MtrLogMarker {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Pattern,
        [ValidateRange(1, 120)]
        [int]$TimeoutSeconds = $MarkerTimeoutSeconds,
        [ValidateRange(50, 2000)]
        [int]$PollMilliseconds = 300
    )

    $started = Get-Date
    $deadline = $started.AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Milliseconds $PollMilliseconds
        $log = Read-MtrLogcat
        if ([regex]::IsMatch($log, $Pattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
            return [pscustomobject]@{
                Found = $true
                WaitMs = [int]((Get-Date) - $started).TotalMilliseconds
                Log = $log
            }
        }
    } while ((Get-Date) -lt $deadline)

    return [pscustomobject]@{
        Found = $false
        WaitMs = [int]((Get-Date) - $started).TotalMilliseconds
        Log = Read-MtrLogcat
    }
}

function Start-MtrActivity {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Extras
    )

    $arguments = [System.Collections.Generic.List[string]]::new()
    foreach ($argument in @('shell', 'am', 'start', '-S', '-n', $component)) {
        $arguments.Add($argument)
    }
    foreach ($entry in $Extras.GetEnumerator()) {
        $arguments.Add('--es')
        $arguments.Add([string]$entry.Key)
        $arguments.Add([string]$entry.Value)
    }
    return Invoke-MtrAdb -Arguments $arguments.ToArray()
}

function Save-MtrScreenshot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $safeName = $Name -replace '[^A-Za-z0-9_.-]', '_'
    $remote = "/sdcard/mtr_${safeName}.png"
    $local = Join-Path $resolvedOutputDir "${safeName}.png"
    Invoke-MtrAdb -Arguments @('shell', 'screencap', '-p', $remote) | Out-Null
    Invoke-MtrAdb -Arguments @('pull', $remote, $local) | Out-Null
    Invoke-MtrAdb -Arguments @('shell', 'rm', $remote) -AllowFailure | Out-Null
    return $local
}

function Get-MtrWindowSize {
    $windowDump = Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'window', 'displays')
    $match = [regex]::Match($windowDump, 'cur=(?<width>\d+)x(?<height>\d+)')
    if (-not $match.Success) {
        throw 'Unable to determine current emulator application window size.'
    }
    return [pscustomobject]@{
        Width = [int]$match.Groups['width'].Value
        Height = [int]$match.Groups['height'].Value
    }
}

function Convert-MtrPoint {
    param(
        [Parameter(Mandatory = $true)]
        [double]$DesignX,
        [Parameter(Mandatory = $true)]
        [double]$DesignY,
        [Parameter(Mandatory = $true)]
        [object]$WindowSize
    )

    return [pscustomobject]@{
        X = [int][Math]::Round($DesignX / 1280.0 * $WindowSize.Width)
        Y = [int][Math]::Round($DesignY / 720.0 * $WindowSize.Height)
    }
}

function Invoke-MtrTap {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Point
    )
    Invoke-MtrAdb -Arguments @(
        'shell', 'input', 'touchscreen', '-d', '0', 'tap',
        [string]$Point.X, [string]$Point.Y
    ) | Out-Null
}

function Get-MtrCurrentFocus {
    $windowDump = Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'window', 'displays')
    $match = [regex]::Match($windowDump, 'mCurrentFocus=[^\r\n]+')
    if ($match.Success) { return $match.Value }
    return ''
}

function Wait-MtrAppInputReady {
    $started = Get-Date
    $deadline = $started.AddSeconds($MarkerTimeoutSeconds)
    $stableSamples = 0
    $lastFocus = ''
    $componentPattern = [regex]::Escape($component)

    do {
        $lastFocus = Get-MtrCurrentFocus
        $inputDump = Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'input') -AllowFailure
        $focused = $lastFocus -match $componentPattern
        $responsiveChannel = [regex]::IsMatch(
            $inputDump,
            "channelName='[^']*$componentPattern \(server\)', status=NORMAL[^\r\n]*responsive=true",
            [Text.RegularExpressions.RegexOptions]::IgnoreCase
        )
        if ($focused -and $responsiveChannel) {
            $stableSamples += 1
            if ($stableSamples -ge 4) {
                return [pscustomobject]@{
                    Found = $true
                    WaitMs = [int]((Get-Date) - $started).TotalMilliseconds
                    Focus = $lastFocus
                    StableSamples = $stableSamples
                }
            }
        } else {
            $stableSamples = 0
        }
        Start-Sleep -Milliseconds 200
    } while ((Get-Date) -lt $deadline)

    return [pscustomobject]@{
        Found = $false
        WaitMs = [int]((Get-Date) - $started).TotalMilliseconds
        Focus = $lastFocus
        StableSamples = $stableSamples
    }
}

function Invoke-MtrVerifiedTap {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Point,
        [Parameter(Mandatory = $true)]
        [string]$Pattern,
        [ValidateRange(1, 3)]
        [int]$MaxAttempts = 3,
        [ValidateRange(1, 10)]
        [int]$PerAttemptTimeoutSeconds = 3
    )

    $attempts = [System.Collections.Generic.List[object]]::new()
    $stopwatch = [Diagnostics.Stopwatch]::StartNew()
    $lastWait = $null

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $focusBeforeTap = Get-MtrCurrentFocus
        Invoke-MtrTap -Point $Point
        $lastWait = Wait-MtrLogMarker -Pattern $Pattern -TimeoutSeconds $PerAttemptTimeoutSeconds
        $attempts.Add([pscustomobject]@{
            attempt = $attempt
            found = $lastWait.Found
            marker_wait_ms = $lastWait.WaitMs
            focus_before_tap = $focusBeforeTap
        })

        if ($lastWait.Found) {
            $stopwatch.Stop()
            return [pscustomobject]@{
                Found = $true
                WaitMs = [int]$stopwatch.ElapsedMilliseconds
                AttemptCount = $attempt
                Attempts = @($attempts)
                Log = $lastWait.Log
            }
        }

        if ($attempt -lt $MaxAttempts) {
            $inputReadyAfterMiss = Wait-MtrAppInputReady
            if (-not $inputReadyAfterMiss.Found) { break }
            Start-Sleep -Milliseconds 400
        }
    }

    $stopwatch.Stop()
    return [pscustomobject]@{
        Found = $false
        WaitMs = [int]$stopwatch.ElapsedMilliseconds
        AttemptCount = $attempts.Count
        Attempts = @($attempts)
        Log = if ($null -ne $lastWait) { $lastWait.Log } else { Read-MtrLogcat }
    }
}

function Close-MtrNativeEditor {
    for ($attempt = 0; $attempt -lt 3; $attempt++) {
        $focus = Get-MtrCurrentFocus
        if ($focus -match 'com\.cocos\.game\.AppActivity') { return $focus }
        Invoke-MtrAdb -Arguments @('shell', 'input', 'keyevent', '4') | Out-Null
        Start-Sleep -Milliseconds 700
    }

    $focus = Get-MtrCurrentFocus
    if ($focus -notmatch 'com\.cocos\.game\.AppActivity') {
        throw "Native editor did not return focus to AppActivity: $focus"
    }
    return $focus
}

function Dump-MtrEditBoxText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $safeName = $Name -replace '[^A-Za-z0-9_.-]', '_'
    $remote = "/sdcard/mtr_${safeName}.xml"
    $local = Join-Path $resolvedOutputDir "${safeName}.xml"
    Invoke-MtrAdb -Arguments @('shell', 'uiautomator', 'dump', $remote) | Out-Null
    Invoke-MtrAdb -Arguments @('pull', $remote, $local) | Out-Null
    Invoke-MtrAdb -Arguments @('shell', 'rm', $remote) -AllowFailure | Out-Null
    [xml]$document = Get-Content -LiteralPath $local
    $node = $document.SelectSingleNode('//node[@class="android.widget.EditText"]')
    if (-not $node) { throw "EditText was not exposed in $local" }
    return [pscustomobject]@{
        Text = [string]$node.text
        Path = $local
    }
}

function Get-MtrCurrentState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Fallback
    )

    $log = Read-MtrRecentCocosLog
    $matches = [regex]::Matches($log, 'MTR_FSM:[^\r\n]*state=[a-z]+->(?<state>[a-z]+)', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if ($matches.Count -gt 0) {
        return $matches[$matches.Count - 1].Groups['state'].Value.ToLowerInvariant()
    }
    return $Fallback
}

function Get-MtrMemorySample {
    param(
        [Parameter(Mandatory = $true)]
        [double]$ElapsedSeconds
    )

    $dump = Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'meminfo', $packageName) -AllowFailure
    $pssMatch = [regex]::Match($dump, 'TOTAL PSS:\s*(?<value>[\d,]+)')
    $rssMatch = [regex]::Match($dump, 'TOTAL RSS:\s*(?<value>[\d,]+)')
    $pss = $null
    $rss = $null
    if ($pssMatch.Success) { $pss = [int64](($pssMatch.Groups['value'].Value) -replace ',', '') }
    if ($rssMatch.Success) { $rss = [int64](($rssMatch.Groups['value'].Value) -replace ',', '') }
    return [pscustomobject]@{
        elapsed_seconds = [Math]::Round($ElapsedSeconds, 3)
        total_pss_kb = $pss
        total_rss_kb = $rss
        pid = (Invoke-MtrAdb -Arguments @('shell', 'pidof', $packageName) -AllowFailure).Trim()
    }
}

function Get-MtrDiagnostics {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Log
    )

    $fatalPattern = 'FATAL EXCEPTION|ANR in com\.martyskin\.trudrunner|Process: com\.martyskin\.trudrunner[^\r\n]*(?:has died|crash)|JS:\s*(?:Uncaught|TypeError|ReferenceError|SyntaxError)|MTR_[A-Z0-9_]*(?:_FAIL|_ERROR)\b'
    $fatalCount = [regex]::Matches($Log, $fatalPattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
    $deprecationCount = [regex]::Matches($Log, 'getFrameSize|LabelOutline\.(?:color|width)', [Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
    $productWarningCount = [regex]::Matches($Log, 'MTR_[A-Z0-9_]*WARN(?:ING)?\b', [Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
    $cocosErrorLines = @($Log -split "`r?`n" | Where-Object { $_ -match '\sE Cocos\s+:' })
    $unexpectedCocosErrorLines = @($cocosErrorLines | Where-Object { $_ -notmatch 'Failed to accquire interfaces|Re-select port after|failed to get addresses' })
    $cocosWarningLines = @($Log -split "`r?`n" | Where-Object { $_ -match '\sW Cocos\s+:' })
    $unexpectedCocosWarningLines = @($cocosWarningLines | Where-Object {
        $_ -notmatch 'Failed to set shading scale|Read json failed:.*gamecaches/cacheList\.json'
    })
    return [pscustomobject]@{
        fatal_count = $fatalCount
        deprecation_count = $deprecationCount
        product_warning_count = $productWarningCount
        known_cocos_error_count = $cocosErrorLines.Count - $unexpectedCocosErrorLines.Count
        unexpected_cocos_errors = $unexpectedCocosErrorLines
        known_cocos_warning_count = $cocosWarningLines.Count - $unexpectedCocosWarningLines.Count
        unexpected_cocos_warnings = $unexpectedCocosWarningLines
    }
}

function Write-MtrFailureEvidence {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $safePhase = $currentQaPhase -replace '[^A-Za-z0-9_.-]', '_'
    $prefix = "failure_cycle${Cycle}_${safePhase}"
    $logcatPath = Join-Path $resolvedOutputDir "${prefix}.logcat.txt"
    $inputPath = Join-Path $resolvedOutputDir "${prefix}.dumpsys-input.txt"
    $windowPath = Join-Path $resolvedOutputDir "${prefix}.dumpsys-window.txt"
    $summaryPath = Join-Path $resolvedOutputDir "${prefix}.json"
    $screenshotPath = $null

    try { $logcat = Read-MtrLogcat } catch { $logcat = "capture_failed: $($_.Exception.Message)" }
    try { $inputDump = Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'input') -AllowFailure } catch { $inputDump = "capture_failed: $($_.Exception.Message)" }
    try { $windowDump = Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'window') -AllowFailure } catch { $windowDump = "capture_failed: $($_.Exception.Message)" }
    try { $screenshotPath = Save-MtrScreenshot -Name $prefix } catch { $screenshotPath = $null }

    Write-MtrUtf8 -Path $logcatPath -Text $logcat
    Write-MtrUtf8 -Path $inputPath -Text $inputDump
    Write-MtrUtf8 -Path $windowPath -Text $windowDump
    $failure = [ordered]@{
        schema = 'mtr.android_emulator_interaction_failure.v1'
        status = 'fail'
        cycle = $Cycle
        serial = $Serial
        emulator_only_guard = $Serial -match '^emulator-\d+$'
        phase = $currentQaPhase
        error = $Message
        started_at = $runStartedAt.ToString('o')
        failed_at = (Get-Date).ToString('o')
        app_process_id = (Invoke-MtrAdb -Arguments @('shell', 'pidof', '-s', $packageName) -AllowFailure).Trim()
        current_focus = Get-MtrCurrentFocus
        logcat = $logcatPath
        dumpsys_input = $inputPath
        dumpsys_window = $windowPath
        screenshot = $screenshotPath
    }
    Write-MtrUtf8 -Path $summaryPath -Text ($failure | ConvertTo-Json -Depth 8)
    return $summaryPath
}

trap {
    $failureMessage = $_.Exception.Message
    $failurePath = $null
    try { $failurePath = Write-MtrFailureEvidence -Message $failureMessage } catch {
        [Console]::Error.WriteLine("Unable to persist Android interaction failure evidence: $($_.Exception.Message)")
    }
    [Console]::Error.WriteLine("Android emulator interaction QA failed in phase '$currentQaPhase': $failureMessage")
    if ($failurePath) { [Console]::Error.WriteLine("Failure evidence: $failurePath") }
    exit 1
}

$currentQaPhase = 'emulator_guard'
$deviceState = (Invoke-MtrAdb -Arguments @('get-state')).Trim()
$isEmulator = (Invoke-MtrAdb -Arguments @('shell', 'getprop', 'ro.kernel.qemu')).Trim() -eq '1'
if ($deviceState -ne 'device' -or -not $isEmulator) {
    throw "Emulator-only guard rejected serial '$Serial' (state=$deviceState, qemu=$isEmulator)."
}
$audioPolicy = Disable-MtrEmulatorAudio

$windowSize = Get-MtrWindowSize
$points = [ordered]@{
    jump = Convert-MtrPoint -DesignX 223 -DesignY 651 -WindowSize $windowSize
    dash = Convert-MtrPoint -DesignX 1065 -DesignY 651 -WindowSize $windowSize
    pause = Convert-MtrPoint -DesignX 1045 -DesignY 110 -WindowSize $windowSize
    resume = Convert-MtrPoint -DesignX 640 -DesignY 308 -WindowSize $windowSize
    name_input = Convert-MtrPoint -DesignX 640 -DesignY 318 -WindowSize $windowSize
    name_save = Convert-MtrPoint -DesignX 640 -DesignY 434 -WindowSize $windowSize
    clear_next = Convert-MtrPoint -DesignX 640 -DesignY 408 -WindowSize $windowSize
    over_retry = Convert-MtrPoint -DesignX 640 -DesignY 448 -WindowSize $windowSize
    finished_restart = Convert-MtrPoint -DesignX 640 -DesignY 418 -WindowSize $windowSize
}

$currentQaPhase = 'touch_startup'
Write-Host '[MTR Android interaction QA] calibrated touch/FSM flow'
Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null
Start-MtrActivity -Extras ([ordered]@{ mtr_dev = '1'; mtr_autostart = '1'; mtr_level = '1' }) | Out-Null
$gameplayGate = Wait-MtrLogMarker -Pattern 'MTR_GAMEPLAY_START_GATE_READY level=1'
if (-not $gameplayGate.Found) { throw 'Level 1 gameplay gate did not become ready.' }
$currentQaPhase = 'input_channel_ready'
$inputReady = Wait-MtrAppInputReady
if (-not $inputReady.Found) {
    throw "App input channel did not become focused and responsive: $($inputReady.Focus)"
}
Start-Sleep -Milliseconds 400
Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null

$currentQaPhase = 'touch_dash'
$dashWait = Invoke-MtrVerifiedTap -Point $points.dash -Pattern 'MTR_PLAYER_POSE[^\r\n]*pose=crouch_dash\b'
if (-not $dashWait.Found) { throw 'Dash touch did not produce a crouch_dash pose.' }
$dashScreenshot = Save-MtrScreenshot -Name 'touch_dash'
$dashLog = Read-MtrLogcat
Start-Sleep -Milliseconds 1100

$currentQaPhase = 'touch_jump'
Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null
$jumpWait = Invoke-MtrVerifiedTap -Point $points.jump -Pattern 'MTR_PLAYER_POSE[^\r\n]*pose=jump(?:_2)?\b'
if (-not $jumpWait.Found) { throw 'Jump touch did not produce a jump pose.' }
$jumpScreenshot = Save-MtrScreenshot -Name 'touch_jump'
$jumpLog = Read-MtrLogcat
Start-Sleep -Milliseconds 650

$currentQaPhase = 'touch_pause_resume'
Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null
$pauseWait = Invoke-MtrVerifiedTap -Point $points.pause -Pattern 'MTR_FSM:RUNNING->PAUSED[^\r\n]*state=playing->paused'
if (-not $pauseWait.Found) { throw 'Pause touch did not produce RUNNING->PAUSED.' }
$pauseMenuGate = Wait-MtrLogMarker -Pattern 'MTR_MENU_UI_GATE_READY[^\r\n]*screen=paused'
if (-not $pauseMenuGate.Found) { throw 'Paused UI gate did not become ready.' }
Start-Sleep -Milliseconds 500
$pauseScreenshot = Save-MtrScreenshot -Name 'touch_pause'
$resumeWait = Invoke-MtrVerifiedTap -Point $points.resume -Pattern 'MTR_FSM:PAUSED->RUNNING[^\r\n]*state=paused->playing'
if (-not $resumeWait.Found) { throw 'Resume button did not produce PAUSED->RUNNING.' }
$resumeScreenshot = Save-MtrScreenshot -Name 'touch_resume'
$pauseResumeLog = Read-MtrLogcat
$interactionLog = "===== dash =====`n$dashLog`n===== jump =====`n$jumpLog`n===== pause_resume =====`n$pauseResumeLog"
Write-MtrUtf8 -Path (Join-Path $resolvedOutputDir 'touch_interaction.logcat.txt') -Text $interactionLog
$interactionDiagnostics = Get-MtrDiagnostics -Log $interactionLog

$currentQaPhase = 'name_entry'
Write-Host '[MTR Android interaction QA] native name entry and cold persistence'
$qaName = "QAPrimateC$Cycle"
Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null
Start-MtrActivity -Extras ([ordered]@{ mtr_state = 'name' }) | Out-Null
$nameGate = Wait-MtrLogMarker -Pattern 'MTR_QA_SCREEN_READY screen=name'
if (-not $nameGate.Found) { throw 'Name screen gate did not become ready.' }
$nameMenuGate = Wait-MtrLogMarker -Pattern 'MTR_MENU_UI_GATE_READY[^\r\n]*screen=name'
if (-not $nameMenuGate.Found) { throw 'Name screen UI gate did not become ready.' }
Start-Sleep -Milliseconds 650
Invoke-MtrTap -Point $points.name_input
Start-Sleep -Milliseconds 700
for ($key = 0; $key -lt 30; $key++) {
    Invoke-MtrAdb -Arguments @('shell', 'input', 'keyevent', '67') | Out-Null
}
Invoke-MtrAdb -Arguments @('shell', 'input', 'text', $qaName) | Out-Null
Start-Sleep -Milliseconds 500
$typedEditBox = Dump-MtrEditBoxText -Name 'name_typed'
if ($typedEditBox.Text -ne $qaName) {
    throw "Native EditBox value mismatch: expected '$qaName', got '$($typedEditBox.Text)'."
}
Close-MtrNativeEditor | Out-Null
Start-Sleep -Milliseconds 500
$typedScreenshot = Save-MtrScreenshot -Name 'name_typed_in_game'
Invoke-MtrTap -Point $points.name_save
Start-Sleep -Milliseconds 650
$savedScreenshot = Save-MtrScreenshot -Name 'name_saved'
$nameEntryLog = Read-MtrLogcat

Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null
Start-MtrActivity -Extras ([ordered]@{ mtr_state = 'name' }) | Out-Null
$coldNameGate = Wait-MtrLogMarker -Pattern 'MTR_QA_SCREEN_READY screen=name'
if (-not $coldNameGate.Found) { throw 'Cold-restart name screen gate did not become ready.' }
$coldNameMenuGate = Wait-MtrLogMarker -Pattern 'MTR_MENU_UI_GATE_READY[^\r\n]*screen=name'
if (-not $coldNameMenuGate.Found) { throw 'Cold-restart name UI gate did not become ready.' }
Start-Sleep -Milliseconds 650
$coldNameScreenshot = Save-MtrScreenshot -Name 'name_cold_restart'
Invoke-MtrTap -Point $points.name_input
Start-Sleep -Milliseconds 700
$persistedEditBox = Dump-MtrEditBoxText -Name 'name_persisted'
if ($persistedEditBox.Text -ne $qaName) {
    throw "Cold-restart name mismatch: expected '$qaName', got '$($persistedEditBox.Text)'."
}
Close-MtrNativeEditor | Out-Null
$coldNameLog = Read-MtrLogcat
$nameLog = "===== entry_and_save =====`n$nameEntryLog`n===== cold_restart =====`n$coldNameLog"
Write-MtrUtf8 -Path (Join-Path $resolvedOutputDir 'name_entry_persistence.logcat.txt') -Text $nameLog
$nameDiagnostics = Get-MtrDiagnostics -Log $nameLog

$currentQaPhase = 'restart_loop'
Write-Host "[MTR Android interaction QA] restart loop ($RestartIterations iterations)"
$restartResults = [System.Collections.Generic.List[object]]::new()
$restartLogBuilder = New-Object System.Text.StringBuilder
for ($iteration = 1; $iteration -le $RestartIterations; $iteration++) {
    Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null
    Start-MtrActivity -Extras ([ordered]@{ mtr_dev = '1'; mtr_state = 'over'; mtr_level = '1' }) | Out-Null
    $overGate = Wait-MtrLogMarker -Pattern 'MTR_QA_SCREEN_READY screen=over'
    $overMenuGate = Wait-MtrLogMarker -Pattern 'MTR_MENU_UI_GATE_READY[^\r\n]*screen=over'
    $stopwatch = [Diagnostics.Stopwatch]::StartNew()
    Invoke-MtrTap -Point $points.over_retry
    $retryWait = Wait-MtrLogMarker -Pattern 'MTR_FSM:[^\r\n]*state=over->playing[^\r\n]*reason=start_level'
    $stopwatch.Stop()
    $appProcessId = (Invoke-MtrAdb -Arguments @('shell', 'pidof', $packageName) -AllowFailure).Trim()
    $iterationLog = Read-MtrLogcat
    [void]$restartLogBuilder.AppendLine("===== iteration $iteration =====")
    [void]$restartLogBuilder.AppendLine($iterationLog)
    $iterationDiagnostics = Get-MtrDiagnostics -Log $iterationLog
    $passed = $overGate.Found -and $overMenuGate.Found -and $retryWait.Found -and [bool]$appProcessId -and $iterationDiagnostics.fatal_count -eq 0 -and $iterationDiagnostics.deprecation_count -eq 0 -and $iterationDiagnostics.product_warning_count -eq 0 -and $iterationDiagnostics.unexpected_cocos_errors.Count -eq 0 -and $iterationDiagnostics.unexpected_cocos_warnings.Count -eq 0
    if ($iteration -eq 1 -or $iteration -eq $RestartIterations) {
        Save-MtrScreenshot -Name ('restart_{0:D2}' -f $iteration) | Out-Null
    }
    $restartResults.Add([pscustomobject]@{
        iteration = $iteration
        status = if ($passed) { 'pass' } else { 'fail' }
        over_gate_ready = $overGate.Found
        over_menu_gate_ready = $overMenuGate.Found
        retry_transition_ready = $retryWait.Found
        retry_latency_ms = [int]$stopwatch.ElapsedMilliseconds
        pid = $appProcessId
        fatal_count = $iterationDiagnostics.fatal_count
        deprecation_count = $iterationDiagnostics.deprecation_count
        product_warning_count = $iterationDiagnostics.product_warning_count
        unexpected_cocos_error_count = $iterationDiagnostics.unexpected_cocos_errors.Count
        unexpected_cocos_warning_count = $iterationDiagnostics.unexpected_cocos_warnings.Count
    })
}
Write-MtrUtf8 -Path (Join-Path $resolvedOutputDir 'restart_loop.logcat.txt') -Text $restartLogBuilder.ToString()

$currentQaPhase = 'gameplay_soak'
Write-Host "[MTR Android interaction QA] ${SoakSeconds}s live gameplay soak"
Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null
Start-MtrActivity -Extras ([ordered]@{ mtr_dev = '1'; mtr_autostart = '1'; mtr_level = '1' }) | Out-Null
$soakGate = Wait-MtrLogMarker -Pattern 'MTR_GAMEPLAY_START_GATE_READY level=1'
if (-not $soakGate.Found) { throw 'Soak gameplay gate did not become ready.' }
Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'gfxinfo', $packageName, 'reset') -AllowFailure | Out-Null

$soakStopwatch = [Diagnostics.Stopwatch]::StartNew()
$memorySamples = [System.Collections.Generic.List[object]]::new()
$statesObserved = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
[void]$statesObserved.Add('playing')
$lastState = 'playing'
$lastMemoryAt = -999.0
$lastScreenshotAt = -999.0
$lastPidCheckAt = -999.0
$nextPauseAt = 45.0
$inputBursts = 0
$stateActions = 0
$processLosses = 0
$inputToggle = $false

while ($soakStopwatch.Elapsed.TotalSeconds -lt $SoakSeconds) {
    $elapsed = $soakStopwatch.Elapsed.TotalSeconds
    $lastState = Get-MtrCurrentState -Fallback $lastState
    [void]$statesObserved.Add($lastState)

    if ($elapsed - $lastPidCheckAt -ge 5.0) {
        $appProcessId = (Invoke-MtrAdb -Arguments @('shell', 'pidof', $packageName) -AllowFailure).Trim()
        if (-not $appProcessId) { $processLosses++ }
        $lastPidCheckAt = $elapsed
    }
    if ($elapsed - $lastMemoryAt -ge 30.0) {
        $memorySamples.Add((Get-MtrMemorySample -ElapsedSeconds $elapsed))
        $lastMemoryAt = $elapsed
    }
    if ($elapsed - $lastScreenshotAt -ge 60.0) {
        Save-MtrScreenshot -Name ('soak_{0:D3}s' -f [int]$elapsed) | Out-Null
        $lastScreenshotAt = $elapsed
    }

    switch ($lastState) {
        'clear' {
            Invoke-MtrTap -Point $points.clear_next
            $stateActions++
        }
        'over' {
            Invoke-MtrTap -Point $points.over_retry
            $stateActions++
        }
        'finished' {
            Invoke-MtrTap -Point $points.finished_restart
            $stateActions++
        }
        'paused' {
            Invoke-MtrTap -Point $points.resume
            $stateActions++
        }
        'playing' {
            if ($elapsed -ge $nextPauseAt) {
                Invoke-MtrTap -Point $points.pause
                $nextPauseAt += 45.0
                $stateActions++
            } elseif ($inputToggle) {
                Invoke-MtrTap -Point $points.dash
                $inputBursts++
                $inputToggle = $false
            } else {
                Invoke-MtrTap -Point $points.jump
                $inputBursts++
                $inputToggle = $true
            }
        }
    }
    Start-Sleep -Milliseconds 700
}
$soakStopwatch.Stop()
$memorySamples.Add((Get-MtrMemorySample -ElapsedSeconds $soakStopwatch.Elapsed.TotalSeconds))
$soakFinalScreenshot = Save-MtrScreenshot -Name 'soak_final'
$soakLog = Read-MtrLogcat
Write-MtrUtf8 -Path (Join-Path $resolvedOutputDir 'soak.logcat.txt') -Text $soakLog
$soakDiagnostics = Get-MtrDiagnostics -Log $soakLog
$gfxInfo = Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'gfxinfo', $packageName, 'framestats') -AllowFailure
Write-MtrUtf8 -Path (Join-Path $resolvedOutputDir 'soak_gfxinfo.txt') -Text $gfxInfo
$cpuInfo = Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'cpuinfo') -AllowFailure
Write-MtrUtf8 -Path (Join-Path $resolvedOutputDir 'soak_cpuinfo.txt') -Text $cpuInfo

$restartFailures = @($restartResults | Where-Object { $_.status -ne 'pass' })
$interactionPassed = $interactionDiagnostics.fatal_count -eq 0 -and $interactionDiagnostics.deprecation_count -eq 0 -and $interactionDiagnostics.product_warning_count -eq 0 -and $interactionDiagnostics.unexpected_cocos_errors.Count -eq 0 -and $interactionDiagnostics.unexpected_cocos_warnings.Count -eq 0
$namePassed = $persistedEditBox.Text -eq $qaName -and $nameDiagnostics.fatal_count -eq 0 -and $nameDiagnostics.deprecation_count -eq 0 -and $nameDiagnostics.product_warning_count -eq 0 -and $nameDiagnostics.unexpected_cocos_errors.Count -eq 0 -and $nameDiagnostics.unexpected_cocos_warnings.Count -eq 0
$soakPassed = $soakStopwatch.Elapsed.TotalSeconds -ge $SoakSeconds -and $inputBursts -gt 0 -and $processLosses -eq 0 -and $soakDiagnostics.fatal_count -eq 0 -and $soakDiagnostics.deprecation_count -eq 0 -and $soakDiagnostics.product_warning_count -eq 0 -and $soakDiagnostics.unexpected_cocos_errors.Count -eq 0 -and $soakDiagnostics.unexpected_cocos_warnings.Count -eq 0
$overallPassed = $interactionPassed -and $namePassed -and $restartFailures.Count -eq 0 -and $soakPassed

$summary = [ordered]@{
    schema = 'mtr.android_emulator_interaction.v1'
    cycle = $Cycle
    status = if ($overallPassed) { 'pass' } else { 'fail' }
    serial = $Serial
    emulator_only_guard = $true
    audio_policy = $audioPolicy
    component = $component
    started_at = $runStartedAt.ToString('o')
    finished_at = (Get-Date).ToString('o')
    window = [ordered]@{ width = $windowSize.Width; height = $windowSize.Height }
    touch_injection = [ordered]@{
        source = 'touchscreen'
        display_id = 0
        coordinate_space = 'current_logical_display'
    }
    touch_coordinates = $points
    touch_flow = [ordered]@{
        status = if ($interactionPassed) { 'pass' } else { 'fail' }
        input_channel_wait_ms = $inputReady.WaitMs
        input_channel_stable_samples = $inputReady.StableSamples
        jump_marker_wait_ms = $jumpWait.WaitMs
        dash_marker_wait_ms = $dashWait.WaitMs
        pause_marker_wait_ms = $pauseWait.WaitMs
        resume_marker_wait_ms = $resumeWait.WaitMs
        touch_attempts = [ordered]@{
            dash = $dashWait.Attempts
            jump = $jumpWait.Attempts
            pause = $pauseWait.Attempts
            resume = $resumeWait.Attempts
        }
        screenshots = @($jumpScreenshot, $dashScreenshot, $pauseScreenshot, $resumeScreenshot)
        diagnostics = $interactionDiagnostics
    }
    name_entry = [ordered]@{
        status = if ($namePassed) { 'pass' } else { 'fail' }
        expected = $qaName
        typed_value = $typedEditBox.Text
        persisted_value_after_cold_restart = $persistedEditBox.Text
        editor_close_method = 'Android back to AppActivity before in-game save tap'
        screenshots = @($typedScreenshot, $savedScreenshot, $coldNameScreenshot)
        diagnostics = $nameDiagnostics
    }
    restart_loop = [ordered]@{
        status = if ($restartFailures.Count -eq 0) { 'pass' } else { 'fail' }
        requested_iterations = $RestartIterations
        pass_count = $RestartIterations - $restartFailures.Count
        fail_count = $restartFailures.Count
        iterations = $restartResults
    }
    soak = [ordered]@{
        status = if ($soakPassed) { 'pass' } else { 'fail' }
        requested_seconds = $SoakSeconds
        actual_seconds = [Math]::Round($soakStopwatch.Elapsed.TotalSeconds, 3)
        input_bursts = $inputBursts
        state_actions = $stateActions
        states_observed = @($statesObserved | Sort-Object)
        process_losses = $processLosses
        memory_samples = $memorySamples
        final_screenshot = $soakFinalScreenshot
        diagnostics = $soakDiagnostics
    }
}

$summaryPath = Join-Path $resolvedOutputDir "android_interaction_cycle${Cycle}_summary.json"
$currentQaPhase = 'complete'
Write-MtrUtf8 -Path $summaryPath -Text ($summary | ConvertTo-Json -Depth 12)
$summary | ConvertTo-Json -Depth 12

if (-not $overallPassed) {
    throw "Android emulator interaction QA cycle $Cycle failed. See $summaryPath"
}
