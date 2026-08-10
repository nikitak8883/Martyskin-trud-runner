[CmdletBinding()]
param(
    [string]$ProjectRoot,
    [string]$ConfigPath = 'build-android-emulator.json',
    [string]$ContractPath = 'tools/codex/android-build-toolchain.contract.json',
    [switch]$CheckGeneratedExport,
    [switch]$RequireGeneratedExport
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

Import-Module (Join-Path $scriptRoot 'MtrAndroidBuildToolchain.psm1') -Force

try {
    $result = Test-MtrAndroidBuildToolchain `
        -ProjectRoot $ProjectRoot `
        -ConfigPath $ConfigPath `
        -ContractPath $ContractPath `
        -CheckGeneratedExport:$CheckGeneratedExport `
        -RequireGeneratedExport:$RequireGeneratedExport
} catch {
    $result = [pscustomobject][ordered]@{
        contract = 'mtr.android_build_toolchain_preflight'
        schemaVersion = 1
        status = 'BLOCKED'
        configPath = $ConfigPath
        blockers = @('preflight-exception')
        error = $_.Exception.Message
    }
}

[Console]::Out.WriteLine(($result | ConvertTo-Json -Depth 12))
if ($result.status -ne 'PASS') { exit 2 }
