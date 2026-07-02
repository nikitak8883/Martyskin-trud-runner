param(
    [string]$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path,
    [string]$LogPath = (Join-Path $ProjectRoot ("logs\entrypoint-router-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd')))
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'codex\MtrEntrypoint.psm1') -Force

$result = Test-MtrEntrypointQuoting -LogPath $LogPath
$result | ConvertTo-Json -Depth 8
if (-not $result.passed) {
    exit 1
}
