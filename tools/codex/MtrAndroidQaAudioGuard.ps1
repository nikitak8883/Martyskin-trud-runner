Set-StrictMode -Version Latest

function Invoke-MtrAndroidQaAudioGuardAdb {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AdbPath,
        [Parameter(Mandatory = $true)]
        [string]$Serial,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = @(& $AdbPath -s $Serial @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    $text = $output -join "`n"
    if ($exitCode -ne 0) {
        throw "adb audio guard failed ($exitCode): $($Arguments -join ' ')`n$text"
    }
    return $text
}

function Assert-MtrAndroidQaAudioMuted {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$AdbPath,
        [Parameter(Mandatory = $true)]
        [string]$Serial
    )

    if ($Serial -notmatch '^emulator-\d+$') {
        throw "Silent Android QA guard rejected non-emulator serial '$Serial'."
    }

    $qemu = (Invoke-MtrAndroidQaAudioGuardAdb -AdbPath $AdbPath -Serial $Serial -Arguments @(
        'shell', 'getprop', 'ro.kernel.qemu'
    )).Trim()
    if ($qemu -ne '1') {
        throw "Silent Android QA guard rejected '$Serial': ro.kernel.qemu=$qemu."
    }

    $avdOutput = Invoke-MtrAndroidQaAudioGuardAdb -AdbPath $AdbPath -Serial $Serial -Arguments @(
        'emu', 'avd', 'name'
    )
    $avdName = @(
        $avdOutput -split '\r?\n' |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ -and $_ -ne 'OK' }
    ) | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace([string]$avdName)) {
        throw "Silent Android QA guard could not resolve the AVD name for '$Serial'."
    }

    $emulatorProcesses = @(
        Get-CimInstance Win32_Process -ErrorAction Stop |
            Where-Object {
                $_.Name -match '^(?:emulator|qemu-system-.+)\.exe$' -and
                -not [string]::IsNullOrWhiteSpace([string]$_.CommandLine)
            }
    )
    $escapedAvd = [regex]::Escape([string]$avdName)
    $matchingProcesses = @(
        $emulatorProcesses | Where-Object {
            $_.CommandLine -match "(?i)(?:^|\s)-avd(?:\s+|=)(?:`"?)$escapedAvd(?:`"?)(?:\s|$)"
        }
    )
    if ($matchingProcesses.Count -eq 0 -and $emulatorProcesses.Count -eq 1) {
        $matchingProcesses = @($emulatorProcesses[0])
    }
    if ($matchingProcesses.Count -eq 0) {
        throw "Silent Android QA guard could not identify the host emulator process for AVD '$avdName'."
    }

    $noAudioProcesses = @(
        $matchingProcesses | Where-Object { $_.CommandLine -match '(?i)(?:^|\s)-no-audio(?:\s|$)' }
    )
    if ($noAudioProcesses.Count -eq 0) {
        throw "Android QA is blocked: AVD '$avdName' was not started with -no-audio. Restart it through Test-MtrAndroidToolchain.ps1 -EnsureEmulator."
    }

    $setOutput = Invoke-MtrAndroidQaAudioGuardAdb -AdbPath $AdbPath -Serial $Serial -Arguments @(
        'shell', 'cmd', 'media_session', 'volume', '--stream', '3', '--set', '0'
    )
    $state = Invoke-MtrAndroidQaAudioGuardAdb -AdbPath $AdbPath -Serial $Serial -Arguments @(
        'shell', 'cmd', 'media_session', 'volume', '--stream', '3', '--get'
    )
    $volumeMatch = [regex]::Match($state, 'volume is (?<volume>\d+)\b')
    if (-not $volumeMatch.Success -or [int]$volumeMatch.Groups['volume'].Value -ne 0) {
        throw "Android QA is blocked: media stream 3 mute verification failed: $state"
    }

    return [pscustomobject]@{
        policy = 'host-no-audio-plus-media-stream-zero'
        status = 'pass'
        avd_name = [string]$avdName
        startup_argument = '-no-audio'
        host_process_ids = @($noAudioProcesses | ForEach-Object { [int]$_.ProcessId })
        media_stream = 3
        volume = 0
        set_output = $setOutput.Trim()
        verification = $state.Trim()
    }
}
