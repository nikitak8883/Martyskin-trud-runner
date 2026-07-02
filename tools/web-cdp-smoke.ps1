param(
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$true)][string]$BrowserPath,
    [int]$Port = 9350,
    [string]$ProfileDir = "$env:TEMP\mtr-cdp-profile",
    [string]$ScreenshotPath = "screenshots\web-cdp-smoke.png",
    [string]$ConsoleLogPath = "logs\web-cdp-console.log",
    [string]$EventLogPath = "logs\web-cdp-events.jsonl",
    [string]$BrowserLogPath = "logs\web-cdp-browser.log",
    [int]$PostReadyDelayMs = 2500,
    [int]$TimeoutSeconds = 45
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

function Format-Exception($ErrorRecord) {
    $messages = [System.Collections.Generic.List[string]]::new()
    $ex = $ErrorRecord.Exception
    while ($ex) {
        $messages.Add($ex.Message)
        $ex = $ex.InnerException
    }
    return ($messages -join " | ")
}

function Send-Cdp($Socket, [ref]$NextId, [string]$Method, $Params, [System.Collections.Generic.List[string]]$Events) {
    $id = $NextId.Value
    $NextId.Value = $NextId.Value + 1
    $payload = @{ id = $id; method = $Method; params = $Params } | ConvertTo-Json -Depth 30 -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($payload)
    try {
        $Socket.SendAsync([ArraySegment[byte]]::new($bytes), [Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None).Wait()
    } catch {
        throw "CDP send failed for ${Method}: $(Format-Exception $_)"
    }
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline) {
        $raw = Read-CdpMessage $Socket 1000
        if (-not $raw) { continue }
        $msg = $raw | ConvertFrom-Json
        if ($msg.id -eq $id) { return $msg }
        $Events.Add($raw)
    }
    throw "Timed out waiting for CDP response to $Method"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ScreenshotPath), (Split-Path -Parent $ConsoleLogPath), (Split-Path -Parent $EventLogPath), (Split-Path -Parent $BrowserLogPath) | Out-Null
Remove-Item -LiteralPath $ConsoleLogPath, $EventLogPath, $BrowserLogPath -Force -ErrorAction SilentlyContinue
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
    "--disable-features=Translate",
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

try {
    $versionUrl = "http://127.0.0.1:$Port/json/version"
    $deadline = (Get-Date).AddSeconds(15)
    do {
        try {
            $version = Invoke-RestMethod -Uri $versionUrl -TimeoutSec 1
            break
        } catch {
            Start-Sleep -Milliseconds 300
        }
    } while ((Get-Date) -lt $deadline)
    if (-not $version) { throw "Browser CDP did not start on port $Port" }

    $tabs = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/json/list" -TimeoutSec 3
    $tab = @($tabs | Where-Object { $_.type -eq "page" } | Select-Object -First 1)[0]
    if (-not $tab) { throw "No page target found" }

    $socket = [Net.WebSockets.ClientWebSocket]::new()
    $socket.ConnectAsync([Uri]$tab.webSocketDebuggerUrl, [Threading.CancellationToken]::None).Wait()
    $nextId = 1
    $events = [System.Collections.Generic.List[string]]::new()

    Send-Cdp $socket ([ref]$nextId) "Runtime.enable" @{} $events | Out-Null
    Send-Cdp $socket ([ref]$nextId) "Log.enable" @{} $events | Out-Null
    Send-Cdp $socket ([ref]$nextId) "Network.enable" @{} $events | Out-Null
    Send-Cdp $socket ([ref]$nextId) "Page.enable" @{} $events | Out-Null
    Send-Cdp $socket ([ref]$nextId) "Emulation.setDeviceMetricsOverride" @{
        width = 1280; height = 720; deviceScaleFactor = 1; mobile = $false
    } $events | Out-Null
    Send-Cdp $socket ([ref]$nextId) "Page.navigate" @{ url = $Url } $events | Out-Null

    $runtimeReady = $false
    $end = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $end) {
        $raw = Read-CdpMessage $socket 1000
        if ($raw) {
            $events.Add($raw)
            if ($raw -match "MTR_RUNTIME_CORE_READY") { $runtimeReady = $true; break }
        }
    }

    if ($runtimeReady -and $PostReadyDelayMs -gt 0) {
        $delayEnd = (Get-Date).AddMilliseconds($PostReadyDelayMs)
        while ((Get-Date) -lt $delayEnd) {
            $raw = Read-CdpMessage $socket 250
            if ($raw) { $events.Add($raw) }
        }
    }

    $probe = $null
    $probeError = $null
    try {
        $probe = Send-Cdp $socket ([ref]$nextId) "Runtime.evaluate" @{
            expression = "(() => ({readyState: document.readyState, title: document.title, bodyText: document.body ? document.body.innerText : '', canvasCount: document.querySelectorAll('canvas').length, canvasSize: (() => { const c=document.querySelector('canvas'); return c ? [c.width,c.height,c.clientWidth,c.clientHeight] : null; })()}))()"
            returnByValue = $true
        } $events
    } catch {
        $probeError = Format-Exception $_
    }

    $shotError = $null
    try {
        $shot = Send-Cdp $socket ([ref]$nextId) "Page.captureScreenshot" @{ format = "png"; fromSurface = $true } $events
        [IO.File]::WriteAllBytes((Resolve-Path -LiteralPath (Split-Path -Parent $ScreenshotPath)).Path + "\" + (Split-Path -Leaf $ScreenshotPath), [Convert]::FromBase64String($shot.result.data))
    } catch {
        $shotError = Format-Exception $_
    }

    foreach ($eventRaw in $events) {
        Add-Content -LiteralPath $EventLogPath -Value $eventRaw -Encoding UTF8
        if ($eventRaw -match "Runtime.consoleAPICalled|Runtime.exceptionThrown|Log.entryAdded|Network.loadingFailed|MTR_") {
            Add-Content -LiteralPath $ConsoleLogPath -Value $eventRaw -Encoding UTF8
        }
    }

    [pscustomobject]@{
        url = $Url
        runtimeReady = $runtimeReady
        probe = if ($probe) { $probe.result.result.value } else { $null }
        probeError = $probeError
        screenshotError = $shotError
        screenshot = if (Test-Path -LiteralPath $ScreenshotPath) { (Resolve-Path -LiteralPath $ScreenshotPath).Path } else { $null }
        consoleLog = (Resolve-Path -LiteralPath $ConsoleLogPath -ErrorAction SilentlyContinue).Path
        eventLog = (Resolve-Path -LiteralPath $EventLogPath).Path
        browserLog = (Resolve-Path -LiteralPath $BrowserLogPath -ErrorAction SilentlyContinue).Path
    } | ConvertTo-Json -Depth 12
}
finally {
    if ($socket) { $socket.Dispose() }
    if ($browser -and -not $browser.HasExited) { Stop-Process -Id $browser.Id -Force -ErrorAction SilentlyContinue }
    Stop-ListenersOnPort $Port
}
