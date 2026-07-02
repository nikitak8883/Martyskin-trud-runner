[CmdletBinding()]
param(
    [string]$ProjectRoot,
    [string]$GradleProjectRoot,
    [string]$PreferredAvdName = 'MTR_Pixel_8_Pro_API_35',
    [int]$BootTimeoutSeconds = 300,
    [switch]$EnsureEmulator,
    [switch]$Windowed,
    [switch]$FailOnNotReady,
    [switch]$FullJsonOutput,
    [switch]$AllowPhysicalDevice
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$scriptRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptRoot)) {
    $scriptRoot = Split-Path -Parent $PSCommandPath
}
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot '..\..')).Path
}
if ([string]::IsNullOrWhiteSpace($GradleProjectRoot)) {
    $GradleProjectRoot = Join-Path $ProjectRoot 'build\android-emulator\proj'
}
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logRoot = Join-Path $ProjectRoot 'logs'
$jsonlPath = Join-Path $logRoot ("android-toolchain-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd'))
$statusPath = Join-Path $logRoot ("android-toolchain-status-{0}.json" -f $timestamp)
$entrypointLogPath = Join-Path $logRoot ("entrypoint-router-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd'))
$modulePath = Join-Path $scriptRoot 'MtrEntrypoint.psm1'

Import-Module $modulePath -Force

function New-MtrDirectory {
    param([Parameter(Mandatory=$true)][string]$Path)

    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-MtrAndroidToolchainLog {
    param([Parameter(Mandatory=$true)][hashtable]$Record)

    New-MtrDirectory -Path $logRoot
    $Record.timestampUtc = (Get-Date).ToUniversalTime().ToString('o')
    ($Record | ConvertTo-Json -Depth 24 -Compress) | Add-Content -LiteralPath $jsonlPath -Encoding UTF8
}

function ConvertFrom-MtrLocalPropertiesPath {
    param([AllowNull()][string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }

    $path = $Value.Trim()
    $path = $path -replace '\\:', ':'
    $path = $path -replace '\\\\', '\'
    return $path
}

function Get-MtrAndroidSdkDir {
    $localProperties = Join-Path $GradleProjectRoot 'local.properties'
    if (-not (Test-Path -LiteralPath $localProperties -PathType Leaf)) {
        return $null
    }

    foreach ($line in Get-Content -LiteralPath $localProperties) {
        if ($line -match '^\s*sdk\.dir\s*=\s*(.+?)\s*$') {
            return ConvertFrom-MtrLocalPropertiesPath -Value $Matches[1]
        }
    }

    return $null
}

function Resolve-MtrToolCandidate {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [string[]]$CandidatePaths = @()
    )

    $command = Get-Command -Name $Name -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command -and $command.Source) {
        return [pscustomobject]@{
            name = $Name
            found = $true
            source = $command.Source
            resolution = 'PATH'
        }
    }

    foreach ($candidate in @($CandidatePaths)) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return [pscustomobject]@{
                name = $Name
                found = $true
                source = (Resolve-Path -LiteralPath $candidate).Path
                resolution = 'candidate'
            }
        }
    }

    return [pscustomobject]@{
        name = $Name
        found = $false
        source = $null
        resolution = 'missing'
    }
}

