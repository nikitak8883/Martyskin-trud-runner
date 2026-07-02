param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'

$script = Join-Path $ProjectRoot 'tools\asset_generation\build_martyshkin_texture10_backgrounds.py'
if (-not (Test-Path -LiteralPath $script)) {
    throw "Texture10 background pipeline script not found: $script"
}

& $Python $script --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    throw "Texture10 background pipeline failed with exit code $LASTEXITCODE"
}
