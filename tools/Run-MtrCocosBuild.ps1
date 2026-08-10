param(
    [string]$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path,
    [string]$CocosExe = 'C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe',
    [string]$ConfigPath = 'build-web-mobile.json',
    [string]$ContentIdentityPath = 'assets/resources/config/content_identity.json',
    [string]$AndroidToolchainContractPath = 'tools/codex/android-build-toolchain.contract.json',
    [string]$LogDest = ("creator-web-ui-icons-{0}-{1}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), ([Guid]::NewGuid().ToString('N').Substring(0, 8))),
    [int]$TimeoutSeconds = 900,
    [switch]$ValidateContentIdentityOnly,
    [switch]$ValidateAndroidToolchainOnly,
    [string]$EntrypointLogPath = (Join-Path $ProjectRoot ("logs\entrypoint-router-{0}.jsonl" -f (Get-Date -Format 'yyyyMMdd'))),
    [string]$StdoutPath = (Join-Path $ProjectRoot ("logs\creator-web-ui-icons-wrapper-{0}-{1}.out.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), ([Guid]::NewGuid().ToString('N').Substring(0, 8)))),
    [string]$StderrPath = (Join-Path $ProjectRoot ("logs\creator-web-ui-icons-wrapper-{0}-{1}.err.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), ([Guid]::NewGuid().ToString('N').Substring(0, 8))))
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'codex\MtrEntrypoint.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'codex\MtrAndroidBuildToolchain.psm1') -Force

function Get-MtrContentIdentityRecord {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$ProjectRoot,
        [Parameter(Mandatory=$true)][string]$IdentityPath,
        [Parameter(Mandatory=$true)][ValidateSet('web-mobile', 'android')][string]$TargetPlatform
    )

    $candidate = if ([System.IO.Path]::IsPathRooted($IdentityPath)) {
        $IdentityPath
    } else {
        Join-Path $ProjectRoot $IdentityPath
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Content identity not found: $candidate"
    }

    $resolved = (Resolve-Path -LiteralPath $candidate).Path
    $rootResolved = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    $rootPrefix = $rootResolved + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Content identity escapes project root: $resolved"
    }
    $canonicalIdentity = [System.IO.Path]::GetFullPath((Join-Path $rootResolved 'assets/resources/config/content_identity.json'))
    if (-not $resolved.Equals($canonicalIdentity, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Only the canonical project content identity is accepted: $canonicalIdentity"
    }

    try {
        $identity = Get-Content -LiteralPath $resolved -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "Content identity is not valid JSON: $($_.Exception.Message)"
    }

    $metaResolved = "$resolved.meta"
    if (-not (Test-Path -LiteralPath $metaResolved -PathType Leaf)) {
        throw "Content identity Cocos metadata not found: $metaResolved"
    }
    try {
        $identityMeta = Get-Content -LiteralPath $metaResolved -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "Content identity Cocos metadata is not valid JSON: $($_.Exception.Message)"
    }
    $metaFiles = @($identityMeta.files)
    if ([string]$identityMeta.ver -ne '2.0.1' -or
        [string]$identityMeta.importer -ne 'json' -or
        -not ($identityMeta.imported -is [bool]) -or
        [bool]$identityMeta.imported -ne $true -or
        $metaFiles.Count -ne 1 -or
        [string]$metaFiles[0] -ne '.json' -or
        [string]$identityMeta.uuid -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' -or
        $null -eq $identityMeta.subMetas -or
        $null -eq $identityMeta.userData -or
        @($identityMeta.subMetas.PSObject.Properties).Count -ne 0 -or
        @($identityMeta.userData.PSObject.Properties).Count -ne 0) {
        throw 'Content identity Cocos metadata contract is invalid.'
    }

    $schemaVersionIsInteger = ($identity.schema_version -is [int] -or $identity.schema_version -is [long])
    if (-not $schemaVersionIsInteger -or [long]$identity.schema_version -ne 1 -or [string]$identity.contract -ne 'mtr.content_identity') {
        throw 'Unsupported content identity contract.'
    }
    $sourceCommit = [string]$identity.source.baseline_commit
    $logicalVersion = [string]$identity.logical_content_version
    if ($sourceCommit -notmatch '^[0-9a-f]{40}$') {
        throw 'Content identity baseline commit must be lowercase 40-hex.'
    }
    if ($logicalVersion -ne ("mtr-v3-source-{0}" -f $sourceCommit.Substring(0, 12))) {
        throw 'Logical content version does not match the baseline commit.'
    }
    if ([string]$identity.source.repository -ne 'https://github.com/nikitak8883/Martyskin-trud-runner.git' -or
        [string]$identity.source.branch -ne 'mtr-source-v3' -or
        [string]$identity.source.baseline_kind -ne 'published_source_before_identity_metadata') {
        throw 'Content identity source contract is invalid.'
    }
    if (@($identity.platform_contract.targets) -notcontains $TargetPlatform -or
        [string]$identity.platform_contract.shared_report_field -ne 'contentIdentity' -or
        [string]$identity.platform_contract.artifact_manifest_field -ne 'platformArtifactManifest' -or
        [string]$identity.platform_contract.artifact_manifest_scope -ne 'per-platform') {
        throw "Content identity does not support target platform '$TargetPlatform'."
    }

    $manifestRelative = [string]$identity.freeze_provenance.manifest
    if ($manifestRelative -ne 'docs/global_modernization/v3/M00/source_content_manifest.json') {
        throw 'Content identity freeze manifest path is not canonical.'
    }
    $manifestCandidate = Join-Path $rootResolved ($manifestRelative -replace '/', [System.IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $manifestCandidate -PathType Leaf)) {
        throw "Content identity freeze manifest not found: $manifestCandidate"
    }
    try {
        $manifest = Get-Content -LiteralPath $manifestCandidate -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "Source content manifest is not valid JSON: $($_.Exception.Message)"
    }

    $matchesFreeze = (
        [string]$identity.freeze_provenance.source_commit -eq [string]$manifest.source_commit -and
        [string]$identity.freeze_provenance.source_tree -eq [string]$manifest.source_tree -and
        [string]$identity.freeze_provenance.content_version -eq [string]$manifest.content_version -and
        [string]$identity.freeze_provenance.aggregate_sha256 -eq [string]$manifest.aggregate_sha256 -and
        [long]$identity.freeze_provenance.file_count -eq [long]$manifest.file_count -and
        [long]$identity.freeze_provenance.total_bytes -eq [long]$manifest.total_bytes
    )
    if (-not $matchesFreeze) {
        throw 'Content identity freeze provenance does not match the canonical M00 manifest.'
    }

    $identityRelative = $resolved.Substring($rootPrefix.Length).Replace('\', '/')
    return [pscustomobject][ordered]@{
        contract = [string]$identity.contract
        schemaVersion = [int]$identity.schema_version
        logicalContentVersion = $logicalVersion
        sourceRepository = [string]$identity.source.repository
        sourceBranch = [string]$identity.source.branch
        sourceCommit = $sourceCommit
        sourceBaselineKind = [string]$identity.source.baseline_kind
        freezeContentVersion = [string]$identity.freeze_provenance.content_version
        freezeAggregateSha256 = [string]$identity.freeze_provenance.aggregate_sha256
        identityPath = $identityRelative
        identityFileSha256 = (Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash
        identityMetaFileSha256 = (Get-FileHash -LiteralPath $metaResolved -Algorithm SHA256).Hash
    }
}

function New-MtrPlatformArtifactManifest {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][ValidateSet('web-mobile', 'android')][string]$Platform,
        [Parameter(Mandatory=$true)][string]$OutputName,
        [Parameter(Mandatory=$true)][string]$ProjectRoot
    )

    return [ordered]@{
        contract = 'mtr.platform_artifact_manifest'
        schemaVersion = 1
        scope = 'per-platform'
        platform = $Platform
        outputName = $OutputName
        outputRoot = (Join-Path $ProjectRoot (Join-Path 'build' $OutputName))
        state = 'NOT_BUILT'
    }
}

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
$targetPlatform = [string]$configJson.platform
if ($targetPlatform -notin @('web-mobile', 'android')) {
    throw "Unsupported Cocos target platform: $targetPlatform"
}
if ($ValidateContentIdentityOnly -and $ValidateAndroidToolchainOnly) {
    throw 'Content-identity-only and Android-toolchain-only modes are mutually exclusive.'
}
$outputName = [string]$configJson.outputName
if ([string]::IsNullOrWhiteSpace($outputName)) {
    $outputName = if ($isAndroidBuild) { 'android' } else { '' }
}
$configArgPath = $configResolved
$projectPrefix = $projectRootResolved + [System.IO.Path]::DirectorySeparatorChar
if ($configResolved.StartsWith($projectPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    $configArgPath = $configResolved.Substring($projectPrefix.Length)
}

$androidToolchainPreflight = $null
if ($ValidateAndroidToolchainOnly) {
    if (-not $isAndroidBuild) {
        throw 'Android toolchain preflight requires an Android build config.'
    }
    $androidToolchainPreflight = Assert-MtrAndroidBuildToolchain `
        -ProjectRoot $projectRootResolved `
        -ConfigPath $configArgPath `
        -ContractPath $AndroidToolchainContractPath `
        -CheckGeneratedExport
    $requestedCocosExe = [System.IO.Path]::GetFullPath($CocosExe)
    $approvedCocosExe = [System.IO.Path]::GetFullPath([string]$androidToolchainPreflight.cocosCreator.executable)
    if (-not $requestedCocosExe.Equals($approvedCocosExe, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Android build Cocos executable is not contract-approved: $requestedCocosExe"
    }
    [pscustomobject][ordered]@{
        contract = 'mtr.cocos_android_toolchain_preflight'
        schemaVersion = 1
        status = 'PASS'
        targetPlatform = $targetPlatform
        configPath = $configArgPath.Replace('\', '/')
        androidToolchain = $androidToolchainPreflight
        generatedEvidenceScope = 'EXISTING_EXPORT_IF_PRESENT_NO_BUILD'
        cocosStarted = $false
        gradleStarted = $false
    } | ConvertTo-Json -Depth 12
    exit 0
}

# Content-only validation remains host-independent for cross-platform CI.
# Every real Android build takes the strict host preflight before Cocos starts.
if ($isAndroidBuild -and -not $ValidateContentIdentityOnly) {
    $androidToolchainPreflight = Assert-MtrAndroidBuildToolchain `
        -ProjectRoot $projectRootResolved `
        -ConfigPath $configArgPath `
        -ContractPath $AndroidToolchainContractPath `
        -CheckGeneratedExport
    $requestedCocosExe = [System.IO.Path]::GetFullPath($CocosExe)
    $approvedCocosExe = [System.IO.Path]::GetFullPath([string]$androidToolchainPreflight.cocosCreator.executable)
    if (-not $requestedCocosExe.Equals($approvedCocosExe, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Android build Cocos executable is not contract-approved: $requestedCocosExe"
    }
}

$contentIdentity = Get-MtrContentIdentityRecord `
    -ProjectRoot $projectRootResolved `
    -IdentityPath $ContentIdentityPath `
    -TargetPlatform $targetPlatform
$platformArtifactManifest = New-MtrPlatformArtifactManifest `
    -Platform $targetPlatform `
    -OutputName $outputName `
    -ProjectRoot $projectRootResolved

if ($ValidateContentIdentityOnly) {
    [pscustomobject][ordered]@{
        contract = 'mtr.build_identity_preflight'
        schemaVersion = 1
        status = 'PASS'
        targetPlatform = $targetPlatform
        configPath = $configArgPath.Replace('\', '/')
        contentIdentity = $contentIdentity
        platformArtifactManifest = [pscustomobject]$platformArtifactManifest
    } | ConvertTo-Json -Depth 8
    exit 0
}

$buildArg = "configPath=$configArgPath;logDest=$LogDest"
$cocosLogPath = if ([System.IO.Path]::IsPathRooted($LogDest)) {
    [System.IO.Path]::GetFullPath($LogDest)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $projectRootResolved $LogDest))
}
# Success evidence must belong to this invocation. Unique defaults prevent
# same-second collisions; an explicitly reused path fails before Cocos starts.
foreach ($reservedPath in @($cocosLogPath, $StdoutPath, $StderrPath)) {
    if (Test-Path -LiteralPath $reservedPath) {
        throw "Build run log path already exists; choose a unique path: $reservedPath"
    }
}
$run = $null
$invokeCocos = {
    Invoke-MtrEntrypoint `
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
}
$run = if ($isAndroidBuild) {
    Invoke-MtrAndroidBuildJavaScope -Toolchain $androidToolchainPreflight -ScriptBlock $invokeCocos
} else {
    & $invokeCocos
}

# MtrEntrypoint matches success only in bytes appended after this process starts.
# Never re-scan a pre-existing Cocos log when deciding the current build state.
$finished = ($run.logicalExitCode -eq 0 -and [bool]$run.completedBySuccessPattern)
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
    $androidProjRoot = [string]$androidToolchainPreflight.generatedExport.project
    if ([string]::IsNullOrWhiteSpace($androidProjRoot)) {
        throw 'Android toolchain preflight did not bind a generated project path.'
    }
    $androidBuildRoot = Split-Path -Parent $androidProjRoot
    $gradlew = Join-Path $androidProjRoot 'gradlew.bat'
    $apkPath = Join-Path $androidProjRoot 'build\CocosGame\outputs\apk\debug\CocosGame-debug.apk'
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $gradleStdout = Join-Path $ProjectRoot ("logs\gradle-android-postpack-{0}.out.log" -f $stamp)
    $gradleStderr = Join-Path $ProjectRoot ("logs\gradle-android-postpack-{0}.err.log" -f $stamp)
    $gradleRun = $null
    $verification = $null
    $postExportToolchain = $null

    try {
        if (-not (Test-Path -LiteralPath $gradlew -PathType Leaf)) {
            throw "Android Gradle wrapper not found: $gradlew"
        }

        $postExportToolchain = Assert-MtrAndroidBuildToolchain `
            -ProjectRoot $projectRootResolved `
            -ConfigPath $configArgPath `
            -ContractPath $AndroidToolchainContractPath `
            -CheckGeneratedExport `
            -RequireGeneratedExport
        $validatedPostExportRoot = [string]$postExportToolchain.generatedExport.project
        if (-not [System.IO.Path]::GetFullPath($androidProjRoot).Equals(
            [System.IO.Path]::GetFullPath($validatedPostExportRoot),
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            throw 'Post-export Android project path differs from the pre-Cocos contract binding.'
        }
        $javaHome = [string]$postExportToolchain.androidBuildJava.home
        $invokeGradle = {
            Invoke-MtrEntrypoint `
                -FilePath $gradlew `
                -ArgumentList @('--no-daemon', "-Dorg.gradle.java.home=$javaHome", 'clean', 'assembleDebug') `
                -WorkingDirectory $androidProjRoot `
                -LogPath $EntrypointLogPath `
                -RedirectStandardOutput $gradleStdout `
                -RedirectStandardError $gradleStderr `
                -Wait `
                -TimeoutSeconds $TimeoutSeconds `
                -PassThru
        }
        $gradleRun = Invoke-MtrAndroidBuildJavaScope `
            -Toolchain $postExportToolchain `
            -ScriptBlock $invokeGradle

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
            toolchain = $postExportToolchain
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
            toolchain = $postExportToolchain
            ok = $false
            error = $_.Exception.Message
        }
    }
}
$reportedExitCode = if ($finished) {
    0
} elseif ($run.logicalExitCode -ne 0) {
    $run.logicalExitCode
} else {
    1
}
$platformArtifactManifest['state'] = if ($finished) { 'BUILT' } else { 'FAILED' }
if ($isAndroidBuild) {
    $platformArtifactManifest['androidPostPackage'] = $androidPostPackage
} else {
    $platformArtifactManifest['webPostProcess'] = $webPostProcess
}
$result = [pscustomobject]@{
    contract = 'mtr.cocos_build_report'
    schemaVersion = 1
    targetPlatform = $targetPlatform
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
    contentIdentity = $contentIdentity
    androidToolchain = $androidToolchainPreflight
    platformArtifactManifest = [pscustomobject]$platformArtifactManifest
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
