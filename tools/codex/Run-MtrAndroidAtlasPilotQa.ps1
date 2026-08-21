[CmdletBinding()]
param(
    [ValidateSet('baseline', 'candidate', 'rollback')]
    [string]$Phase = 'baseline',
    [string]$Serial = 'emulator-5554',
    [ValidatePattern('^[a-z0-9_]{3,64}$')]
    [string]$AtlasId = 'objective_npc',
    [ValidateRange(1, 64)]
    [int]$ExpectedSourceCount = 10,
    [string]$ProjectRoot = '',
    [string]$OutputPath = 'temp\m04-c-pilot\baseline\android\runtime.json',
    [string]$ScreenshotPath = 'temp\m04-c-pilot\baseline\android\atlas-pilot.png',
    [ValidateRange(10, 120)]
    [int]$MarkerTimeoutSeconds = 45
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = [string]$MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($scriptPath)) {
    throw 'Cannot resolve the Android atlas QA script path.'
}
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $scriptRoot = Split-Path -Parent $scriptPath
    $ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot '..\..')).Path
}

if ($Serial -notmatch '^emulator-\d+$') {
    throw "Emulator-only guard rejected serial '$Serial' before any ADB call."
}

$resolvedProject = (Resolve-Path -LiteralPath $ProjectRoot).Path
$projectPrefix = $resolvedProject.TrimEnd('\') + '\'
function Resolve-MtrContainedOutput {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Label)
    $candidate = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $resolvedProject $Path }
    $full = [System.IO.Path]::GetFullPath($candidate)
    if (-not $full.StartsWith($projectPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes project root: $full"
    }
    return $full
}

$resolvedOutput = Resolve-MtrContainedOutput -Path $OutputPath -Label 'OutputPath'
$resolvedScreenshot = Resolve-MtrContainedOutput -Path $ScreenshotPath -Label 'ScreenshotPath'
$evidenceRoot = Split-Path -Parent $resolvedOutput
[System.IO.Directory]::CreateDirectory($evidenceRoot) | Out-Null
[System.IO.Directory]::CreateDirectory((Split-Path -Parent $resolvedScreenshot)) | Out-Null
$logcatPath = Join-Path $evidenceRoot 'logcat.txt'
$meminfoPath = Join-Path $evidenceRoot 'meminfo.txt'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$adb = (Get-Command adb -ErrorAction Stop).Source
$packageName = 'com.martyskin.trudrunner'
$component = "$packageName/com.cocos.game.AppActivity"

