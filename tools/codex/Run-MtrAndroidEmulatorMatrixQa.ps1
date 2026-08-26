[CmdletBinding()]
param(
    [string]$Serial = 'emulator-5554',
    [ValidateRange(1, 99)]
    [int]$Cycle = 1,
    [string]$OutputDir = 'docs\qa\evidence\android_emulator_matrix',
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

function Invoke-MtrAdb {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        # Windows PowerShell wraps native stderr as ErrorRecord even when adb
        # exits successfully (notably `adb pull` progress). Exit code is the
        # authoritative transport result.
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

function Read-MtrLogcat {
    return Invoke-MtrAdb -Arguments @('logcat', '-d', '-v', 'threadtime')
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

function Wait-MtrLogMarker {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Pattern
    )

    $started = Get-Date
    $deadline = $started.AddSeconds($MarkerTimeoutSeconds)
    $log = ''
    do {
        Start-Sleep -Milliseconds 350
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
        Log = $log
    }
}

function Save-MtrScreenshot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CaseName
    )

    $remote = "/sdcard/mtr_${CaseName}.png"
    $local = Join-Path $resolvedOutputDir "${CaseName}.png"
    Invoke-MtrAdb -Arguments @('shell', 'screencap', '-p', $remote) | Out-Null
    Invoke-MtrAdb -Arguments @('pull', $remote, $local) | Out-Null
    Invoke-MtrAdb -Arguments @('shell', 'rm', $remote) -AllowFailure | Out-Null
    return $local
}

function New-MtrCase {
    param(
        [string]$Name,
        [System.Collections.IDictionary]$Extras,
        [string]$ExpectedMarker,
        [string]$Screen = '',
        [int]$Level = 0,
        [double]$SettleSeconds = 2.5
    )

    return [pscustomobject]@{
        Name = $Name
        Extras = $Extras
        ExpectedMarker = $ExpectedMarker
        Screen = $Screen
        Level = $Level
        SettleSeconds = $SettleSeconds
    }
}

$deviceState = (Invoke-MtrAdb -Arguments @('get-state')).Trim()
$isEmulator = (Invoke-MtrAdb -Arguments @('shell', 'getprop', 'ro.kernel.qemu')).Trim() -eq '1'
if ($deviceState -ne 'device' -or -not $isEmulator) {
    throw "Emulator-only guard rejected serial '$Serial' (state=$deviceState, qemu=$isEmulator)."
}
$audioPolicy = Disable-MtrEmulatorAudio

