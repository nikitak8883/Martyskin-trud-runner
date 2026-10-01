[CmdletBinding()]
param([string]$ProjectRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $ProjectRoot) { $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
Import-Module (Join-Path $PSScriptRoot 'MtrAndroidQaBootPolicy.psm1') -Force
. (Join-Path $PSScriptRoot 'MtrAndroidQaAudioGuard.ps1')
$passed = [System.Collections.Generic.List[string]]::new()
function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Assert-Throws([scriptblock]$Body, [string]$Pattern) {
    $message = $null
    try { & $Body | Out-Null } catch { $message = $_.Exception.Message }
    Assert-True ($null -ne $message -and $message -match $Pattern) "Expected rejection '$Pattern', got '$message'"
}
function Test-Case([string]$Name, [scriptblock]$Body) {
    try { & $Body; $passed.Add($Name) } catch { throw "$Name`: $($_.Exception.Message)" }
}
function New-Start {
    return [pscustomobject]@{ attempted = $true; error = $null; processId = 42; hasExited = $false; arguments = @('-no-audio', '-no-snapshot-save', '-no-snapshot-load') }
}

Test-Case 'default-headless-remains-silent-without-snapshot-load-change' {
    $args = @(Get-MtrAndroidQaEmulatorArguments -AvdName 'qa')
    Assert-True (($args -join '|') -eq '-avd|qa|-no-snapshot-save|-no-boot-anim|-no-audio|-no-window|-gpu|swiftshader_indirect') 'Default arguments changed'
}
Test-Case 'cold-windowed-no-wipe-no-host-sound' {
    $args = @(Get-MtrAndroidQaEmulatorArguments -AvdName 'qa' -Windowed $true -ColdBoot $true)
    Assert-True ($args -contains '-no-audio' -and $args -contains '-no-snapshot-load' -and $args -contains '-no-snapshot-save') 'Cold policy missing flags'
    Assert-True ($args -notcontains '-wipe-data' -and $args -notcontains '-no-window' -and $args -notcontains '-gpu') 'Windowed cold boot changed data/renderer'
}
Test-Case 'cold-headless-keeps-renderer' {
    $args = @(Get-MtrAndroidQaEmulatorArguments -AvdName 'qa' -ColdBoot $true)
    Assert-True ($args -contains 'swiftshader_indirect' -and $args -contains '-no-snapshot-load') 'Cold renderer drift'
}
Test-Case 'cold-requires-ensure-before-probing' {
    Assert-Throws { Assert-MtrAndroidQaBootOptions -ColdBoot $true } 'ColdBoot requires'
}
Test-Case 'cold-disallows-physical-override' {
    Assert-Throws { Assert-MtrAndroidQaBootOptions -ColdBoot $true -EnsureEmulator $true -AllowPhysicalDevice $true } 'emulator-only'
}
Test-Case 'normal-and-explicit-cold-options-accepted' {
    Assert-MtrAndroidQaBootOptions -EnsureEmulator $true -ColdBoot $true
    Assert-MtrAndroidQaBootOptions -AllowPhysicalDevice $true
}
Test-Case 'fresh-matching-boot-confirmed' {
    Assert-True (Test-MtrAndroidQaColdBootConfirmed (New-Start) 'emulator-5554' $true) 'Fresh cold boot rejected'
}
Test-Case 'existing-session-not-cold' {
    Assert-True (-not (Test-MtrAndroidQaColdBootConfirmed $null 'emulator-5554' $true)) 'Reused session accepted'
}
foreach ($field in @('error', 'attempted', 'processId', 'arguments', 'hasExited')) {
    Test-Case "cold-rejects-invalid-$field" {
        $start = New-Start
        switch ($field) {
            'error' { $start.error = 'start failed' }
            'attempted' { $start.attempted = $false }
            'processId' { $start.processId = 0 }
            'arguments' { $start.arguments = @('-no-audio', '-no-snapshot-save') }
            'hasExited' { $start.hasExited = $true }
        }
        Assert-True (-not (Test-MtrAndroidQaColdBootConfirmed $start 'emulator-5554' $true)) "Invalid $field accepted"
    }
}
Test-Case 'cold-rejects-physical-and-unbooted-targets' {
    foreach ($serial in @('R5CY933XP7P', '')) {
        Assert-True (-not (Test-MtrAndroidQaColdBootConfirmed (New-Start) $serial $true)) 'Non-booted emulator accepted'
    }
}
Test-Case 'cold-rejects-mismatched-avd' {
    Assert-True (-not (Test-MtrAndroidQaColdBootConfirmed (New-Start) 'emulator-5554' $false)) 'Unidentified AVD accepted'
}
foreach ($flag in @('-no-audio', '-no-snapshot-save')) {
    Test-Case "cold-requires-$flag" {
        $start = New-Start
        $start.arguments = @($start.arguments | Where-Object { $_ -ne $flag })
        Assert-True (-not (Test-MtrAndroidQaColdBootConfirmed $start 'emulator-5554' $true)) 'Incomplete cold policy accepted'
    }
}

# Device/host mocks: no process launches, ADB calls or volume changes in unit tests.
$script:mockQemu = '1'
$script:mockAvd = 'qa'
$script:mockCommand = 'emulator.exe -avd qa -no-audio'
$script:mockVolume = 'volume is 0 in range [0..15]'
$script:mockCalls = [System.Collections.Generic.List[string]]::new()
function Get-CimInstance { return [pscustomobject]@{ Name = 'emulator.exe'; CommandLine = $script:mockCommand; ProcessId = 42 } }
function Invoke-MtrAndroidQaAudioGuardAdb {
    param([string]$AdbPath, [string]$Serial, [string[]]$Arguments)
    $key = $Arguments -join ' '
    $script:mockCalls.Add($key)
    switch ($key) {
        'shell getprop ro.kernel.qemu' { return $script:mockQemu }
        'emu avd name' { return "$($script:mockAvd)`nOK" }
        'shell cmd media_session volume --stream 3 --set 0' { return 'set' }
        'shell cmd media_session volume --stream 3 --get' { return $script:mockVolume }
        default { throw "Unexpected mocked adb operation: $key" }
    }
}
Test-Case 'audio-host-and-stream-zero-proven' {
    $report = Assert-MtrAndroidQaAudioMuted -AdbPath 'mock' -Serial 'emulator-5554'
    Assert-True ($report.status -eq 'pass' -and $report.volume -eq 0 -and $report.media_stream -eq 3) 'Silent report invalid'
}
Test-Case 'audio-rejects-physical-before-adb' {
    $script:mockCalls.Clear()
    Assert-Throws { Assert-MtrAndroidQaAudioMuted -AdbPath 'mock' -Serial 'R5CY933XP7P' } 'non-emulator'
    Assert-True ($script:mockCalls.Count -eq 0) 'Physical device queried'
}
Test-Case 'audio-rejects-non-qemu-before-muting' {
    $script:mockQemu = '0'
    try { Assert-Throws { Assert-MtrAndroidQaAudioMuted -AdbPath 'mock' -Serial 'emulator-5554' } 'ro.kernel.qemu=0' } finally { $script:mockQemu = '1' }
}
Test-Case 'audio-rejects-unidentified-host-not-single-process-guess' {
    $script:mockCommand = 'emulator.exe -avd other -no-audio'
    try { Assert-Throws { Assert-MtrAndroidQaAudioMuted -AdbPath 'mock' -Serial 'emulator-5554' } 'could not identify' } finally { $script:mockCommand = 'emulator.exe -avd qa -no-audio' }
}
Test-Case 'audio-rejects-audible-host' {
    $script:mockCommand = 'emulator.exe -avd qa'
    try { Assert-Throws { Assert-MtrAndroidQaAudioMuted -AdbPath 'mock' -Serial 'emulator-5554' } 'not started with -no-audio' } finally { $script:mockCommand = 'emulator.exe -avd qa -no-audio' }
}
foreach ($volume in @('volume is 1 in range [0..15]', 'unavailable')) {
    Test-Case "audio-rejects-volume-$volume" {
        $script:mockVolume = $volume
        try { Assert-Throws { Assert-MtrAndroidQaAudioMuted -AdbPath 'mock' -Serial 'emulator-5554' } 'media stream 3 mute verification failed' } finally { $script:mockVolume = 'volume is 0 in range [0..15]' }
    }
}
Test-Case 'seven-android-entrypoints-bind-silent-guard' {
    $names = @('AtlasPilot', 'EmulatorInteraction', 'EmulatorMatrix', 'PowerUpLifecycle', 'CollisionRouter', 'DevEvent', 'RuntimeOwnership')
    foreach ($name in $names) {
        $source = Get-Content -LiteralPath (Join-Path $PSScriptRoot "Run-MtrAndroid${name}Qa.ps1") -Raw
        Assert-True ($source -match 'MtrAndroidQaAudioGuard.ps1' -and $source -match 'Assert-MtrAndroidQaAudioMuted -AdbPath') "Unmuted entrypoint $name"
    }
}
Test-Case 'web-launchers-explicitly-mute-audio' {
    foreach ($name in @('Run-MtrWebAtlasPilotQa.js', 'Run-MtrWebMatrixQa.js', 'run_web_playwright_function.js')) {
        $source = Get-Content -LiteralPath (Join-Path $PSScriptRoot $name) -Raw
        Assert-True ($source -match '--mute-audio' -and $source -match 'audioPolicy') "Unmuted Web launcher $name"
    }
}
Test-Case 'toolchain-integrates-policy-before-adb-probes' {
    $source = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Test-MtrAndroidToolchain.ps1') -Raw
    Assert-True ($source.IndexOf('Assert-MtrAndroidQaBootOptions') -lt $source.IndexOf("-Name 'adb-devices'")) 'Option rejection moved after ADB'
    Assert-True ($source -match 'Get-MtrAndroidQaEmulatorArguments' -and $source -match 'Test-MtrAndroidQaColdBootConfirmed' -and $source -match 'cold-boot-not-confirmed-existing-or-unverified-session') 'Cold policy not enforced'
    Assert-True ($source.Contains('if (-not $avdIdentityProbe.ok -or $observedAvdName -ne $selectedAvdName)') -and $source.Contains("if (`$bootCheck.ok -and `$bootCheck.stdout.Trim() -eq '1')")) 'Failed ADB probe could be accepted from stdout alone'
    $tokens = $null; $errors = $null
    [System.Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors) | Out-Null
    Assert-True (@($errors).Count -eq 0) 'Toolchain parse failure'
}
Write-Output ([pscustomobject]@{ status = 'PASS'; testsPassed = $passed.Count; testsTotal = $passed.Count; tests = @($passed); deviceOperations = 'NONE_MOCKS_ONLY' } | ConvertTo-Json -Depth 4)
