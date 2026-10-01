Set-StrictMode -Version Latest

function Assert-MtrAndroidQaBootOptions {
    param([bool]$EnsureEmulator, [bool]$ColdBoot, [bool]$AllowPhysicalDevice)
    if ($ColdBoot -and (-not $EnsureEmulator -or $AllowPhysicalDevice)) {
        throw 'ColdBoot requires EnsureEmulator and an emulator-only target policy.'
    }
}

function Get-MtrAndroidQaEmulatorArguments {
    param(
        [Parameter(Mandatory = $true)][string]$AvdName,
        [bool]$Windowed = $false,
        [bool]$ColdBoot = $false
    )
    $arguments = @('-avd', $AvdName, '-no-snapshot-save', '-no-boot-anim', '-no-audio')
    if ($ColdBoot) { $arguments += '-no-snapshot-load' }
    if (-not $Windowed) { $arguments += @('-no-window', '-gpu', 'swiftshader_indirect') }
    return $arguments
}

function Test-MtrAndroidQaColdBootConfirmed {
    param(
        [AllowNull()][object]$EmulatorStart,
        [AllowNull()][string]$BootCompletedSerial,
        [bool]$AvdIdentityConfirmed
    )
    # Never label an existing, failed, unverified or physical session as cold.
    return [bool](
        $null -ne $EmulatorStart -and
        $EmulatorStart.attempted -eq $true -and
        $EmulatorStart.hasExited -eq $false -and
        [string]::IsNullOrEmpty([string]$EmulatorStart.error) -and
        $null -ne $EmulatorStart.processId -and $EmulatorStart.processId -gt 0 -and
        @($EmulatorStart.arguments) -contains '-no-snapshot-load' -and
        @($EmulatorStart.arguments) -contains '-no-snapshot-save' -and
        @($EmulatorStart.arguments) -contains '-no-audio' -and
        $BootCompletedSerial -match '^emulator-\d+$' -and $AvdIdentityConfirmed
    )
}

Export-ModuleMember -Function Assert-MtrAndroidQaBootOptions, Get-MtrAndroidQaEmulatorArguments, Test-MtrAndroidQaColdBootConfirmed
