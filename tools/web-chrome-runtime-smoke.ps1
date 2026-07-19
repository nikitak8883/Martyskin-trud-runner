param(
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$true)][string]$BrowserPath,
    [int]$Port = 9370,
    [string]$ProfileDir = "$env:TEMP\mtr-runtime-smoke-profile",
    [string]$ScreenshotPath = "screenshots\web-runtime-smoke.png",
    [string]$BrowserLogPath = "logs\web-runtime-smoke-browser.log",
    [string]$ConsoleLogPath = "",
    [string]$ProbePath = "logs\web-runtime-smoke-probe.json",
    [int]$TimeoutSeconds = 75,
    [string]$WaitForLogPattern = "",
    [int]$WaitForLogPatternTimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"

function Stop-ListenersOnPort([int]$LocalPort) {
    Get-NetTCPConnection -LocalPort $LocalPort -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}

function Read-CdpMessage($Socket, [int]$TimeoutMs = 1000) {
    $buffer = New-Object byte[] 1048576
    $builder = [Text.StringBuilder]::new()
    do {
        $segment = [ArraySegment[byte]]::new($buffer)
        $task = $Socket.ReceiveAsync($segment, [Threading.CancellationToken]::None)
        try {
            if (-not $task.Wait($TimeoutMs)) { return $null }
        } catch {
            return $null
        }
        if ($task.Result.Count -le 0) { return $null }
        [void]$builder.Append([Text.Encoding]::UTF8.GetString($buffer, 0, $task.Result.Count))
    } while (-not $task.Result.EndOfMessage)
    return $builder.ToString()
}

function Send-Cdp($Socket, [ref]$NextId, [string]$Method, $Params) {
    $id = $NextId.Value
    $NextId.Value = $NextId.Value + 1
    $payload = @{ id = $id; method = $Method; params = $Params } | ConvertTo-Json -Depth 30 -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($payload)
    $Socket.SendAsync([ArraySegment[byte]]::new($bytes), [Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None).Wait()
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        $raw = Read-CdpMessage $Socket 1000
        if (-not $raw) { continue }
        $msg = $raw | ConvertFrom-Json
        if ($msg.id -eq $id) { return $msg }
        if (-not $msg.id) { Add-CdpConsoleEvent $msg | Out-Null }
    }
    throw "Timed out waiting for CDP response to $Method"
}

function Get-CdpArgText($Arg) {
    if ($null -ne $Arg.value) { return [string]$Arg.value }
    if ($Arg.unserializableValue) { return [string]$Arg.unserializableValue }
    if ($Arg.description) { return [string]$Arg.description }
    return ""
}

function Add-CdpConsoleEvent($Msg) {
    $entryType = ""
    $text = ""

    if ($Msg.method -eq "Runtime.consoleAPICalled") {
        $entryType = [string]$Msg.params.type
        $parts = @()
        foreach ($arg in @($Msg.params.args)) {
            $part = Get-CdpArgText $arg
            if ($part) { $parts += $part }
        }
        $text = ($parts -join " ")
    } elseif ($Msg.method -eq "Log.entryAdded") {
        $entryType = [string]$Msg.params.entry.level
        $text = [string]$Msg.params.entry.text
    } else {
        return $null
    }

    if (-not $text) { return $null }

    $event = [pscustomobject]@{
        ts = (Get-Date).ToString("o")
        method = [string]$Msg.method
        type = $entryType
        text = $text
    }
    $script:CdpConsoleEvents.Add($event) | Out-Null
    if ($script:ResolvedConsoleLogPath) {
        try {
            Add-Content -LiteralPath $script:ResolvedConsoleLogPath -Value ($event | ConvertTo-Json -Depth 8 -Compress) -Encoding UTF8
        } catch {
            # Console-event evidence is helpful but must not break the smoke probe.
        }
    }
    return $text
}

