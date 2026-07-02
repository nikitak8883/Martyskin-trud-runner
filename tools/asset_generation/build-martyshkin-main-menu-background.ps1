param(
    [string]$ProjectRoot = "C:\Test\MTRCocosCreator"
)

$ErrorActionPreference = "Stop"
$script = Join-Path $ProjectRoot "tools\asset_generation\build_martyshkin_main_menu_background.py"
python $script
