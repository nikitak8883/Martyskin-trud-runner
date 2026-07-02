param(
    [string]$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path,
    [string]$CocosExe = 'C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe',
    [string]$ConfigPath = 'build-web-mobile.json',
    [string]$LogDest = ("creator-web-ui-icons-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss')),
    [int]$TimeoutSeconds = 900,
    [string]$EntrypointLogPath = (Join-Path $ProjectRoot ("logs\entrypoint-router-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd'))),
    [string]$StdoutPath = (Join-Path $ProjectRoot ("logs\creator-web-ui-icons-wrapper-{0}.out.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))),
    [string]$StderrPath = (Join-Path $ProjectRoot ("logs\creator-web-ui-icons-wrapper-{0}.err.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss')))
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'codex\MtrEntrypoint.psm1') -Force

function Test-MtrAndroidApkPayload {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$ApkPath)

    $summary = [ordered]@{
        apkPath = $ApkPath
        exists = $false
        entry = $null
        hasOldMainMenuLayerDraw = $null
        hasNewMainMenuGrid = $null
        hasCurrentRuntimeMenu = $null
        hasNativeQaStartupRoute = $null
        hasStyledNameFlow = $null
        hasNewBonusPngPack = $null
        containsPrimatalPassword = $null
        containsPromptCall = $null
        ok = $false
        error = $null
    }

    if (-not (Test-Path -LiteralPath $ApkPath -PathType Leaf)) {
        $summary.error = 'apk-not-found'
        return [pscustomobject]$summary
    }

    $summary.exists = $true
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
        $zip = [System.IO.Compression.ZipFile]::OpenRead($ApkPath)
        try {
            $entry = $zip.Entries |
                Where-Object { $_.FullName -eq 'assets/assets/main/index.js' -or $_.FullName -eq 'assets/main/index.js' } |
                Select-Object -First 1
            if (-not $entry) {
                $summary.error = 'main-index-js-not-found'
                return [pscustomobject]$summary
            }

            $summary.entry = $entry.FullName
            $stream = $entry.Open()
            try {
                $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8, $true)
                try {
                    $text = $reader.ReadToEnd()
                } finally {
                    $reader.Dispose()
                }
            } finally {
                if ($stream) { $stream.Dispose() }
            }

            $summary.hasOldMainMenuLayerDraw = (
                $text -match 'const mid = this\.drawAssetSprite\(MAIN_MENU_BACKGROUND_LAYER_KEYS\[1\]' -or
                $text -match 'this\.button\(430, 275, 420, 52,'
            )
            $summary.hasNewMainMenuGrid = (
                $text -match 'const mainButtonW = 382' -and
                $text -match 'const rowY = \[220, 350, 480\]'
            )
            $summary.hasCurrentRuntimeMenu = (
                $text -match 'MTR_MAIN_MENU_DEFERRED_BUTTON_PRELOAD_REQUESTED' -or
                $text -match 'mtr_last_main_menu_ui_main_menu_button'
            )
            $summary.hasNativeQaStartupRoute = (
                $text -match 'MTR_NATIVE_STARTUP_QUERY_READY' -and
                $text -match 'getStartupQuery'
            )
            $summary.hasStyledNameFlow = (
                $text -match 'mtr_start_menu_button_save_name_01' -or
                $text -match 'mtr_player_name'
            )
            $summary.hasNewBonusPngPack = (
                $text -match 'bonus_jump_spring_01' -and
                $text -match 'bonus_dash_bolt_01' -and
                $text -match 'bonus_extra_life_01'
            )
            $summary.containsPrimatalPassword = ($text -match 'primatal')
            $summary.containsPromptCall = ($text -match 'prompt\(')
            $summary.ok = (
                -not $summary.hasOldMainMenuLayerDraw -and
                $summary.hasCurrentRuntimeMenu -and
                $summary.hasNativeQaStartupRoute -and
                $summary.hasStyledNameFlow -and
                $summary.hasNewBonusPngPack -and
                $summary.containsPrimatalPassword -and
                -not $summary.containsPromptCall
            )
        } finally {
            if ($zip) { $zip.Dispose() }
        }
    } catch {
        $summary.error = $_.Exception.Message
    }

    return [pscustomobject]$summary
}

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Project root not found: $ProjectRoot"
}

$configCandidate = if ([System.IO.Path]::IsPathRooted($ConfigPath)) {
    $ConfigPath
} else {
    Join-Path $ProjectRoot $ConfigPath
}
if (-not (Test-Path -LiteralPath $configCandidate -PathType Leaf)) {
    throw "Cocos build config not found: $configCandidate"
}
$projectRootResolved = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
$configResolved = (Resolve-Path -LiteralPath $configCandidate).Path
$configJson = Get-Content -LiteralPath $configResolved -Raw | ConvertFrom-Json
$isAndroidBuild = ([string]$configJson.platform) -eq 'android'
$outputName = [string]$configJson.outputName
if ([string]::IsNullOrWhiteSpace($outputName)) {
    $outputName = if ($isAndroidBuild) { 'android' } else { '' }
}
$configArgPath = $configResolved
$projectPrefix = $projectRootResolved + [System.IO.Path]::DirectorySeparatorChar
if ($configResolved.StartsWith($projectPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    $configArgPath = $configResolved.Substring($projectPrefix.Length)
}

$buildArg = "configPath=$configArgPath;logDest=$LogDest"
$cocosLogPath = Join-Path $ProjectRoot $LogDest
$run = Invoke-MtrEntrypoint `
    -FilePath $CocosExe `
    -ArgumentList @('--project', $ProjectRoot, '--build', $buildArg) `
    -WorkingDirectory $ProjectRoot `
    -LogPath $EntrypointLogPath `
    -RedirectStandardOutput $StdoutPath `
    -RedirectStandardError $StderrPath `
    -Wait `
    -TimeoutSeconds $TimeoutSeconds `
    -SuccessLogPath @($cocosLogPath) `
    -SuccessPattern @('build Task \(.*\) Finished', 'build task\(.*\) in \d+') `
    -SuccessPollIntervalMilliseconds 1000 `
    -PassThru

$evidenceText = ''
foreach ($path in @($StdoutPath, $StderrPath, $cocosLogPath)) {
    if (Test-Path -LiteralPath $path) {
        $evidenceText += "`n"
        $evidenceText += Get-Content -LiteralPath $path -Raw -ErrorAction SilentlyContinue
    }
}

$finished = ($evidenceText -match 'build Task \(.*\) Finished' -or $evidenceText -match 'build task\(.*\) in \d+')
$androidPostPackage = $null
$webPostProcess = $null
if ($finished -and -not $isAndroidBuild) {
    $webBuildRoot = Join-Path $ProjectRoot (Join-Path 'build' $outputName)
    $faviconSource = Join-Path $ProjectRoot 'assets\favicon.png'
    $faviconDest = Join-Path $webBuildRoot 'favicon.png'
    $indexPath = Join-Path $webBuildRoot 'index.html'
    $webPostProcess = [ordered]@{
        reason = 'prevent-browser-favicon-404-noise-in-web-qa'
        webBuildRoot = $webBuildRoot
        faviconSource = $faviconSource
        faviconDest = $faviconDest
        indexPath = $indexPath
        copiedFavicon = $false
        patchedIndex = $false
        ok = $false
        error = $null
    }

    try {
        if ((Test-Path -LiteralPath $webBuildRoot -PathType Container) -and
            (Test-Path -LiteralPath $faviconSource -PathType Leaf) -and
            (Test-Path -LiteralPath $indexPath -PathType Leaf)) {
            Copy-Item -LiteralPath $faviconSource -Destination $faviconDest -Force
            $webPostProcess.copiedFavicon = $true

            $html = Get-Content -LiteralPath $indexPath -Raw
            if ($html -notmatch '<link\s+rel=["'']icon["'']') {
                $iconLink = '  <link rel="icon" type="image/png" href="favicon.png"/>'
                $html = $html -replace '(<head>\s*)', "`$1$iconLink`r`n"
                Set-Content -LiteralPath $indexPath -Value $html -Encoding UTF8
                $webPostProcess.patchedIndex = $true
            }

            $webPostProcess.ok = (Test-Path -LiteralPath $faviconDest -PathType Leaf)
        } else {
            $webPostProcess.error = 'web-root-favicon-source-or-index-missing'
        }
    } catch {
        $webPostProcess.error = $_.Exception.Message
    }
}
if ($finished -and $isAndroidBuild) {
    $androidBuildRoot = Join-Path $ProjectRoot (Join-Path 'build' $outputName)
    $androidProjRoot = Join-Path $androidBuildRoot 'proj'
    $gradlew = Join-Path $androidProjRoot 'gradlew.bat'
    $apkPath = Join-Path $androidProjRoot 'build\CocosGame\outputs\apk\debug\CocosGame-debug.apk'
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $gradleStdout = Join-Path $ProjectRoot ("logs\gradle-android-postpack-{0}.out.log" -f $stamp)
    $gradleStderr = Join-Path $ProjectRoot ("logs\gradle-android-postpack-{0}.err.log" -f $stamp)
    $gradleRun = $null
    $verification = $null
    $previousJavaHome = $env:JAVA_HOME
    $previousPath = $env:Path

    try {
        if (-not (Test-Path -LiteralPath $gradlew -PathType Leaf)) {
            throw "Android Gradle wrapper not found: $gradlew"
        }

        $javaHome = [string]$configJson.packages.android.javaHome
        $javaPath = [string]$configJson.packages.android.javaPath
        if (-not [string]::IsNullOrWhiteSpace($javaHome) -and (Test-Path -LiteralPath $javaHome -PathType Container)) {
            $env:JAVA_HOME = $javaHome
        }
        if (-not [string]::IsNullOrWhiteSpace($javaPath) -and (Test-Path -LiteralPath $javaPath -PathType Container)) {
            $env:Path = "$javaPath$([System.IO.Path]::PathSeparator)$previousPath"
        }

        $gradleRun = Invoke-MtrEntrypoint `
            -FilePath $gradlew `
            -ArgumentList @('--no-daemon', 'clean', 'assembleDebug') `
            -WorkingDirectory $androidProjRoot `
            -LogPath $EntrypointLogPath `
            -RedirectStandardOutput $gradleStdout `
            -RedirectStandardError $gradleStderr `
            -Wait `
            -TimeoutSeconds $TimeoutSeconds `
            -PassThru

        $verification = Test-MtrAndroidApkPayload -ApkPath $apkPath
        $androidPostPackageOk = ($gradleRun.exitCode -eq 0 -and [bool]$verification.ok)
        $androidPostPackage = [pscustomobject]@{
            tool = 'gradle-clean-assembleDebug'
            reason = 'prevent-stale-mergeDebugAssets-apk-payload'
            projectRoot = $androidProjRoot
            apkPath = $apkPath
            exitCode = $gradleRun.exitCode
            stdout = $gradleStdout
            stderr = $gradleStderr
            verification = $verification
            ok = $androidPostPackageOk
        }
        if (-not $androidPostPackageOk) {
            $finished = $false
        }
    } catch {
        $finished = $false
        $androidPostPackage = [pscustomobject]@{
            tool = 'gradle-clean-assembleDebug'
            reason = 'prevent-stale-mergeDebugAssets-apk-payload'
            projectRoot = $androidProjRoot
            apkPath = $apkPath
            exitCode = if ($gradleRun) { $gradleRun.exitCode } else { $null }
            stdout = $gradleStdout
            stderr = $gradleStderr
            verification = $verification
            ok = $false
            error = $_.Exception.Message
        }
    } finally {
        $env:JAVA_HOME = $previousJavaHome
        $env:Path = $previousPath
    }
}
$reportedExitCode = if ($finished) { 0 } else { $run.logicalExitCode }
$result = [pscustomobject]@{
    configPath = $configArgPath
    configPathResolved = $configResolved
    buildArg = $buildArg
    exitCode = $reportedExitCode
    rawExitCode = $run.exitCode
    buildFinished = $finished
    stdout = $StdoutPath
    stderr = $StderrPath
    cocosLog = $cocosLogPath
    entrypointLog = $EntrypointLogPath
    autocorrections = $run.autocorrections
    completedBySuccessPattern = $run.completedBySuccessPattern
    successMatch = $run.successMatch
    webPostProcess = $webPostProcess
    androidPostPackage = $androidPostPackage
}

$result | ConvertTo-Json -Depth 8
if (-not $finished) {
    if ($run.exitCode -ne 0) {
        exit $run.exitCode
    }
    exit 1
}