$cases = [System.Collections.Generic.List[object]]::new()
$cases.Add((New-MtrCase -Name 'ui_menu' -Extras ([ordered]@{ mtr_state = 'menu' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=menu' -Screen 'menu'))
$cases.Add((New-MtrCase -Name 'ui_name' -Extras ([ordered]@{ mtr_state = 'name' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=name' -Screen 'name'))
$cases.Add((New-MtrCase -Name 'ui_levels' -Extras ([ordered]@{ mtr_dev = '1'; mtr_state = 'levels' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=levels' -Screen 'levels'))
$cases.Add((New-MtrCase -Name 'ui_skins' -Extras ([ordered]@{ mtr_state = 'skins' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=skins' -Screen 'skins'))
$cases.Add((New-MtrCase -Name 'ui_sound' -Extras ([ordered]@{ mtr_state = 'sound' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=sound' -Screen 'sound'))
$cases.Add((New-MtrCase -Name 'ui_records' -Extras ([ordered]@{ mtr_state = 'records'; mtr_seed_records = '1' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=records' -Screen 'records'))
$cases.Add((New-MtrCase -Name 'ui_achievements' -Extras ([ordered]@{ mtr_state = 'achievements'; mtr_unlock_achievements = '1' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=achievements' -Screen 'achievements'))
$cases.Add((New-MtrCase -Name 'ui_devgate' -Extras ([ordered]@{ mtr_state = 'devgate' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=devgate' -Screen 'devgate'))
$cases.Add((New-MtrCase -Name 'ui_devpanel' -Extras ([ordered]@{ mtr_dev = '1'; mtr_state = 'devpanel' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=devpanel' -Screen 'devpanel'))
$cases.Add((New-MtrCase -Name 'ui_paused' -Extras ([ordered]@{ mtr_dev = '1'; mtr_autostart = '1'; mtr_level = '8'; mtr_pause = '1'; mtr_show_touch_zones = '1' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=paused' -Screen 'paused' -Level 8 -SettleSeconds 3.0))
$cases.Add((New-MtrCase -Name 'ui_clear' -Extras ([ordered]@{ mtr_dev = '1'; mtr_state = 'clear'; mtr_level = '1' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=clear' -Screen 'clear'))
$cases.Add((New-MtrCase -Name 'ui_over' -Extras ([ordered]@{ mtr_dev = '1'; mtr_state = 'over'; mtr_level = '1' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=over' -Screen 'over'))
$cases.Add((New-MtrCase -Name 'ui_finished' -Extras ([ordered]@{ mtr_dev = '1'; mtr_state = 'finished'; mtr_level = '15' }) -ExpectedMarker 'MTR_QA_SCREEN_READY screen=finished' -Screen 'finished'))

for ($level = 1; $level -le 15; $level++) {
    $caseName = 'level_{0:D2}' -f $level
    $extras = [ordered]@{
        mtr_dev = '1'
        mtr_autostart = '1'
        mtr_level = [string]$level
        mtr_qa_obstacles = '1'
        mtr_qa_bonuses = '1'
    }
    $cases.Add((New-MtrCase -Name $caseName -Extras $extras -ExpectedMarker "MTR_GAMEPLAY_START_GATE_READY level=$level" -Level $level -SettleSeconds 4.0))
}

$results = [System.Collections.Generic.List[object]]::new()
$startedAt = Get-Date

foreach ($case in $cases) {
    Write-Host "[MTR Android QA] $($case.Name)"
    $audioPolicy = Disable-MtrEmulatorAudio
    Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null

    $startArguments = [System.Collections.Generic.List[string]]::new()
    foreach ($arg in @('shell', 'am', 'start', '-S', '-n', $component)) {
        $startArguments.Add($arg)
    }
    foreach ($entry in $case.Extras.GetEnumerator()) {
        $startArguments.Add('--es')
        $startArguments.Add([string]$entry.Key)
        $startArguments.Add([string]$entry.Value)
    }

    $startOutput = Invoke-MtrAdb -Arguments $startArguments.ToArray()
    $wait = Wait-MtrLogMarker -Pattern $case.ExpectedMarker
    Start-Sleep -Milliseconds ([int]($case.SettleSeconds * 1000))

    $screenshotPath = Save-MtrScreenshot -CaseName $case.Name
    $log = Read-MtrLogcat
    $logPath = Join-Path $resolvedOutputDir "$($case.Name).logcat.txt"
    Write-MtrUtf8 -Path $logPath -Text $log

    $nativeQueryReady = [regex]::IsMatch($log, 'MTR_NATIVE_STARTUP_QUERY_READY')
    $expectedReady = [regex]::IsMatch($log, $case.ExpectedMarker, [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $menuGateReady = if ($case.Screen) {
        [regex]::IsMatch($log, "MTR_MENU_UI_GATE_READY[^\r\n]*screen=$([regex]::Escape($case.Screen))", [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    } else {
        $true
    }
    $backgroundReady = if ($case.Level -gt 0 -and -not $case.Screen) {
        [regex]::IsMatch($log, "MTR_BACKGROUND_BITMAP_APPLIED level=$($case.Level) source=full")
    } else {
        $true
    }
    $assetSummaryReady = if ($case.Level -gt 0 -and -not $case.Screen) {
        [regex]::IsMatch($log, "MTR_ASSET_USAGE_SUMMARY level=$($case.Level)")
    } else {
        $true
    }

    $fatalPattern = 'FATAL EXCEPTION|ANR in com\.martyskin\.trudrunner|Process: com\.martyskin\.trudrunner[^\r\n]*(?:has died|crash)|JS:\s*(?:Uncaught|TypeError|ReferenceError|SyntaxError)|MTR_[A-Z0-9_]*(?:_FAIL|_ERROR)\b'
    $fatalCount = [regex]::Matches($log, $fatalPattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
    $deprecationCount = [regex]::Matches($log, "getFrameSize|LabelOutline\.(?:color|width)", [Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
    $productWarningCount = [regex]::Matches($log, 'MTR_[A-Z0-9_]*WARN(?:ING)?\b', [Text.RegularExpressions.RegexOptions]::IgnoreCase).Count

    $cocosErrorLines = @($log -split "`r?`n" | Where-Object { $_ -match '\sE Cocos\s+:' })
    $unexpectedCocosErrorLines = @($cocosErrorLines | Where-Object { $_ -notmatch 'Failed to accquire interfaces|Re-select port after|failed to get addresses' })
    $cocosWarningLines = @($log -split "`r?`n" | Where-Object { $_ -match '\sW Cocos\s+:' })
    $unexpectedCocosWarningLines = @($cocosWarningLines | Where-Object {
        $_ -notmatch 'Failed to set shading scale|Read json failed:.*gamecaches/cacheList\.json'
    })

    $appPid = (Invoke-MtrAdb -Arguments @('shell', 'pidof', $packageName) -AllowFailure).Trim()
    $screenshotBytes = if (Test-Path -LiteralPath $screenshotPath) { (Get-Item -LiteralPath $screenshotPath).Length } else { 0 }
    $passed = $wait.Found -and $nativeQueryReady -and $expectedReady -and $menuGateReady -and $backgroundReady -and $assetSummaryReady -and $appPid -and $screenshotBytes -gt 100000 -and $fatalCount -eq 0 -and $deprecationCount -eq 0 -and $productWarningCount -eq 0 -and $unexpectedCocosErrorLines.Count -eq 0 -and $unexpectedCocosWarningLines.Count -eq 0

    $results.Add([pscustomobject]@{
        name = $case.Name
        status = if ($passed) { 'pass' } else { 'fail' }
        level = $case.Level
        screen = $case.Screen
        expected_marker = $case.ExpectedMarker
        marker_wait_ms = $wait.WaitMs
        native_query_ready = $nativeQueryReady
        expected_ready = $expectedReady
        menu_gate_ready = $menuGateReady
        background_ready = $backgroundReady
        asset_summary_ready = $assetSummaryReady
        process_pid = $appPid
        screenshot = $screenshotPath
        screenshot_bytes = $screenshotBytes
        logcat = $logPath
        fatal_count = $fatalCount
        deprecation_count = $deprecationCount
        product_warning_count = $productWarningCount
        known_cocos_error_count = $cocosErrorLines.Count - $unexpectedCocosErrorLines.Count
        unexpected_cocos_errors = $unexpectedCocosErrorLines
        known_cocos_warning_count = $cocosWarningLines.Count - $unexpectedCocosWarningLines.Count
        unexpected_cocos_warnings = $unexpectedCocosWarningLines
        start_output = $startOutput
    })
}

$failed = @($results | Where-Object { $_.status -ne 'pass' })
$summary = [pscustomobject]@{
    schema = 'mtr.android_emulator_matrix.v1'
    cycle = $Cycle
    serial = $Serial
    audio_policy = $audioPolicy
    component = $component
    started_at = $startedAt.ToString('o')
    finished_at = (Get-Date).ToString('o')
    case_count = $results.Count
    pass_count = $results.Count - $failed.Count
    fail_count = $failed.Count
    status = if ($failed.Count -eq 0) { 'pass' } else { 'fail' }
    cases = $results
}

$summaryPath = Join-Path $resolvedOutputDir "android_matrix_cycle${Cycle}_summary.json"
Write-MtrUtf8 -Path $summaryPath -Text ($summary | ConvertTo-Json -Depth 10)
$summary | ConvertTo-Json -Depth 4

if ($failed.Count -gt 0) {
    exit 1
}