function Invoke-MtrCapturedTool {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$FilePath,
        [object[]]$ArgumentList = @(),
        [int]$TimeoutSeconds = 20,
        [string]$WorkingDirectory = $ProjectRoot
    )

    $safeName = $Name -replace '[^A-Za-z0-9_.-]', '-'
    $stdoutPath = Join-Path $logRoot ("{0}-{1}.stdout.log" -f $safeName, $timestamp)
    $stderrPath = Join-Path $logRoot ("{0}-{1}.stderr.log" -f $safeName, $timestamp)

    try {
        $run = Invoke-MtrEntrypoint `
            -FilePath $FilePath `
            -ArgumentList $ArgumentList `
            -WorkingDirectory $WorkingDirectory `
            -LogPath $entrypointLogPath `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -Wait `
            -TimeoutSeconds $TimeoutSeconds `
            -PassThru

        $stdout = ''
        $stderr = ''
        if (Test-Path -LiteralPath $stdoutPath -PathType Leaf) {
            $stdout = Get-Content -LiteralPath $stdoutPath -Raw
        }
        if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
            $stderr = Get-Content -LiteralPath $stderrPath -Raw
        }

        return [pscustomobject]@{
            name = $Name
            ok = ($run.exitCode -eq 0)
            exitCode = $run.exitCode
            timedOut = [bool]$run.timedOut
            stdoutPath = $stdoutPath
            stderrPath = $stderrPath
            stdout = $stdout
            stderr = $stderr
            error = $null
        }
    } catch {
        $stdout = ''
        $stderr = ''
        if (Test-Path -LiteralPath $stdoutPath -PathType Leaf) {
            $stdout = Get-Content -LiteralPath $stdoutPath -Raw
        }
        if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
            $stderr = Get-Content -LiteralPath $stderrPath -Raw
        }

        return [pscustomobject]@{
            name = $Name
            ok = $false
            exitCode = $null
            timedOut = ($_.Exception.Message -match 'timed out')
            stdoutPath = $stdoutPath
            stderrPath = $stderrPath
            stdout = $stdout
            stderr = $stderr
            error = $_.Exception.Message
        }
    }
}

function ConvertFrom-MtrAdbDevices {
    param([AllowNull()][string]$Text)

    $devices = [System.Collections.Generic.List[object]]::new()
    foreach ($line in (($Text -split "`r?`n") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
        if ($line -match '^\s*List of devices attached') {
            continue
        }
        if ($line -match '^\s*([^\s]+)\s+([^\s]+)(.*)$') {
            $devices.Add([pscustomobject]@{
                serial = $Matches[1]
                state = $Matches[2]
                detail = $Matches[3].Trim()
            })
        }
    }

    return @($devices)
}

function ConvertFrom-MtrAvdList {
    param([AllowNull()][string]$Text)

    $avds = [System.Collections.Generic.List[string]]::new()
    foreach ($line in (($Text -split "`r?`n") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
        $trimmed = $line.Trim()
        if ($trimmed -and $trimmed -notmatch '(?i)^error:') {
            $avds.Add($trimmed)
        }
    }

    return @($avds)
}

function ConvertTo-MtrTextPreview {
    param(
        [AllowNull()][string]$Text,
        [int]$MaxChars = 1200
    )

    if ($null -eq $Text) {
        return ''
    }
    if ($Text.Length -le $MaxChars) {
        return $Text
    }
    return $Text.Substring(0, $MaxChars) + "`n...<truncated>"
}

function ConvertTo-MtrProbeSummary {
    param([AllowNull()]$Probe)

    if ($null -eq $Probe) {
        return $null
    }

    return [pscustomobject]@{
        name = $Probe.name
        ok = [bool]$Probe.ok
        exitCode = $Probe.exitCode
        timedOut = [bool]$Probe.timedOut
        stdoutPath = $Probe.stdoutPath
        stderrPath = $Probe.stderrPath
        stdoutPreview = ConvertTo-MtrTextPreview -Text $Probe.stdout
        stderrPreview = ConvertTo-MtrTextPreview -Text $Probe.stderr
        error = $Probe.error
    }
}

function ConvertTo-MtrToolSummary {
    param([Parameter(Mandatory=$true)]$Tool)

    return [pscustomobject]@{
        name = $Tool.name
        found = [bool]$Tool.found
        source = $Tool.source
        resolution = $Tool.resolution
    }
}

function Select-MtrAvdName {
    param(
        [string[]]$AvdNames = @(),
        [string]$PreferredName
    )

    if (@($AvdNames).Count -eq 0) {
        return $null
    }
    if ($PreferredName -and (@($AvdNames) -contains $PreferredName)) {
        return $PreferredName
    }

    $pixel = @($AvdNames | Where-Object { $_ -match '(?i)pixel' } | Select-Object -First 1)
    if (@($pixel).Count -gt 0) {
        return $pixel[0]
    }

    return @($AvdNames)[0]
}

function Test-MtrAdbEmulatorDevice {
    param([Parameter(Mandatory=$true)][object]$Device)

    $serial = [string]$Device.serial
    $detail = [string]$Device.detail
    if ($serial -match '^emulator-\d+$') {
        return $true
    }
    if ($detail -match '(?i)(\bdevice:emu\b|sdk_gphone|generic_x86|generic_x86_64|ranchu|goldfish)') {
        return $true
    }
    return $false
}

