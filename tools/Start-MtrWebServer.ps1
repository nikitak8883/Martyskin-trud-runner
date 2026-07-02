param(
    [string]$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path,
    [string]$Root = (Join-Path $ProjectRoot 'build\web-mobile'),
    [int]$Port = 8123,
    [bool]$StopExisting = $true,
    [int]$TimeoutSeconds = 20,
    [string]$LogPath = (Join-Path $ProjectRoot ("logs\entrypoint-router-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd'))),
    [string]$StdoutPath = (Join-Path $ProjectRoot ("logs\web-mobile-server-browser-{0}.out.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))),
    [string]$StderrPath = (Join-Path $ProjectRoot ("logs\web-mobile-server-browser-{0}.err.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))),
    [string]$StatusPath = (Join-Path $ProjectRoot ("logs\web-mobile-server-browser-status-{0}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss')))
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'codex\MtrEntrypoint.psm1') -Force

if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    throw "Web build directory not found: $Root"
}

if ($StopExisting) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}

$python = (Get-Command python -ErrorAction Stop | Select-Object -First 1).Source
$run = Invoke-MtrEntrypoint `
    -FilePath $python `
    -ArgumentList @('-m', 'http.server', [string]$Port, '--bind', '127.0.0.1', '--directory', $Root) `
    -WorkingDirectory $ProjectRoot `
    -LogPath $LogPath `
    -RedirectStandardOutput $StdoutPath `
    -RedirectStandardError $StderrPath `
    -PassThru

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$listening = $false
while ((Get-Date) -lt $deadline) {
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        $listening = $true
        break
    }

    $process = Get-Process -Id $run.processId -ErrorAction SilentlyContinue
    if (-not $process) { break }
    Start-Sleep -Milliseconds 250
}

$result = [pscustomobject]@{
    url = "http://127.0.0.1:$Port/index.html"
    root = (Resolve-Path -LiteralPath $Root).Path
    processId = $run.processId
    listening = $listening
    stdout = $StdoutPath
    stderr = $StderrPath
    entrypointLog = $LogPath
    status = $StatusPath
    autocorrections = $run.autocorrections
}

$json = $result | ConvertTo-Json -Depth 8
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StatusPath) | Out-Null
Set-Content -LiteralPath $StatusPath -Value $json -Encoding UTF8
[Console]::Out.WriteLine($json)
if (-not $listening) {
    exit 1
}