function Pump-CdpConsole($Socket, [int]$TimeoutMs = 250) {
    $texts = @()
    while ($true) {
        $raw = Read-CdpMessage $Socket $TimeoutMs
        if (-not $raw) { break }
        try {
            $msg = $raw | ConvertFrom-Json
        } catch {
            $TimeoutMs = 1
            continue
        }
        if ($msg.id) {
            $TimeoutMs = 1
            continue
        }
        $text = Add-CdpConsoleEvent $msg
        if ($text) { $texts += $text }
        $TimeoutMs = 1
    }
    return $texts
}

function Test-CdpConsolePattern([string]$Pattern) {
    if (-not $Pattern) { return $false }
    foreach ($event in @($script:CdpConsoleEvents)) {
        if ($event.text -match $Pattern) { return $true }
    }
    return $false
}

function Test-BrowserLogPattern([string]$Pattern) {
    if (-not $Pattern) { return $false }
    if (-not (Test-Path -LiteralPath $BrowserLogPath)) { return $false }
    $text = Get-Content -LiteralPath $BrowserLogPath -Raw -ErrorAction SilentlyContinue
    return ($text -match $Pattern)
}

if (-not $ConsoleLogPath) {
    $probeDir = Split-Path -Parent $ProbePath
    $probeBase = [IO.Path]::GetFileNameWithoutExtension($ProbePath)
    $ConsoleLogPath = Join-Path $probeDir "$probeBase.console.jsonl"
}

$script:ResolvedConsoleLogPath = $ConsoleLogPath
$script:CdpConsoleEvents = [System.Collections.Generic.List[object]]::new()

$dirs = @(
    (Split-Path -Parent $ScreenshotPath),
    (Split-Path -Parent $BrowserLogPath),
    (Split-Path -Parent $ProbePath),
    (Split-Path -Parent $ConsoleLogPath)
) | Where-Object { $_ }
foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Remove-Item -LiteralPath $ScreenshotPath, $BrowserLogPath, $ProbePath, $ConsoleLogPath -Force -ErrorAction SilentlyContinue
Stop-ListenersOnPort $Port
Remove-Item -LiteralPath $ProfileDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$args = @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=$ProfileDir",
    "--no-first-run",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-backgrounding-occluded-windows",
    "--disable-features=CalculateNativeWinOcclusion,Translate",
    "--disable-popup-blocking",
    "--disable-sync",
    "--enable-logging",
    "--log-level=0",
    "--log-file=$BrowserLogPath",
    "--ignore-gpu-blocklist",
    "--autoplay-policy=no-user-gesture-required",
    "--window-size=1280,720",
    "--force-device-scale-factor=1",
    "about:blank"
)
$browser = Start-Process -FilePath $BrowserPath -ArgumentList $args -WindowStyle Hidden -PassThru
$socket = $null