function Select-MtrAndroidQaTargetDevices {
    param(
        [object[]]$Devices = @(),
        [switch]$AllowPhysical
    )

    $online = @($Devices | Where-Object {
        $null -ne $_ -and
        ($_.PSObject.Properties.Name -contains 'state') -and
        $_.state -eq 'device'
    })
    $emulators = @($online | Where-Object { Test-MtrAdbEmulatorDevice -Device $_ })
    $physical = @($online | Where-Object { -not (Test-MtrAdbEmulatorDevice -Device $_) })
    $targets = $(if ($AllowPhysical) { @($online) } else { @($emulators) })

    return [pscustomobject]@{
        allOnlineDevices = @($online)
        emulatorDevices = @($emulators)
        ignoredPhysicalDevices = $(if ($AllowPhysical) { @() } else { @($physical) })
        qaTargetDevices = @($targets)
    }
}

New-MtrDirectory -Path $logRoot

$sdkDir = Get-MtrAndroidSdkDir
$adbCandidates = @()
$emulatorCandidates = @()
if ($sdkDir) {
    $adbCandidates += (Join-Path $sdkDir 'platform-tools\adb.exe')
    $emulatorCandidates += (Join-Path $sdkDir 'emulator\emulator.exe')
}

$javaCandidates = @()
if ($env:JAVA_HOME) {
    $javaCandidates += (Join-Path $env:JAVA_HOME 'bin\java.exe')
}

$gradlewPath = Join-Path $GradleProjectRoot 'gradlew.bat'
$tools = [ordered]@{
    adb = Resolve-MtrToolCandidate -Name 'adb' -CandidatePaths $adbCandidates
    emulator = Resolve-MtrToolCandidate -Name 'emulator' -CandidatePaths $emulatorCandidates
    java = Resolve-MtrToolCandidate -Name 'java' -CandidatePaths $javaCandidates
    gradlew = [pscustomobject]@{
        name = 'gradlew'
        found = (Test-Path -LiteralPath $gradlewPath -PathType Leaf)
        source = $(if (Test-Path -LiteralPath $gradlewPath -PathType Leaf) { (Resolve-Path -LiteralPath $gradlewPath).Path } else { $null })
        resolution = 'project'
    }
}

$toolSummary = @(
    ConvertTo-MtrToolSummary -Tool $tools.adb
    ConvertTo-MtrToolSummary -Tool $tools.emulator
    ConvertTo-MtrToolSummary -Tool $tools.java
    ConvertTo-MtrToolSummary -Tool $tools.gradlew
)
$adbRun = $null
$emulatorRun = $null
$adbDevices = @()
$avds = @()

if ($tools.adb.found) {
    $adbRun = Invoke-MtrCapturedTool -Name 'adb-devices' -FilePath $tools.adb.source -ArgumentList @('devices', '-l') -TimeoutSeconds 20
    $adbDevices = ConvertFrom-MtrAdbDevices -Text $adbRun.stdout
}

if ($tools.emulator.found) {
    $emulatorRun = Invoke-MtrCapturedTool -Name 'emulator-list-avds' -FilePath $tools.emulator.source -ArgumentList @('-list-avds') -TimeoutSeconds 20
    $avds = ConvertFrom-MtrAvdList -Text $emulatorRun.stdout
}

$qaTargetSelection = Select-MtrAndroidQaTargetDevices -Devices $adbDevices -AllowPhysical:$AllowPhysicalDevice
$allOnlineDevices = @($qaTargetSelection.allOnlineDevices)
$onlineDevices = @($qaTargetSelection.qaTargetDevices)
$onlineEmulatorDevices = @($qaTargetSelection.emulatorDevices)
$ignoredPhysicalDevices = @($qaTargetSelection.ignoredPhysicalDevices)
$emulatorStart = $null
$selectedAvdName = $null
$bootCompletedSerial = $null
$bootPolls = [System.Collections.Generic.List[object]]::new()

