param(
  [string]$BuildDir = "C:\Test\MTRCocosCreator\build\web-mobile"
)

$ErrorActionPreference = "Stop"

$settingsPath = Join-Path $BuildDir "src\settings.json"
if (-not (Test-Path -LiteralPath $settingsPath)) {
  throw "settings.json not found: $settingsPath"
}

$raw = Get-Content -LiteralPath $settingsPath -Raw
$settings = $raw | ConvertFrom-Json

if (-not $settings.rendering) {
  $settings | Add-Member -NotePropertyName rendering -NotePropertyValue ([pscustomobject]@{})
}

$settings.rendering.customPipeline = $false
$settings.rendering.renderPipeline = ""

$json = $settings | ConvertTo-Json -Depth 100 -Compress
Set-Content -LiteralPath $settingsPath -Value $json -Encoding UTF8

Write-Host "Patched Web settings for the configured Cocos render pipeline: $settingsPath"
