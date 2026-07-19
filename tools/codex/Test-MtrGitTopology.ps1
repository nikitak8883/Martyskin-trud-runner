[CmdletBinding()]
param(
    [string]$Root = 'C:\Projects\Monkey Work',
    [string]$ChildRelative = '_github/Martyskin-trud-runner',
    [string]$ExpectedUrl = 'https://github.com/nikitak8883/Martyskin-trud-runner.git',
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

function Invoke-GitText {
    param(
        [Parameter(Mandatory = $true)][string]$Repository,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $output = & git -C $Repository @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git -C '$Repository' $($Arguments -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return @($output | ForEach-Object { $_.ToString() })
}

$rootPath = (Resolve-Path -LiteralPath $Root).Path
$childPath = (Resolve-Path -LiteralPath (Join-Path $rootPath $ChildRelative)).Path
$gitModulesPath = Join-Path $rootPath '.gitmodules'
$failures = [System.Collections.Generic.List[string]]::new()

$parentTop = @(Invoke-GitText -Repository $rootPath -Arguments @('rev-parse', '--show-toplevel'))[0]
if (-not [System.IO.Path]::GetFullPath($parentTop).Equals($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    $failures.Add("Parent root mismatch: $parentTop")
}

$stageLine = (Invoke-GitText -Repository $rootPath -Arguments @('ls-files', '--stage', '--', $ChildRelative) | Select-Object -First 1)
if ($stageLine -notmatch '^160000\s+([0-9a-f]{40})\s+\d+\s+') {
    $failures.Add('Parent index does not contain a mode-160000 gitlink for the Pages repository.')
    $gitlinkCommit = $null
} else {
    $gitlinkCommit = $Matches[1]
}

if (-not (Test-Path -LiteralPath $gitModulesPath -PathType Leaf)) {
    $failures.Add('.gitmodules is missing.')
    $mappedPath = $null
    $mappedUrl = $null
} else {
    $mappedPath = (& git config -f $gitModulesPath --get 'submodule._github/Martyskin-trud-runner.path' 2>$null)
    $mappedUrl = (& git config -f $gitModulesPath --get 'submodule._github/Martyskin-trud-runner.url' 2>$null)
    if ($LASTEXITCODE -ne 0) {
        $failures.Add('The expected submodule mapping cannot be read from .gitmodules.')
    }
    if ($mappedPath -ne $ChildRelative) {
        $failures.Add("Mapped submodule path is '$mappedPath', expected '$ChildRelative'.")
    }
    if ($mappedUrl -ne $ExpectedUrl) {
        $failures.Add("Mapped submodule URL is '$mappedUrl', expected '$ExpectedUrl'.")
    }
}

$childTop = @(Invoke-GitText -Repository $childPath -Arguments @('rev-parse', '--show-toplevel'))[0]
if (-not [System.IO.Path]::GetFullPath($childTop).Equals($childPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    $failures.Add("Child root mismatch: $childTop")
}

$childHead = @(Invoke-GitText -Repository $childPath -Arguments @('rev-parse', 'HEAD'))[0]
$childBranch = @(Invoke-GitText -Repository $childPath -Arguments @('branch', '--show-current'))[0]
$childStatus = @(Invoke-GitText -Repository $childPath -Arguments @('status', '--porcelain=v1'))
if ($childStatus.Count -gt 0) {
    $failures.Add('Pages repository is dirty.')
}
if ($gitlinkCommit -and $gitlinkCommit -ne $childHead) {
    $failures.Add("Parent gitlink $gitlinkCommit does not match child HEAD $childHead.")
}

$result = [ordered]@{
    schema_version = 1
    generated_at = [DateTimeOffset]::Now.ToString('o')
    pass = ($failures.Count -eq 0)
    parent = [ordered]@{
        root = $rootPath
        head = @(Invoke-GitText -Repository $rootPath -Arguments @('rev-parse', 'HEAD'))[0]
        branch = @(Invoke-GitText -Repository $rootPath -Arguments @('branch', '--show-current'))[0]
        gitlink = $gitlinkCommit
    }
    pages = [ordered]@{
        root = $childPath
        head = $childHead
        branch = $childBranch
        clean = ($childStatus.Count -eq 0)
        mapped_path = $mappedPath
        mapped_url = $mappedUrl
    }
    failures = @($failures)
}

$json = $result | ConvertTo-Json -Depth 8
if ($OutputPath) {
    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
    $outputDirectory = Split-Path -Parent $resolvedOutput
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    [System.IO.File]::WriteAllText($resolvedOutput, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

$json
if (-not $result.pass) {
    exit 1
}
