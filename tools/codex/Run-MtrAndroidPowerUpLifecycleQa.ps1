[CmdletBinding()]
param(
    [string]$Serial = 'emulator-5554',
    [string]$OutputPath = 'temp\m03-6-android-powerup-lifecycle.json',
    [ValidateRange(10, 120)]
    [int]$MarkerTimeoutSeconds = 45
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($Serial -notmatch '^emulator-\d+$') {
    throw "Emulator-only guard rejected serial '$Serial' before any ADB call."
}

$adb = (Get-Command adb -ErrorAction Stop).Source
$packageName = 'com.martyskin.trudrunner'
$component = "$packageName/com.cocos.game.AppActivity"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Invoke-MtrAdb {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    $output = @(& $adb -s $Serial @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $text = $output -join "`n"
    if ($exitCode -ne 0) {
        throw "adb failed ($exitCode): $($Arguments -join ' ')`n$text"
    }
    return $text
}

$state = (Invoke-MtrAdb -Arguments @('get-state')).Trim()
$qemu = (Invoke-MtrAdb -Arguments @('shell', 'getprop', 'ro.kernel.qemu')).Trim()
$abi = (Invoke-MtrAdb -Arguments @('shell', 'getprop', 'ro.product.cpu.abi')).Trim()
if ($state -ne 'device' -or $qemu -ne '1') {
    throw "Emulator-only guard rejected serial '$Serial' (state=$state, qemu=$qemu)."
}

Invoke-MtrAdb -Arguments @('logcat', '-c') | Out-Null
Invoke-MtrAdb -Arguments @('shell', 'am', 'force-stop', $packageName) | Out-Null
$launchOutput = Invoke-MtrAdb -Arguments @(
    'shell', 'am', 'start', '-n', $component,
    '--es', 'mtr_dev', '1',
    '--es', 'mtr_autostart', '1',
    '--es', 'mtr_level', '1',
    '--es', 'mtr_qa_powerups', '1'
)

$deadline = (Get-Date).AddSeconds($MarkerTimeoutSeconds)
$logcat = ''
do {
    Start-Sleep -Milliseconds 250
    $logcat = Invoke-MtrAdb -Arguments @('logcat', '-d', '-v', 'threadtime')
    if ($logcat -match 'MTR_POWERUP_QA_(?:READY|FAIL)') { break }
} while ((Get-Date) -lt $deadline)

$appProcessId = (Invoke-MtrAdb -Arguments @('shell', 'pidof', '-s', $packageName)).Trim()
if ($appProcessId -match '^\d+$') {
    $logcat = Invoke-MtrAdb -Arguments @('logcat', '--pid', $appProcessId, '-d', '-v', 'threadtime')
}

$expectedPhases = 'spawned>collected>activated>expired>cleaned'
$readyPattern = 'MTR_POWERUP_QA_READY checks=8/8 phases=' + [regex]::Escape($expectedPhases) +
    ' stale=rejected epoch=\d+ events=\d+ state=playing'
$readyMatches = [regex]::Matches($logcat, $readyPattern)
$failureMatches = [regex]::Matches($logcat, 'MTR_POWERUP_QA_FAIL')
$nativeQueryMatches = [regex]::Matches($logcat, 'MTR_NATIVE_STARTUP_QUERY_READY')
$fatalMatches = [regex]::Matches(
    $logcat,
    'FATAL EXCEPTION|ANR in com\.martyskin\.trudrunner|(?:Type|Reference|Syntax)Error:'
)
$passed = $appProcessId -match '^\d+$' -and
    $nativeQueryMatches.Count -ge 1 -and
    $readyMatches.Count -eq 1 -and
    $failureMatches.Count -eq 0 -and
    $fatalMatches.Count -eq 0

$result = [ordered]@{
    schema = 'mtr.android_powerup_lifecycle_runtime.v1'
    status = if ($passed) { 'pass' } else { 'fail' }
    serial = $Serial
    emulatorVerified = ($qemu -eq '1')
    abi = $abi
    packageName = $packageName
    appProcessId = $appProcessId
    launchOutput = $launchOutput.Trim()
    nativeQueryReadyCount = $nativeQueryMatches.Count
    readyCount = $readyMatches.Count
    failureCount = $failureMatches.Count
    fatalCount = $fatalMatches.Count
    expectedPhases = $expectedPhases
    expectedMarkerPattern = $readyPattern
}
$json = $result | ConvertTo-Json -Depth 8
$resolvedOutput = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputPath))
[System.IO.Directory]::CreateDirectory((Split-Path -Parent $resolvedOutput)) | Out-Null
[System.IO.File]::WriteAllText($resolvedOutput, "$json`n", $utf8NoBom)
[Console]::Out.WriteLine($json)
if (-not $passed) { exit 1 }