function Invoke-MtrAdb {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    # adb writes successful transfer progress to stderr. Under Windows PowerShell
    # and ErrorActionPreference=Stop that stream otherwise becomes a terminating
    # NativeCommandError before LASTEXITCODE can be evaluated.
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = @(& $adb -s $Serial @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
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
Invoke-MtrAdb -Arguments @('shell', 'am', 'force-stop', '--user', '0', $packageName) | Out-Null
$launchOutput = Invoke-MtrAdb -Arguments @(
    'shell', 'am', 'start', '--user', '0', '-n', $component,
    '--es', 'mtr_qa_atlas_pilot', $AtlasId,
    '--es', 'mtr_screen', 'menu'
)

$deadline = (Get-Date).AddSeconds($MarkerTimeoutSeconds)
$logcat = ''
do {
    Start-Sleep -Milliseconds 250
    $logcat = Invoke-MtrAdb -Arguments @('logcat', '-d', '-v', 'threadtime')
    if ($logcat -match 'MTR_ATLAS_PILOT_(?:COMPLETE|FAIL)') { break }
} while ((Get-Date) -lt $deadline)

$completeMatches = [regex]::Matches($logcat, 'MTR_ATLAS_PILOT_COMPLETE (?<json>\{[^\r\n]+\})')
$failureMatches = [regex]::Matches($logcat, 'MTR_ATLAS_PILOT_FAIL')
$fatalMatches = [regex]::Matches($logcat, 'FATAL EXCEPTION|ANR in com\.martyskin\.trudrunner|(?:Type|Reference|Syntax)Error:')
$nativeQueryMatches = [regex]::Matches($logcat, 'MTR_NATIVE_STARTUP_QUERY_READY')
$isolationMatches = [regex]::Matches($logcat, 'MTR_ATLAS_PILOT_ISOLATION_READY')
$metric = $null
$metricParseError = $null
if ($completeMatches.Count -eq 1) {
    try {
        $metric = $completeMatches[0].Groups['json'].Value | ConvertFrom-Json
    } catch {
        $metricParseError = $_.Exception.Message
    }
}

$appProcessId = (Invoke-MtrAdb -Arguments @('shell', 'pidof', '-s', $packageName)).Trim()
$meminfo = Invoke-MtrAdb -Arguments @('shell', 'dumpsys', 'meminfo', $packageName)
$remoteScreenshot = "/sdcard/mtr-atlas-$AtlasId-$Phase.png"
Invoke-MtrAdb -Arguments @('shell', 'rm', '-f', $remoteScreenshot) | Out-Null
Invoke-MtrAdb -Arguments @('shell', 'screencap', '-p', $remoteScreenshot) | Out-Null
Invoke-MtrAdb -Arguments @('pull', $remoteScreenshot, $resolvedScreenshot) | Out-Null
Invoke-MtrAdb -Arguments @('shell', 'rm', '-f', $remoteScreenshot) | Out-Null
[System.IO.File]::WriteAllText($logcatPath, "$logcat`n", $utf8NoBom)
[System.IO.File]::WriteAllText($meminfoPath, "$meminfo`n", $utf8NoBom)

$metricValid = $null -ne $metric -and
    [string]$metric.contract -eq 'mtr.atlas_pilot_runtime_metric' -and
    [int]$metric.schemaVersion -eq 2 -and
    [string]$metric.atlasId -eq $AtlasId -and
    [string]$metric.platform -eq 'android' -and
    [int]$metric.sourceCount -eq $ExpectedSourceCount -and
    [int]$metric.aggregate.sampleCount -eq 7 -and
    [int]$metric.sourceTextureCount -gt 0 -and
    [int]$metric.drawTextureCount -gt 0
$screenshotValid = (Test-Path -LiteralPath $resolvedScreenshot -PathType Leaf) -and (Get-Item -LiteralPath $resolvedScreenshot).Length -gt 0
$passed = $appProcessId -match '^\d+$' -and
    $completeMatches.Count -eq 1 -and
    $failureMatches.Count -eq 0 -and
    $fatalMatches.Count -eq 0 -and
    $nativeQueryMatches.Count -ge 1 -and
    $isolationMatches.Count -eq 1 -and
    $metricValid -and
    $screenshotValid

$result = [ordered]@{
    schema = 'mtr.android_atlas_pilot.v1'
    status = if ($passed) { 'pass' } else { 'fail' }
    phase = $Phase
    atlasId = $AtlasId
    expectedSourceCount = $ExpectedSourceCount
    serial = $Serial
    androidUser = 0
    emulatorVerified = ($qemu -eq '1')
    abi = $abi
    packageName = $packageName
    appProcessId = $appProcessId
    launchOutput = $launchOutput.Trim()
    completeCount = $completeMatches.Count
    failureCount = $failureMatches.Count
    fatalCount = $fatalMatches.Count
    nativeQueryReadyCount = $nativeQueryMatches.Count
    isolationReadyCount = $isolationMatches.Count
    metricValid = $metricValid
    metricParseError = $metricParseError
    metric = $metric
    screenshot = $resolvedScreenshot.Substring($projectPrefix.Length).Replace('\', '/')
    screenshotBytes = if ($screenshotValid) { (Get-Item -LiteralPath $resolvedScreenshot).Length } else { 0 }
    logcat = $logcatPath.Substring($projectPrefix.Length).Replace('\', '/')
    meminfo = $meminfoPath.Substring($projectPrefix.Length).Replace('\', '/')
}
$json = $result | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($resolvedOutput, "$json`n", $utf8NoBom)
[Console]::Out.WriteLine($json)
if (-not $passed) { exit 1 }