try {
    $versionUrl = "http://127.0.0.1:$Port/json/version"
    $deadline = (Get-Date).AddSeconds(15)
    do {
        try {
            Invoke-RestMethod -Uri $versionUrl -TimeoutSec 1 | Out-Null
            break
        } catch {
            Start-Sleep -Milliseconds 300
        }
    } while ((Get-Date) -lt $deadline)

    $tabs = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/json/list" -TimeoutSec 3
    $tab = @($tabs | Where-Object { $_.type -eq "page" } | Select-Object -First 1)[0]
    if (-not $tab) { throw "No page target found before navigation" }

    $socket = [Net.WebSockets.ClientWebSocket]::new()
    $socket.ConnectAsync([Uri]$tab.webSocketDebuggerUrl, [Threading.CancellationToken]::None).Wait()
    $nextId = 1
    Send-Cdp $socket ([ref]$nextId) "Runtime.enable" @{} | Out-Null
    Send-Cdp $socket ([ref]$nextId) "Page.enable" @{} | Out-Null
    try { Send-Cdp $socket ([ref]$nextId) "Log.enable" @{} | Out-Null } catch {}
    Send-Cdp $socket ([ref]$nextId) "Page.navigate" @{ url = $Url } | Out-Null

    $ready = $false
    $readyDeadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $readyDeadline) {
        if ($browser.HasExited) { throw "Browser exited before runtime became ready" }
        Pump-CdpConsole $socket 250 | Out-Null
        if ((Test-CdpConsolePattern "MTR_RUNTIME_CORE_READY") -or (Test-BrowserLogPattern "MTR_RUNTIME_CORE_READY")) {
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 100
    }

    $waitForLogPatternReady = $null
    if ($WaitForLogPattern) {
        $waitForLogPatternReady = $false
        $patternDeadline = (Get-Date).AddSeconds($WaitForLogPatternTimeoutSeconds)
        while ((Get-Date) -lt $patternDeadline) {
            if ($browser.HasExited) { throw "Browser exited before WaitForLogPattern was observed" }
            Pump-CdpConsole $socket 250 | Out-Null
            if ((Test-CdpConsolePattern $WaitForLogPattern) -or (Test-BrowserLogPattern $WaitForLogPattern)) {
                $waitForLogPatternReady = $true
                break
            }
            Start-Sleep -Milliseconds 100
        }
    }

    Start-Sleep -Milliseconds 500
    Pump-CdpConsole $socket 100 | Out-Null
    if ($socket) {
        $socket.Dispose()
        $socket = $null
    }

    $tabs = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/json/list" -TimeoutSec 3
    $tab = @($tabs | Where-Object { $_.type -eq "page" -and $_.url -like "http*" } | Select-Object -First 1)[0]
    if (-not $tab) { throw "No page target found after runtime wait" }

    $socket = [Net.WebSockets.ClientWebSocket]::new()
    $socket.ConnectAsync([Uri]$tab.webSocketDebuggerUrl, [Threading.CancellationToken]::None).Wait()
    $nextId = 1
    try { Send-Cdp $socket ([ref]$nextId) "Page.enable" @{} | Out-Null } catch {}
    $probe = Send-Cdp $socket ([ref]$nextId) "Runtime.evaluate" @{
        expression = "(() => ({href: location.href, readyState: document.readyState, title: document.title, bodyText: document.body ? document.body.innerText : '', canvasCount: document.querySelectorAll('canvas').length, canvasSize: (() => { const c=document.querySelector('canvas'); return c ? [c.width,c.height,c.clientWidth,c.clientHeight] : null; })()}))()"
        returnByValue = $true
    }
    $shot = Send-Cdp $socket ([ref]$nextId) "Page.captureScreenshot" @{ format = "png"; fromSurface = $true }
    [IO.File]::WriteAllBytes((Resolve-Path -LiteralPath (Split-Path -Parent $ScreenshotPath)).Path + "\" + (Split-Path -Leaf $ScreenshotPath), [Convert]::FromBase64String($shot.result.data))
    $targetUrl = $probe.result.result.value.href
    if (-not $targetUrl) { $targetUrl = $Url }

    $result = [pscustomobject]@{
        url = $Url
        runtimeReady = $ready
        targetUrl = $targetUrl
        waitForLogPattern = $WaitForLogPattern
        waitForLogPatternReady = $waitForLogPatternReady
        probe = $probe.result.result.value
        screenshot = if (Test-Path -LiteralPath $ScreenshotPath) { (Resolve-Path -LiteralPath $ScreenshotPath).Path } else { $null }
        browserLog = if (Test-Path -LiteralPath $BrowserLogPath) { (Resolve-Path -LiteralPath $BrowserLogPath).Path } else { $null }
        consoleLog = if (Test-Path -LiteralPath $ConsoleLogPath) { (Resolve-Path -LiteralPath $ConsoleLogPath).Path } else { $null }
        consoleEventCount = $script:CdpConsoleEvents.Count
        consoleMessagesSample = @($script:CdpConsoleEvents | Select-Object -Last 25)
    }
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ProbePath -Encoding UTF8
    $result | ConvertTo-Json -Depth 12
}
finally {
    if ($socket) { $socket.Dispose() }
    if ($browser -and -not $browser.HasExited) { Stop-Process -Id $browser.Id -Force -ErrorAction SilentlyContinue }
    Stop-ListenersOnPort $Port
}
