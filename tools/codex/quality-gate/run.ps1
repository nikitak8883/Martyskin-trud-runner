[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$ConfigPath,
  [Parameter(Mandatory = $true)][string]$OutputPath,
  [Parameter(Mandatory = $true)][string]$ContentVersion,
  [string]$SourceCommit = 'auto',
  [string]$ExpectedSourceCommit,
  [string]$RunId,
  [switch]$AllowPhysicalDevice,
  [switch]$AllowDirtySource,
  [string]$PythonExecutable = 'python'
)

$ErrorActionPreference = 'Stop'
$ToolRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = (Resolve-Path (Join-Path $ToolRoot '..\..\..')).Path
$Bootstrap = Join-Path $ToolRoot 'bootstrap.py'
$RunnerArguments = @(
  '--project-root', $ProjectRoot,
  '--config', $ConfigPath,
  '--output', $OutputPath,
  '--content-version', $ContentVersion,
  '--source-commit', $SourceCommit
)
if ($ExpectedSourceCommit) {
  $RunnerArguments += @('--expected-source-commit', $ExpectedSourceCommit)
}
if ($RunId) {
  $RunnerArguments += @('--run-id', $RunId)
}
if ($AllowPhysicalDevice) {
  $RunnerArguments += '--allow-physical-device'
}
if ($AllowDirtySource) {
  $RunnerArguments += '--allow-dirty-source'
}

& $PythonExecutable $Bootstrap '--' @RunnerArguments
exit $LASTEXITCODE