if ($EnsureEmulator -and @($onlineDevices).Count -eq 0 -and $tools.adb.found -and $tools.emulator.found -and @($avds).Count -gt 0) {
    $selectedAvdName = Select-MtrAvdName -AvdNames $avds -PreferredName $PreferredAvdName
    $emulatorStdoutPath = Join-Path $logRoot ("emulator-start-{0}.stdout.log" -f $timestamp)
    $emulatorStderrPath = Join-Path $logRoot ("emulator-start-{0}.stderr.log" -f $timestamp)
    $emulatorArguments = @('-avd', $selectedAvdName, '-no-snapshot-save', '-no-boot-anim')
    if (-not $Windowed) {
        $emulatorArguments += @('-no-window', '-gpu', 'swiftshader_indirect')
    }

    try {
        $startRun = Invoke-MtrEntrypoint `
            -FilePath $tools.emulator.source `
            -ArgumentList $emulatorArguments `
            -WorkingDirectory $ProjectRoot `
            -LogPath $entrypointLogPath `
            -RedirectStandardOutput $emulatorStdoutPath `
            -RedirectStandardError $emulatorStderrPath `
            -PassThru

        $emulatorStart = [pscustomobject]@{
            attempted = $true
            avdName = $selectedAvdName
            processId = $startRun.processId
            hasExited = $startRun.hasExited
            exitCode = $startRun.exitCode
            stdoutPath = $emulatorStdoutPath
            stderrPath = $emulatorStderrPath
            error = $null
        }
    } catch {
        $emulatorStart = [pscustomobject]@{
            attempted = $true
            avdName = $selectedAvdName
            processId = $null
            hasExited = $null
            exitCode = $null
            stdoutPath = $emulatorStdoutPath
            stderrPath = $emulatorStderrPath
            error = $_.Exception.Message
        }
    }

    $deadline = (Get-Date).AddSeconds($BootTimeoutSeconds)
    $pollIndex = 0
    while (-not $bootCompletedSerial -and (Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5
        $pollIndex += 1
        $adbPoll = Invoke-MtrCapturedTool -Name ("adb-devices-poll-{0:000}" -f $pollIndex) -FilePath $tools.adb.source -ArgumentList @('devices', '-l') -TimeoutSeconds 20
        $pollDevices = ConvertFrom-MtrAdbDevices -Text $adbPoll.stdout
        $pollTargetSelection = Select-MtrAndroidQaTargetDevices -Devices $pollDevices -AllowPhysical:$AllowPhysicalDevice
        $pollAllOnlineDevices = @($pollTargetSelection.allOnlineDevices)
        $pollOnlineDevices = @($pollTargetSelection.qaTargetDevices)
        $pollOnlineEmulatorDevices = @($pollTargetSelection.emulatorDevices)
        $pollIgnoredPhysicalDevices = @($pollTargetSelection.ignoredPhysicalDevices)
        $bootCheck = $null

        foreach ($device in @($pollOnlineDevices)) {
            $bootCheck = Invoke-MtrCapturedTool -Name ("adb-boot-completed-{0:000}" -f $pollIndex) -FilePath $tools.adb.source -ArgumentList @('-s', $device.serial, 'shell', 'getprop', 'sys.boot_completed') -TimeoutSeconds 20
            if ($bootCheck.stdout.Trim() -eq '1') {
                $bootCompletedSerial = $device.serial
                break
            }
        }

        $bootPolls.Add([pscustomobject]@{
            poll = $pollIndex
            adbProbe = ConvertTo-MtrProbeSummary -Probe $adbPoll
            adbDevices = @($pollDevices)
            allOnlineDevices = @($pollAllOnlineDevices)
            emulatorDevices = @($pollOnlineEmulatorDevices)
            onlineDevices = @($pollOnlineDevices)
            ignoredPhysicalDevices = @($pollIgnoredPhysicalDevices)
            bootProbe = ConvertTo-MtrProbeSummary -Probe $bootCheck
            bootCompletedSerial = $bootCompletedSerial
        })

        if ($bootCompletedSerial) {
            $adbDevices = @($pollDevices)
            $allOnlineDevices = @($pollAllOnlineDevices)
            $onlineDevices = @($pollOnlineDevices)
            $onlineEmulatorDevices = @($pollOnlineEmulatorDevices)
            $ignoredPhysicalDevices = @($pollIgnoredPhysicalDevices)
        }
    }
}

$blockers = [System.Collections.Generic.List[string]]::new()
if (-not $tools.adb.found) { $blockers.Add('adb-not-found') }
if (-not $tools.java.found) { $blockers.Add('java-not-found') }
if (-not $tools.gradlew.found) { $blockers.Add('gradlew-not-found') }
if ($tools.adb.found -and @($onlineDevices).Count -eq 0) {
    $blockers.Add($(if ($AllowPhysicalDevice) { 'no-online-adb-device' } else { 'no-online-adb-emulator' }))
}
if ($EnsureEmulator -and $tools.emulator.found -and @($avds).Count -eq 0) { $blockers.Add('no-avd-defined') }
if ($EnsureEmulator -and $selectedAvdName -and @($onlineDevices).Count -gt 0 -and -not $bootCompletedSerial) { $blockers.Add('emulator-boot-not-confirmed') }

$qaReady = ($blockers.Count -eq 0)
$status = [pscustomobject]@{
    statusSchemaVersion = 2
    timestampUtc = (Get-Date).ToUniversalTime().ToString('o')
    projectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
    gradleProjectRoot = $GradleProjectRoot
    sdkDir = $sdkDir
    tools = @($toolSummary)
    adbProbe = ConvertTo-MtrProbeSummary -Probe $adbRun
    emulatorProbe = ConvertTo-MtrProbeSummary -Probe $emulatorRun
    ensureEmulator = [bool]$EnsureEmulator
    selectedAvdName = $selectedAvdName
    emulatorStart = $emulatorStart
    bootCompletedSerial = $bootCompletedSerial
    bootPolls = @($bootPolls)
    androidQaTargetPolicy = $(if ($AllowPhysicalDevice) { 'physical-device-override-enabled' } else { 'emulator-only-default' })
    adbDevices = @($adbDevices)
    allOnlineDevices = @($allOnlineDevices)
    emulatorDevices = @($onlineEmulatorDevices)
    onlineDevices = @($onlineDevices)
    ignoredPhysicalDevices = @($ignoredPhysicalDevices)
    avds = @($avds)
    qaReady = $qaReady
    blockers = @($blockers)
    preventions = @(
        'runtime-project-root-resolution',
        'android-sdk-local-properties-discovery',
        'bounded-probe-output-preview',
        'compact-console-summary-with-full-json-status-file',
        'entrypoint-router-captured-stdout-stderr',
        'emulator-only-qa-default-with-physical-device-ignore-log',
        'no-inline-powershell-pipeline-probes',
        'auto-start-avd-when-no-online-device'
    )
    logs = @{
        jsonl = $jsonlPath
        status = $statusPath
        entrypoint = $entrypointLogPath
    }
}

$statusJson = $status | ConvertTo-Json -Depth 10
$statusJson | Set-Content -LiteralPath $statusPath -Encoding UTF8

Write-MtrAndroidToolchainLog -Record @{
    event = 'android_toolchain.probe'
    projectRoot = $status.projectRoot
    gradleProjectRoot = $GradleProjectRoot
    sdkDir = $sdkDir
    tools = @($toolSummary)
    adbDevices = @($adbDevices)
    allOnlineDeviceCount = @($allOnlineDevices).Count
    emulatorDeviceCount = @($onlineEmulatorDevices).Count
    onlineDeviceCount = @($onlineDevices).Count
    ignoredPhysicalDeviceCount = @($ignoredPhysicalDevices).Count
    avdCount = @($avds).Count
    androidQaTargetPolicy = $status.androidQaTargetPolicy
    ensureEmulator = [bool]$EnsureEmulator
    selectedAvdName = $selectedAvdName
    bootCompletedSerial = $bootCompletedSerial
    qaReady = $qaReady
    blockers = @($blockers)
    statusPath = $statusPath
}

$consoleSummary = [pscustomobject]@{
    statusSchemaVersion = $status.statusSchemaVersion
    timestampUtc = $status.timestampUtc
    qaReady = $qaReady
    blockers = @($blockers)
    ensureEmulator = [bool]$EnsureEmulator
    androidQaTargetPolicy = $status.androidQaTargetPolicy
    selectedAvdName = $selectedAvdName
    bootCompletedSerial = $bootCompletedSerial
    ignoredPhysicalDeviceCount = @($ignoredPhysicalDevices).Count
    onlineDevices = @(
        foreach ($device in @($onlineDevices)) {
            [pscustomobject]@{
                serial = $device.serial
                state = $device.state
                detail = $device.detail
            }
        }
    )
    avdCount = @($avds).Count
    statusPath = $statusPath
    jsonlPath = $jsonlPath
    entrypointLogPath = $entrypointLogPath
}

if ($FullJsonOutput) {
    [Console]::Out.WriteLine($statusJson)
} else {
    [Console]::Out.WriteLine(($consoleSummary | ConvertTo-Json -Depth 6))
}

if ($FailOnNotReady -and -not $qaReady) {
    exit 2
}
