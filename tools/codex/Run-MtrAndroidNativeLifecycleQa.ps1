[CmdletBinding()]
param(
    [string]$Serial = 'emulator-5554',
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [string]$ApkPath = 'build/android-emulator/proj/build/CocosGame/outputs/apk/debug/CocosGame-debug.apk'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($Serial -notmatch '^emulator-\d+$') { throw 'Native lifecycle QA is emulator-only.' }
. (Join-Path $PSScriptRoot 'MtrAndroidQaAudioGuard.ps1')
$adb = (Get-Command adb -ErrorAction Stop).Source
$package = 'com.martyskin.trudrunner'
$component = "$package/com.cocos.game.AppActivity"
$out = [IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputDir))
if (Test-Path -LiteralPath $out) { throw "Evidence directory already exists: $out" }
$apkHash = (Get-FileHash -LiteralPath $ApkPath -Algorithm SHA256).Hash
New-Item -ItemType Directory -Path $out | Out-Null
$utf8 = [Text.UTF8Encoding]::new($false)
$rows = [Collections.Generic.List[object]]::new()
$densityChanged = $false
$restoreDensity = $null
$failure = $null
$started = Get-Date
function Save-Text([string]$Name,[string]$Text) {
    [IO.File]::WriteAllText((Join-Path $out $Name),$Text,$utf8)
}
function Adb([string[]]$Arguments) {
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $lines = @(& $adb -s $Serial @Arguments 2>&1); $code = $LASTEXITCODE }
    finally { $ErrorActionPreference = $old }
    $text = $lines -join "`n"
    if ($code -ne 0) { throw "ADB exit $code $($Arguments -join ' '): $text" }
    return $text
}
function Capture([string]$Name) {
    $log = Adb @('logcat','-d','-v','threadtime')
    Save-Text "$Name.logcat.txt" $log
    $activities = Adb @('shell','dumpsys','activity','activities')
    Save-Text "$Name.activities.txt" $activities
    Save-Text "$Name.window.txt" (Adb @('shell','dumpsys','window','windows'))
    $appPid = (Adb @('shell','pidof',$package)).Trim()
    Save-Text "$Name.pid.txt" $appPid
    $remote = "/sdcard/mtr_native_lifecycle_$Name.png"
    Adb @('shell','screencap','-p',$remote) | Out-Null
    Adb @('pull',$remote,(Join-Path $out "$Name.png")) | Out-Null
    Adb @('shell','rm',$remote) | Out-Null
    return @{log=$log;activities=$activities;pid=$appPid;bytes=(Get-Item (Join-Path $out "$Name.png")).Length}
}
function Wait-Marker([string]$Pattern) {
    $watch = [Diagnostics.Stopwatch]::StartNew()
    do {
        $log = Adb @('logcat','-d','-v','threadtime')
        if ($log -match $Pattern) { return @{found=$true;wait_ms=$watch.ElapsedMilliseconds} }
        Start-Sleep -Milliseconds 350
    } while ($watch.ElapsedMilliseconds -lt 35000)
    return @{found=$false;wait_ms=$watch.ElapsedMilliseconds}
}
function Assert-Frame([string]$Name,[string]$Screen,[AllowNull()][string]$SamePid=$null,[bool]$ExpectQaQuery=$true) {
    $wait = Wait-Marker "MTR_MENU_UI_GATE_READY[^\r\n]*screen=$Screen"
    $state = Capture $Name
    $fatal = $state.log -match 'FATAL EXCEPTION|Fatal signal|ANR in com\.martyskin\.trudrunner|JS:\s*(Uncaught|TypeError|ReferenceError|SyntaxError)|MTR_[A-Z0-9_]*(?:_FAIL|_ERROR)\b'
    $focused = $state.activities -match 'topResumedActivity=ActivityRecord\{[^\r\n]*u0 com\.martyskin\.trudrunner/com\.cocos\.game\.AppActivity'
    $queryReady = if ($ExpectQaQuery) {
        $state.log -match 'MTR_NATIVE_STARTUP_QUERY_READY' -and $state.log -match "MTR_QA_SCREEN_READY screen=$Screen"
    } else {
        # A real default launch has no QA query. Require absence, not a synthetic query marker.
        $state.log -notmatch 'MTR_NATIVE_STARTUP_QUERY_READY|MTR_QA_SCREEN_READY'
    }
    $instanceMatches = [regex]::Matches($state.log,'MTR_NATIVE_LIFECYCLE event=create_ready instance=(\d+)')
    $state.instance = if($instanceMatches.Count){$instanceMatches[$instanceMatches.Count-1].Groups[1].Value}else{''}
    $passed = $wait.found -and $state.bytes -gt 100000 -and $focused -and -not $fatal -and
        $queryReady -and
        $state.log -match 'MTR_NATIVE_LIFECYCLE event=create_ready' -and
        (-not $SamePid -or $state.pid -eq $SamePid)
    $rows.Add(@{case=$Name;status=if($passed){'pass'}else{'fail'};expected_screen=$Screen;qa_query_expected=$ExpectQaQuery;query_contract_passed=$queryReady;marker_wait_ms=$wait.wait_ms;pid=$state.pid;instance=$state.instance;same_pid_expected=$SamePid;screenshot_bytes=$state.bytes;focused_user0=$focused;fatal=$fatal})
    if (-not $passed) { throw "Native lifecycle case failed: $Name" }
    return $state
}
try {
    $audioPolicy = Assert-MtrAndroidQaAudioMuted -AdbPath $adb -Serial $Serial
    Save-Text 'audio.receipt.json' ($audioPolicy | ConvertTo-Json -Depth 10)
    if ((Adb @('shell','am','get-current-user')).Trim() -ne '0') { throw 'QA must use emulator user0.' }
    $installed = (Adb @('shell','pm','path','--user','0',$package)).Trim()
    if ($installed -notmatch '^package:(/[^\r\n]+/base\.apk)$') { throw 'Expected one installed base APK.' }
    $installedHash = (Adb @('shell','sha256sum',$Matches[1])).Split(' ')[0].ToUpperInvariant()
    if ($installedHash -ne $apkHash) { throw 'Installed APK differs from the requested local build.' }
    Save-Text 'apk.identity.json' (@{sha256=$apkHash;installed_sha256=$installedHash;path=$ApkPath} | ConvertTo-Json)
    $density = Adb @('shell','wm','density')
    Save-Text 'density.before.txt' $density
    $override = [regex]::Match($density,'Override density:\s*(\d+)')
    $restoreDensity = if ($override.Success) { $override.Groups[1].Value } else { 'reset' }
    $physical = [regex]::Match($density,'Physical density:\s*(\d+)')
    if (-not $physical.Success) { throw 'Cannot prove emulator density before mutation.' }
    $current = if ($override.Success) { [int]$override.Groups[1].Value } else { [int]$physical.Groups[1].Value }
    Adb @('logcat','-c') | Out-Null
    Save-Text 'launch.stdout.txt' (Adb @('shell','am','start','--user','0','-S','-n',$component,'--es','mtr_state','menu'))
    $initial = Assert-Frame 'initial-menu' 'menu'
    Adb @('logcat','-c') | Out-Null
    Save-Text 'new-intent.stdout.txt' (Adb @('shell','am','start','--user','0','-n',$component,'--es','mtr_dev','1','--es','mtr_state','levels'))
    $intentWait = Wait-Marker 'MTR_NATIVE_LIFECYCLE event=new_intent_ready'
    $intentState = Capture 'new-intent'
    $samePid = $intentState.pid -eq $initial.pid
    $intentPassed = $intentWait.found -and $samePid -and $intentState.log -notmatch 'MTR_NATIVE_LIFECYCLE event=create_enter'
    $rows.Add(@{case='new-intent';status=if($intentPassed){'pass'}else{'fail'};same_pid=$samePid;marker_wait_ms=$intentWait.wait_ms})
    if (-not $intentPassed) { throw 'New Intent was not delivered to the existing Activity.' }
    $audioPolicy = Assert-MtrAndroidQaAudioMuted -AdbPath $adb -Serial $Serial
    Adb @('logcat','-c') | Out-Null
    $densityChanged=$true
    Save-Text 'density.change.stdout.txt' (Adb @('shell','wm','density',[string]($current+20)))
    $changedState = Assert-Frame 'recreated-levels' 'levels' $initial.pid
    if ($changedState.log -notmatch 'MTR_NATIVE_LIFECYCLE event=destroy_ready' -or
        $changedState.log -notmatch 'MTR_NATIVE_LIFECYCLE event=create_enter_saved' -or
        $changedState.instance -eq $initial.instance) { throw 'Expected actual saved-state Activity recreation.' }
    $audioPolicy = Assert-MtrAndroidQaAudioMuted -AdbPath $adb -Serial $Serial
    Adb @('logcat','-c') | Out-Null
    Save-Text 'density.restore.stdout.txt' (Adb @('shell','wm','density',[string]$restoreDensity))
    $restored = Assert-Frame 'restored-levels' 'levels' $initial.pid
    if ($restored.log -notmatch 'MTR_NATIVE_LIFECYCLE event=create_enter_saved' -or
        $restored.instance -eq $changedState.instance) { throw 'Expected another saved-state Activity recreation on restoration.' }
    $after = Adb @('shell','wm','density')
    Save-Text 'density.after.txt' $after
    if ($after.Trim() -ne $density.Trim()) { throw 'Density restoration differs from the initial emulator state.' }
    $densityChanged=$false
    $audioPolicy = Assert-MtrAndroidQaAudioMuted -AdbPath $adb -Serial $Serial
    Adb @('logcat','-c') | Out-Null
    Save-Text 'fresh-default.stdout.txt' (Adb @('shell','am','start','--user','0','-S','-n',$component))
    $fresh = Assert-Frame 'fresh-default-menu' 'menu' $null $false
    if ($fresh.pid -eq $initial.pid) { throw 'Force-stopped default launch unexpectedly reused the previous PID.' }
} catch {
    $failure = $_.Exception.Message
    Save-Text 'failure.txt' $failure
} finally {
    if ($densityChanged) {
        try {
            Save-Text 'density.finally-restore.stdout.txt' (Adb @('shell','wm','density',[string]$restoreDensity))
            Save-Text 'density.finally-after.txt' (Adb @('shell','wm','density'))
        } catch { $failure = "$failure; density restoration failed: $($_.Exception.Message)" }
    }
    $passCount=@($rows | Where-Object status -eq 'pass').Count
    $status=if(-not $failure -and $rows.Count -eq 5 -and $passCount -eq 5){'pass'}else{'fail'}
    $report=@{schema='mtr.android_native_lifecycle_qa.v1';status=$status;cases=@($rows);pass_count=$passCount;case_count=$rows.Count;expected_case_count=5;failure=$failure;apk_sha256=$apkHash;serial=$Serial;user=0;timeout_seconds=35;retry_count=0;started_at=$started.ToString('o');finished_at=(Get-Date).ToString('o')}
    Save-Text 'report.json' ($report | ConvertTo-Json -Depth 12)
}
@{status=$status;pass_count=$passCount;case_count=$rows.Count;failure=$failure;report=(Join-Path $out 'report.json')} | ConvertTo-Json
if ($status -ne 'pass') { exit 1 }
