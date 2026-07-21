[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$ScopePath,
  [Parameter(Mandatory = $true)][string]$OutputPath,
  [string]$ConfigPath = 'docs/global_modernization/v3/M01/quality_gate.config.json',
  [switch]$AllowPhysicalDevice,
  [switch]$AllowDirtySource,
  [string]$PythonExecutable = 'python'
)

$ErrorActionPreference = 'Stop'
$ToolRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = (Resolve-Path (Join-Path $ToolRoot '..\..\..')).Path
$Bootstrap = Join-Path $ToolRoot 'bootstrap.py'
$ProfileArguments = @(
  '--project-root', $ProjectRoot,
  '--config', $ConfigPath,
  '--scope', $ScopePath,
  '--output', $OutputPath
)
if ($AllowPhysicalDevice) {
  $ProfileArguments += '--allow-physical-device'
}
if ($AllowDirtySource) {
  $ProfileArguments += '--allow-dirty-source'
}

& $PythonExecutable $Bootstrap '--entrypoint' 'profile' '--' @ProfileArguments
exit $LASTEXITCODE
