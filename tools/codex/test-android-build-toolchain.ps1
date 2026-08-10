[CmdletBinding()]
param([string]$ProjectRoot)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$scriptRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptRoot)) {
    $scriptRoot = Split-Path -Parent $PSCommandPath
}
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot '..\..')).Path
}
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
Import-Module (Join-Path $scriptRoot 'MtrAndroidBuildToolchain.psm1') -Force

$passedGroups = 0
function Invoke-MtrToolchainTestGroup {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][scriptblock]$Body
    )
    try {
        & $Body
        $script:passedGroups += 1
    } catch {
        throw "$Name`: $($_.Exception.Message)"
    }
}

function Assert-MtrToolchainTest {
    param(
        [Parameter(Mandatory=$true)][bool]$Condition,
        [Parameter(Mandatory=$true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function New-MtrToolchainTempProject {
    param(
        [Parameter(Mandatory=$true)][string]$Root,
        [Parameter(Mandatory=$true)][scriptblock]$Mutate
    )
    New-Item -ItemType Directory -Path (Join-Path $Root 'tools\codex') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $Root 'native\engine\android\app') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'package.json') -Destination (Join-Path $Root 'package.json')
    Copy-Item `
        -LiteralPath (Join-Path $ProjectRoot 'native\engine\android\app\build.gradle') `
        -Destination (Join-Path $Root 'native\engine\android\app\build.gradle')
    $config = Get-Content -LiteralPath (Join-Path $ProjectRoot 'build-android.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $contract = Get-Content -LiteralPath (Join-Path $ProjectRoot 'tools\codex\android-build-toolchain.contract.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    & $Mutate $config $contract
    $config | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $Root 'build-android.json') -Encoding UTF8
    $contract.build_configs = @('build-android.json', 'build-android-emulator.json')
    $contract | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $Root 'tools\codex\android-build-toolchain.contract.json') -Encoding UTF8
}

function New-MtrToolchainTempGeneratedExport {
    param(
        [Parameter(Mandatory=$true)][string]$Root,
        [string]$CompileSdk = '36'
    )

    $project = Join-Path $Root 'build\android\proj'
    New-Item -ItemType Directory -Path (Join-Path $project 'gradle\wrapper') -Force | Out-Null
    'distributionUrl=https\://services.gradle.org/distributions/gradle-8.11.1-bin.zip' |
        Set-Content -LiteralPath (Join-Path $project 'gradle\wrapper\gradle-wrapper.properties') -Encoding UTF8
    '@echo off' | Set-Content -LiteralPath (Join-Path $project 'gradlew.bat') -Encoding UTF8
    'synthetic-test-wrapper-jar' |
        Set-Content -LiteralPath (Join-Path $project 'gradle\wrapper\gradle-wrapper.jar') -Encoding UTF8
    'buildscript { dependencies { classpath "com.android.tools.build:gradle:8.10.1" } }' |
        Set-Content -LiteralPath (Join-Path $project 'build.gradle') -Encoding UTF8
    @(
        "PROP_COMPILE_SDK_VERSION=$CompileSdk",
        'PROP_TARGET_SDK_VERSION=35',
        'PROP_BUILD_TOOLS_VERSION=36.0.0',
        'PROP_NDK_VERSION=23.2.8568313'
    ) | Set-Content -LiteralPath (Join-Path $project 'gradle.properties') -Encoding UTF8
    $sdkPath = 'C:\Users\nikit\AppData\Local\Android\Sdk'
    $escapedSdkPath = $sdkPath.Replace('\', '\\').Replace(':', '\:')
    "sdk.dir=$escapedSdkPath" | Set-Content -LiteralPath (Join-Path $project 'local.properties') -Encoding UTF8
    $contractPath = Join-Path $Root 'tools\codex\android-build-toolchain.contract.json'
    if (Test-Path -LiteralPath $contractPath -PathType Leaf) {
        $tempContract = Get-Content -LiteralPath $contractPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $tempContract.android.gradlew_bat_sha256 = (Get-FileHash -LiteralPath (Join-Path $project 'gradlew.bat') -Algorithm SHA256).Hash
        $tempContract.android.gradle_wrapper_jar_sha256 = (Get-FileHash -LiteralPath (Join-Path $project 'gradle\wrapper\gradle-wrapper.jar') -Algorithm SHA256).Hash
        $tempContract | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $contractPath -Encoding UTF8
    }
}

function Invoke-MtrToolchainChildProcess {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)

    $powershellExe = (Get-Process -Id $PID).Path
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $powershellExe
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.Arguments = ($Arguments | ForEach-Object { '"{0}"' -f $_.Replace('"', '\"') }) -join ' '
    $process = [System.Diagnostics.Process]::new()
    try {
        $process.StartInfo = $startInfo
        if (-not $process.Start()) { throw 'child-process-start-failed' }
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()
        return [pscustomobject]@{ exitCode = $process.ExitCode; stdout = $stdout; stderr = $stderr }
    } finally {
        $process.Dispose()
    }
}

$initialJavaHome = $env:JAVA_HOME
$initialPath = $env:Path
$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
$tempRoot = Join-Path $tempBase ("mtr-tc01-{0}" -f [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

try {
    $arm = Test-MtrAndroidBuildToolchain `
        -ProjectRoot $ProjectRoot `
        -ConfigPath 'build-android.json' `
        -CheckGeneratedExport
    $emulator = Test-MtrAndroidBuildToolchain `
        -ProjectRoot $ProjectRoot `
        -ConfigPath 'build-android-emulator.json' `
        -CheckGeneratedExport

    Invoke-MtrToolchainTestGroup 'live_arm_config' {
        Assert-MtrToolchainTest ($arm.status -eq 'PASS') "arm status was $($arm.status)"
        Assert-MtrToolchainTest ($arm.androidBuildJava.major -eq 17) 'arm Java major was not 17'
        Assert-MtrToolchainTest ($arm.androidBuildJava.javacMajor -eq 17) 'arm javac major was not 17'
    }
    Invoke-MtrToolchainTestGroup 'live_emulator_config' {
        Assert-MtrToolchainTest ($emulator.status -eq 'PASS') "emulator status was $($emulator.status)"
        Assert-MtrToolchainTest ($emulator.androidBuildJava.major -eq 17) 'emulator Java major was not 17'
    }
    Invoke-MtrToolchainTestGroup 'config_identity_and_optional_generated_history' {
        Assert-MtrToolchainTest ($arm.androidBuildJava.home -eq $emulator.androidBuildJava.home) 'config Java homes differ'
        Assert-MtrToolchainTest ($arm.android.sdkPath -eq $emulator.android.sdkPath) 'config SDK paths differ'
        Assert-MtrToolchainTest ($arm.generatedExport.status -in @('PASS', 'NOT_PRESENT')) 'arm generated evidence was invalid'
        Assert-MtrToolchainTest ($emulator.generatedExport.status -in @('PASS', 'NOT_PRESENT')) 'emulator generated evidence was invalid'
    }

    $cleanCheckoutRoot = Join-Path $tempRoot 'clean-checkout-no-build'
    New-MtrToolchainTempProject -Root $cleanCheckoutRoot -Mutate { param($config, $contract) }
    $cleanCheckout = Test-MtrAndroidBuildToolchain `
        -ProjectRoot $cleanCheckoutRoot `
        -ConfigPath 'build-android.json' `
        -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'clean_checkout_without_generated_export_passes_not_present' {
        Assert-MtrToolchainTest ($cleanCheckout.status -eq 'PASS') 'clean checkout without build/ was blocked'
        Assert-MtrToolchainTest ($cleanCheckout.generatedExport.status -eq 'NOT_PRESENT') 'clean checkout did not report NOT_PRESENT'
    }

    Invoke-MtrToolchainTestGroup 'java_scope_binds_before_child_and_restores_after_success' {
        $observed = Invoke-MtrAndroidBuildJavaScope -Toolchain $arm -ScriptBlock {
            [pscustomobject]@{
                javaHome = $env:JAVA_HOME
                firstPath = @($env:Path -split [regex]::Escape([System.IO.Path]::PathSeparator))[0]
            }
        }
        Assert-MtrToolchainTest ($observed.javaHome -eq $arm.androidBuildJava.home) 'configured JDK was not visible to child scope'
        Assert-MtrToolchainTest ($observed.firstPath -eq $arm.androidBuildJava.bin) 'configured JDK bin was not first in child PATH'
        Assert-MtrToolchainTest ($env:JAVA_HOME -eq $initialJavaHome) 'JAVA_HOME was not restored after success'
        Assert-MtrToolchainTest ($env:Path -eq $initialPath) 'PATH was not restored after success'
    }

    Invoke-MtrToolchainTestGroup 'java_scope_restores_after_child_throw' {
        $threw = $false
        try {
            Invoke-MtrAndroidBuildJavaScope -Toolchain $arm -ScriptBlock { throw 'expected-child-failure' }
        } catch {
            $threw = $_.Exception.Message -match 'expected-child-failure'
        }
        Assert-MtrToolchainTest $threw 'child exception did not propagate'
        Assert-MtrToolchainTest ($env:JAVA_HOME -eq $initialJavaHome) 'JAVA_HOME was not restored after throw'
        Assert-MtrToolchainTest ($env:Path -eq $initialPath) 'PATH was not restored after throw'
    }
    Invoke-MtrToolchainTestGroup 'ambient_is_reported_never_selected' {
        Assert-MtrToolchainTest (-not $arm.ambientFallbackAllowed) 'ambient fallback was allowed'
        Assert-MtrToolchainTest (-not $arm.ambientJava.selectedForBuild) 'ambient Java was selected'
        Assert-MtrToolchainTest ($arm.androidBuildJava.resolution -eq 'config-approved') 'build Java was not config-approved'
    }
    Invoke-MtrToolchainTestGroup 'version_parser' {
        Assert-MtrToolchainTest ((Get-MtrAndroidToolchainJavaMajor 'openjdk version "17.0.20"') -eq 17) 'openjdk parser failed'
        Assert-MtrToolchainTest ((Get-MtrAndroidToolchainJavaMajor 'javac 17.0.20') -eq 17) 'javac parser failed'
        Assert-MtrToolchainTest ($null -eq (Get-MtrAndroidToolchainJavaMajor 'not-a-java-version')) 'invalid version parsed'
    }

    $missingRoot = Join-Path $tempRoot 'missing-jdk'
    New-MtrToolchainTempProject -Root $missingRoot -Mutate {
        param($config, $contract)
        $missingHome = 'C:\mtr-tc01-missing-jdk-17'
        $config.packages.android.javaHome = $missingHome
        $config.packages.android.javaPath = Join-Path $missingHome 'bin'
        $contract.java.approved_home = $missingHome
    }
    $missing = Test-MtrAndroidBuildToolchain -ProjectRoot $missingRoot -ConfigPath 'build-android.json'
    Invoke-MtrToolchainTestGroup 'missing_configured_jdk_never_falls_back' {
        Assert-MtrToolchainTest ($missing.status -eq 'BLOCKED') 'missing configured JDK passed'
        Assert-MtrToolchainTest (@($missing.blockers | Where-Object { $_ -like 'configured-jdk-file-missing:*' }).Count -gt 0) 'missing JDK blocker absent'
        Assert-MtrToolchainTest (-not $missing.ambientJava.selectedForBuild) 'ambient Java selected for missing JDK'
    }

    $mismatchRoot = Join-Path $tempRoot 'java-path-mismatch'
    New-MtrToolchainTempProject -Root $mismatchRoot -Mutate {
        param($config, $contract)
        $config.packages.android.javaPath = 'C:\unexpected-java-bin'
    }
    $mismatch = Test-MtrAndroidBuildToolchain -ProjectRoot $mismatchRoot -ConfigPath 'build-android.json'
    Invoke-MtrToolchainTestGroup 'java_path_mismatch_fails' {
        Assert-MtrToolchainTest ($mismatch.status -eq 'BLOCKED') 'javaPath mismatch passed'
        Assert-MtrToolchainTest (@($mismatch.blockers) -contains 'configured-java-path-mismatch') 'javaPath blocker absent'
    }

    $java21Root = Join-Path $tempRoot 'configured-java-21'
    New-MtrToolchainTempProject -Root $java21Root -Mutate {
        param($config, $contract)
        $java21 = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.12.8-hotspot'
        $config.packages.android.javaHome = $java21
        $config.packages.android.javaPath = Join-Path $java21 'bin'
    }
    $java21 = Test-MtrAndroidBuildToolchain -ProjectRoot $java21Root -ConfigPath 'build-android.json'
    Invoke-MtrToolchainTestGroup 'configured_java_21_cannot_replace_approved_patch' {
        Assert-MtrToolchainTest ($java21.status -eq 'BLOCKED') 'configured Java 21 passed'
        Assert-MtrToolchainTest (@($java21.blockers) -contains 'configured-java-home-not-approved') 'unapproved Java home blocker absent'
    }

    $redefinedPolicyRoot = Join-Path $tempRoot 'contract-redefined-to-java-21'
    New-MtrToolchainTempProject -Root $redefinedPolicyRoot -Mutate {
        param($config, $contract)
        $java21Home = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.12.8-hotspot'
        $config.packages.android.javaHome = $java21Home
        $config.packages.android.javaPath = Join-Path $java21Home 'bin'
        $contract.java.required_major = 21
        $contract.java.required_version = '21.0.12'
        $contract.java.required_vendor = 'Eclipse Adoptium'
        $contract.java.required_arch = 'x86_64'
        $contract.java.approved_home = $java21Home
        $jdk21Hashes = @{
            'bin\java.exe' = 'A38D821EFB69EF99C55D315B00D9E8B88F126743B8773E44154E1A3D193EFD41'
            'bin\javac.exe' = '4F3A8103193E1AC3E9268B9BB998CC672B7346F6E67E3B8A95109D4D494755AD'
            'bin\jar.exe' = '9CA50D7360F851966DA1640449FDA584FD6886F1E8BCCBDB792DEBCDE006097D'
            'release' = '0838EC7ABAB7D1B89D425E36735DBB696889E05968C1DBAE18EAE631972F443E'
        }
        foreach ($relativeFile in @($contract.java.required_files)) {
            $contract.java.required_file_sha256.$relativeFile = $jdk21Hashes[$relativeFile]
        }
    }
    $redefinedPolicy = Test-MtrAndroidBuildToolchain -ProjectRoot $redefinedPolicyRoot -ConfigPath 'build-android.json'
    Invoke-MtrToolchainTestGroup 'contract_cannot_redefine_approved_jdk' {
        Assert-MtrToolchainTest ($redefinedPolicy.status -eq 'BLOCKED') 'self-consistent JDK21 contract redefinition passed'
        Assert-MtrToolchainTest (@($redefinedPolicy.blockers) -contains 'contract-java-policy-not-approved') 'runtime JDK policy pin blocker absent'
        Assert-MtrToolchainTest (-not $redefinedPolicy.androidBuildJava.selectedForBuild) 'redefined JDK21 was selected for build'
    }

    $versionRoot = Join-Path $tempRoot 'jdk-version-mismatch'
    New-MtrToolchainTempProject -Root $versionRoot -Mutate {
        param($config, $contract)
        $contract.java.required_version = '17.0.19'
    }
    $versionMismatch = Test-MtrAndroidBuildToolchain -ProjectRoot $versionRoot -ConfigPath 'build-android.json'
    Invoke-MtrToolchainTestGroup 'exact_jdk_version_mismatch_fails' {
        Assert-MtrToolchainTest ($versionMismatch.status -eq 'BLOCKED') 'wrong exact JDK version passed'
        Assert-MtrToolchainTest (@($versionMismatch.blockers) -contains 'contract-java-policy-not-approved') 'exact JDK policy pin blocker absent'
    }

    $previousToolOptions = [Environment]::GetEnvironmentVariable('JAVA_TOOL_OPTIONS', 'Process')
    try {
        [Environment]::SetEnvironmentVariable('JAVA_TOOL_OPTIONS', '-Dmtr.tc01.test=true', 'Process')
        $override = Test-MtrAndroidBuildToolchain -ProjectRoot $ProjectRoot -ConfigPath 'build-android.json'
    } finally {
        [Environment]::SetEnvironmentVariable('JAVA_TOOL_OPTIONS', $previousToolOptions, 'Process')
    }
    Invoke-MtrToolchainTestGroup 'hidden_environment_override_fails' {
        Assert-MtrToolchainTest ($override.status -eq 'BLOCKED') 'JAVA_TOOL_OPTIONS override passed'
        Assert-MtrToolchainTest (@($override.blockers) -contains 'environment-override-active:JAVA_TOOL_OPTIONS') 'override blocker absent'
    }

    $previousJavaOpts = [Environment]::GetEnvironmentVariable('JAVA_OPTS', 'Process')
    try {
        [Environment]::SetEnvironmentVariable('JAVA_OPTS', '-Dorg.gradle.java.home=C:\unapproved-jdk', 'Process')
        $javaOptsOverride = Test-MtrAndroidBuildToolchain -ProjectRoot $ProjectRoot -ConfigPath 'build-android.json'
    } finally {
        [Environment]::SetEnvironmentVariable('JAVA_OPTS', $previousJavaOpts, 'Process')
    }
    Invoke-MtrToolchainTestGroup 'java_opts_override_fails' {
        Assert-MtrToolchainTest ($javaOptsOverride.status -eq 'BLOCKED') 'JAVA_OPTS override passed'
        Assert-MtrToolchainTest (@($javaOptsOverride.blockers) -contains 'environment-override-active:JAVA_OPTS') 'JAVA_OPTS blocker absent'
    }

    $previousGradleUserHome = [Environment]::GetEnvironmentVariable('GRADLE_USER_HOME', 'Process')
    try {
        [Environment]::SetEnvironmentVariable('GRADLE_USER_HOME', (Join-Path $tempRoot 'alternate-gradle-home'), 'Process')
        $gradleUserHomeOverride = Test-MtrAndroidBuildToolchain -ProjectRoot $ProjectRoot -ConfigPath 'build-android.json'
    } finally {
        [Environment]::SetEnvironmentVariable('GRADLE_USER_HOME', $previousGradleUserHome, 'Process')
    }
    Invoke-MtrToolchainTestGroup 'gradle_user_home_override_fails' {
        Assert-MtrToolchainTest ($gradleUserHomeOverride.status -eq 'BLOCKED') 'GRADLE_USER_HOME override passed'
        Assert-MtrToolchainTest (@($gradleUserHomeOverride.blockers) -contains 'environment-override-active:GRADLE_USER_HOME') 'GRADLE_USER_HOME blocker absent'
    }

    $previousWhitespaceGradleUserHome = [Environment]::GetEnvironmentVariable('GRADLE_USER_HOME', 'Process')
    try {
        [Environment]::SetEnvironmentVariable('GRADLE_USER_HOME', '   ', 'Process')
        $whitespaceGradleUserHome = Test-MtrAndroidBuildToolchain -ProjectRoot $ProjectRoot -ConfigPath 'build-android.json'
    } finally {
        [Environment]::SetEnvironmentVariable('GRADLE_USER_HOME', $previousWhitespaceGradleUserHome, 'Process')
    }
    Invoke-MtrToolchainTestGroup 'whitespace_gradle_user_home_override_fails' {
        Assert-MtrToolchainTest ($whitespaceGradleUserHome.status -eq 'BLOCKED') 'whitespace GRADLE_USER_HOME override passed'
        Assert-MtrToolchainTest (@($whitespaceGradleUserHome.blockers) -contains 'environment-override-active:GRADLE_USER_HOME') 'whitespace GRADLE_USER_HOME blocker absent'
    }

    $fakeProfile = Join-Path $tempRoot 'caller-controlled-userprofile'
    New-Item -ItemType Directory -Path (Join-Path $fakeProfile '.gradle') -Force | Out-Null
    'org.gradle.java.home=C\:\unapproved-jdk' |
        Set-Content -LiteralPath (Join-Path $fakeProfile '.gradle\gradle.properties') -Encoding UTF8
    $previousUserProfile = [Environment]::GetEnvironmentVariable('USERPROFILE', 'Process')
    try {
        [Environment]::SetEnvironmentVariable('USERPROFILE', $fakeProfile, 'Process')
        $profileIdentity = Test-MtrAndroidBuildToolchain -ProjectRoot $ProjectRoot -ConfigPath 'build-android.json'
    } finally {
        [Environment]::SetEnvironmentVariable('USERPROFILE', $previousUserProfile, 'Process')
    }
    $expectedGradleProperties = Join-Path `
        ([Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)) `
        '.gradle\gradle.properties'
    Invoke-MtrToolchainTestGroup 'userprofile_override_fails_and_authoritative_gradle_home_remains_bound' {
        Assert-MtrToolchainTest ($profileIdentity.status -eq 'BLOCKED') 'caller USERPROFILE override passed'
        Assert-MtrToolchainTest (@($profileIdentity.blockers) -contains 'userprofile-environment-mismatch') 'caller USERPROFILE mismatch blocker absent'
        Assert-MtrToolchainTest (@($profileIdentity.gradlePropertiesChecked) -contains $expectedGradleProperties) 'authoritative Gradle user properties path was not checked'
        Assert-MtrToolchainTest (-not (@($profileIdentity.gradlePropertiesChecked) -contains (Join-Path $fakeProfile '.gradle\gradle.properties'))) 'caller USERPROFILE path was trusted'
    }

    $outputRoot = Join-Path $tempRoot 'output-name-mismatch'
    New-MtrToolchainTempProject -Root $outputRoot -Mutate {
        param($config, $contract)
        $config.outputName = 'android-unvalidated'
    }
    $outputMismatch = Test-MtrAndroidBuildToolchain -ProjectRoot $outputRoot -ConfigPath 'build-android.json'
    Invoke-MtrToolchainTestGroup 'config_output_name_is_bound_to_generated_project' {
        Assert-MtrToolchainTest ($outputMismatch.status -eq 'BLOCKED') 'unapproved outputName passed'
        Assert-MtrToolchainTest (@($outputMismatch.blockers) -contains 'config-output-name-not-approved') 'outputName blocker absent'
    }

    $escapeRoot = Join-Path $tempRoot 'generated-project-escape'
    New-MtrToolchainTempProject -Root $escapeRoot -Mutate {
        param($config, $contract)
        $contract.generated_exports[0].project = '../outside-project'
    }
    $escapedProject = Test-MtrAndroidBuildToolchain -ProjectRoot $escapeRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'generated_project_cannot_escape_project_root' {
        Assert-MtrToolchainTest ($escapedProject.status -eq 'BLOCKED') 'escaping generated project passed'
        Assert-MtrToolchainTest (@($escapedProject.blockers) -contains 'generated-export-project-escapes-root') 'project escape blocker absent'
    }

    $reparseRoot = Join-Path $tempRoot 'generated-project-reparse'
    $reparseTargetRoot = Join-Path $tempRoot 'generated-project-reparse-target'
    New-MtrToolchainTempProject -Root $reparseRoot -Mutate { param($config, $contract) }
    New-MtrToolchainTempGeneratedExport -Root $reparseTargetRoot
    New-Item -ItemType Directory -Path (Join-Path $reparseRoot 'build\android') -Force | Out-Null
    New-Item `
        -ItemType Junction `
        -Path (Join-Path $reparseRoot 'build\android\proj') `
        -Target (Join-Path $reparseTargetRoot 'build\android\proj') | Out-Null
    $reparseProject = Test-MtrAndroidBuildToolchain -ProjectRoot $reparseRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'generated_project_reparse_point_fails' {
        Assert-MtrToolchainTest ($reparseProject.status -eq 'BLOCKED') 'generated project reparse point passed'
        Assert-MtrToolchainTest (@($reparseProject.blockers) -contains 'generated-export-reparse-point-not-allowed') 'reparse-point blocker absent'
    }

    $generatedMismatchRoot = Join-Path $tempRoot 'generated-compile-sdk-mismatch'
    New-MtrToolchainTempProject -Root $generatedMismatchRoot -Mutate { param($config, $contract) }
    New-MtrToolchainTempGeneratedExport -Root $generatedMismatchRoot -CompileSdk '35'
    $generatedMismatch = Test-MtrAndroidBuildToolchain -ProjectRoot $generatedMismatchRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'generated_compile_sdk_mismatch_fails' {
        Assert-MtrToolchainTest ($generatedMismatch.status -eq 'BLOCKED') 'generated compile SDK mismatch passed'
        Assert-MtrToolchainTest (@($generatedMismatch.blockers) -contains 'generated-compile-sdk-mismatch') 'generated compile SDK blocker absent'
    }

    $duplicatePropertyRoot = Join-Path $tempRoot 'duplicate-generated-property'
    New-MtrToolchainTempProject -Root $duplicatePropertyRoot -Mutate { param($config, $contract) }
    New-MtrToolchainTempGeneratedExport -Root $duplicatePropertyRoot
    Add-Content -LiteralPath (Join-Path $duplicatePropertyRoot 'build\android\proj\gradle.properties') `
        -Value 'PROP_COMPILE_SDK_VERSION=35' `
        -Encoding UTF8
    $duplicateProperty = Test-MtrAndroidBuildToolchain -ProjectRoot $duplicatePropertyRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'duplicate_generated_property_assignment_fails' {
        Assert-MtrToolchainTest ($duplicateProperty.status -eq 'BLOCKED') 'duplicate generated property passed'
        Assert-MtrToolchainTest (@($duplicateProperty.blockers) -contains 'generated-property-assignment-count:PROP_COMPILE_SDK_VERSION') 'duplicate property blocker absent'
    }

    $colonOverrideRoot = Join-Path $tempRoot 'colon-generated-overrides'
    New-MtrToolchainTempProject -Root $colonOverrideRoot -Mutate { param($config, $contract) }
    New-MtrToolchainTempGeneratedExport -Root $colonOverrideRoot
    Add-Content -LiteralPath (Join-Path $colonOverrideRoot 'build\android\proj\gradle.properties') `
        -Value @('PROP_TARGET_SDK_VERSION:34', 'org.gradle.java.home:C\:\\unapproved-jdk', "PROP_NDK_VERSION`f0.0") `
        -Encoding UTF8
    $colonOverride = Test-MtrAndroidBuildToolchain -ProjectRoot $colonOverrideRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'colon_delimited_generated_overrides_fail' {
        Assert-MtrToolchainTest ($colonOverride.status -eq 'BLOCKED') 'colon-delimited generated overrides passed'
        Assert-MtrToolchainTest (@($colonOverride.blockers) -contains 'generated-property-assignment-count:PROP_TARGET_SDK_VERSION') 'colon property blocker absent'
        Assert-MtrToolchainTest (@($colonOverride.blockers) -contains 'generated-property-assignment-count:PROP_NDK_VERSION') 'form-feed property blocker absent'
        Assert-MtrToolchainTest (@($colonOverride.blockers) -contains 'generated-gradle-java-home-override-active') 'colon java home blocker absent'
    }

    $escapedKeyRoot = Join-Path $tempRoot 'escaped-and-bare-generated-keys'
    New-MtrToolchainTempProject -Root $escapedKeyRoot -Mutate { param($config, $contract) }
    New-MtrToolchainTempGeneratedExport -Root $escapedKeyRoot
    Add-Content -LiteralPath (Join-Path $escapedKeyRoot 'build\android\proj\gradle.properties') `
        -Value @('PROP_BUILD_TOOLS_VERSION', 'PROP_COMPILE_SDK\_VERSION=35') `
        -Encoding UTF8
    $escapedKeys = Test-MtrAndroidBuildToolchain -ProjectRoot $escapedKeyRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'bare_and_escaped_generated_property_keys_fail' {
        Assert-MtrToolchainTest ($escapedKeys.status -eq 'BLOCKED') 'bare or escaped generated key passed'
        Assert-MtrToolchainTest (@($escapedKeys.blockers) -contains 'generated-property-assignment-count:PROP_BUILD_TOOLS_VERSION') 'bare property blocker absent'
        Assert-MtrToolchainTest (@($escapedKeys.blockers) -contains 'generated-gradle-escaped-key-not-allowed') 'escaped property key blocker absent'
    }

    $continuationRoot = Join-Path $tempRoot 'root-gradle-continuation'
    New-MtrToolchainTempProject -Root $continuationRoot -Mutate { param($config, $contract) }
    @('org.gradle.java.\', '  home=C\:\\unapproved-jdk') |
        Set-Content -LiteralPath (Join-Path $continuationRoot 'gradle.properties') -Encoding UTF8
    $continuationOverride = Test-MtrAndroidBuildToolchain -ProjectRoot $continuationRoot -ConfigPath 'build-android.json'
    Invoke-MtrToolchainTestGroup 'root_gradle_property_continuation_fails' {
        Assert-MtrToolchainTest ($continuationOverride.status -eq 'BLOCKED') 'continued root Gradle override passed'
        Assert-MtrToolchainTest (@($continuationOverride.blockers) -contains 'gradle-property-continuation-not-allowed') 'Gradle continuation blocker absent'
    }

    $loneCrRoot = Join-Path $tempRoot 'lone-cr-generated-overrides'
    New-MtrToolchainTempProject -Root $loneCrRoot -Mutate { param($config, $contract) }
    New-MtrToolchainTempGeneratedExport -Root $loneCrRoot
    $loneCrProperties = Join-Path $loneCrRoot 'build\android\proj\gradle.properties'
    [System.IO.File]::AppendAllText(
        $loneCrProperties,
        "# hidden after CR`rorg.gradle.java.home:C\:\\unapproved-jdk`rPROP_COMPILE_SDK_VERSION:35"
    )
    $loneCrOverride = Test-MtrAndroidBuildToolchain -ProjectRoot $loneCrRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'lone_cr_generated_overrides_fail' {
        Assert-MtrToolchainTest ($loneCrOverride.status -eq 'BLOCKED') 'lone-CR generated overrides passed'
        Assert-MtrToolchainTest (@($loneCrOverride.blockers) -contains 'generated-gradle-java-home-override-active') 'lone-CR java home blocker absent'
        Assert-MtrToolchainTest (@($loneCrOverride.blockers) -contains 'generated-property-assignment-count:PROP_COMPILE_SDK_VERSION') 'lone-CR duplicate blocker absent'
    }

    $partialRoot = Join-Path $tempRoot 'partial-generated-export'
    New-MtrToolchainTempProject -Root $partialRoot -Mutate { param($config, $contract) }
    New-Item -ItemType Directory -Path (Join-Path $partialRoot 'build\android\proj') -Force | Out-Null
    $partialExport = Test-MtrAndroidBuildToolchain -ProjectRoot $partialRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'partial_existing_generated_export_fails_before_cocos' {
        Assert-MtrToolchainTest ($partialExport.status -eq 'BLOCKED') 'partial generated export passed'
        Assert-MtrToolchainTest (@($partialExport.blockers) -contains 'generated-export-incomplete') 'partial generated export blocker absent'
    }

    $daemonCriteriaRoot = Join-Path $tempRoot 'generated-daemon-jvm-criteria'
    New-MtrToolchainTempProject -Root $daemonCriteriaRoot -Mutate { param($config, $contract) }
    New-MtrToolchainTempGeneratedExport -Root $daemonCriteriaRoot
    'toolchainVersion=21' |
        Set-Content -LiteralPath (Join-Path $daemonCriteriaRoot 'build\android\proj\gradle\gradle-daemon-jvm.properties') -Encoding UTF8
    $daemonCriteria = Test-MtrAndroidBuildToolchain -ProjectRoot $daemonCriteriaRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'generated_daemon_jvm_criteria_fails' {
        Assert-MtrToolchainTest ($daemonCriteria.status -eq 'BLOCKED') 'generated daemon JVM criteria passed'
        Assert-MtrToolchainTest (@($daemonCriteria.blockers) -contains 'generated-gradle-daemon-jvm-criteria-not-allowed') 'daemon JVM criteria blocker absent'
    }

    $launcherHashRoot = Join-Path $tempRoot 'generated-launcher-hash-mismatch'
    New-MtrToolchainTempProject -Root $launcherHashRoot -Mutate { param($config, $contract) }
    New-MtrToolchainTempGeneratedExport -Root $launcherHashRoot
    'set JAVA_HOME=C:\unapproved-jdk' |
        Add-Content -LiteralPath (Join-Path $launcherHashRoot 'build\android\proj\gradlew.bat') -Encoding UTF8
    $launcherHash = Test-MtrAndroidBuildToolchain -ProjectRoot $launcherHashRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'generated_gradlew_launcher_hash_mismatch_fails' {
        Assert-MtrToolchainTest ($launcherHash.status -eq 'BLOCKED') 'modified gradlew.bat passed'
        Assert-MtrToolchainTest (@($launcherHash.blockers) -contains 'generated-gradlew-bat-hash-mismatch') 'gradlew.bat hash blocker absent'
    }

    $distributionUrlRoot = Join-Path $tempRoot 'generated-distribution-url-mismatch'
    New-MtrToolchainTempProject -Root $distributionUrlRoot -Mutate { param($config, $contract) }
    New-MtrToolchainTempGeneratedExport -Root $distributionUrlRoot
    'distributionUrl=https\://example.invalid/gradle-8.11.1-bin.zip' |
        Set-Content -LiteralPath (Join-Path $distributionUrlRoot 'build\android\proj\gradle\wrapper\gradle-wrapper.properties') -Encoding UTF8
    $distributionUrl = Test-MtrAndroidBuildToolchain -ProjectRoot $distributionUrlRoot -ConfigPath 'build-android.json' -CheckGeneratedExport
    Invoke-MtrToolchainTestGroup 'generated_distribution_url_must_match_exact_contract' {
        Assert-MtrToolchainTest ($distributionUrl.status -eq 'BLOCKED') 'alternate Gradle distribution URL passed'
        Assert-MtrToolchainTest (@($distributionUrl.blockers) -contains 'generated-gradle-distribution-url-mismatch') 'distribution URL blocker absent'
    }

    $hashRoot = Join-Path $tempRoot 'jdk-hash-mismatch'
    New-MtrToolchainTempProject -Root $hashRoot -Mutate {
        param($config, $contract)
        $contract.java.required_file_sha256.'bin\java.exe' = ('0' * 64)
    }
    $hashMismatch = Test-MtrAndroidBuildToolchain -ProjectRoot $hashRoot -ConfigPath 'build-android.json'
    Invoke-MtrToolchainTestGroup 'exact_jdk_file_hash_mismatch_fails' {
        Assert-MtrToolchainTest ($hashMismatch.status -eq 'BLOCKED') 'wrong JDK hash passed'
        Assert-MtrToolchainTest (@($hashMismatch.blockers) -contains 'configured-jdk-file-hash-mismatch:bin/java.exe') 'JDK hash blocker absent'
    }

    $wrongCocos = Invoke-MtrToolchainChildProcess -Arguments @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
        (Join-Path $ProjectRoot 'tools\Run-MtrCocosBuild.ps1'),
        '-ProjectRoot', $ProjectRoot,
        '-ConfigPath', 'build-android.json',
        '-ValidateAndroidToolchainOnly',
        '-CocosExe', 'C:\does-not-exist\CocosCreator.exe'
    )
    Invoke-MtrToolchainTestGroup 'preflight_only_rejects_unapproved_cocos_override' {
        Assert-MtrToolchainTest ($wrongCocos.exitCode -ne 0) 'unapproved Cocos override returned exit 0'
    }

    $wrapperSource = Get-Content -LiteralPath (Join-Path $ProjectRoot 'tools\Run-MtrCocosBuild.ps1') -Raw -Encoding UTF8
    Invoke-MtrToolchainTestGroup 'wrapper_log_paths_are_unique_and_reuse_fails_closed' {
        Assert-MtrToolchainTest ($wrapperSource -match '\[Guid\]::NewGuid\(\)') 'wrapper defaults do not contain per-run GUIDs'
        Assert-MtrToolchainTest ($wrapperSource -match 'Build run log path already exists; choose a unique path') 'wrapper does not reject reused run log paths'
    }

    Invoke-MtrToolchainTestGroup 'caller_environment_is_unchanged' {
        Assert-MtrToolchainTest ($env:JAVA_HOME -eq $initialJavaHome) 'JAVA_HOME changed'
        Assert-MtrToolchainTest ($env:Path -eq $initialPath) 'PATH changed'
    }
} finally {
    $resolvedTemp = [System.IO.Path]::GetFullPath($tempRoot)
    $tempPrefix = $tempBase + [System.IO.Path]::DirectorySeparatorChar
    if ($resolvedTemp.StartsWith($tempPrefix, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Test-Path -LiteralPath $resolvedTemp -PathType Container)) {
        Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
    }
    $env:JAVA_HOME = $initialJavaHome
    $env:Path = $initialPath
}

[Console]::Out.WriteLine(([pscustomobject][ordered]@{
        status = 'PASS'
        testGroups = $passedGroups
        buildJavaMajor = $arm.androidBuildJava.major
        ambientJavaMajor = $arm.ambientJava.major
        configuredJavaOnly = $true
        exactJdkPatchAndHashes = $true
        generatedExportEvidence = if (
            $arm.generatedExport.status -eq 'PASS' -and
            $emulator.generatedExport.status -eq 'PASS'
        ) { 'HISTORICAL_EXISTING_EXPORT' } else { 'NOT_PRESENT_ALLOWED' }
        cocosStarted = $false
        gradleStarted = $false
        adbStarted = $false
        emulatorStarted = $false
    } | ConvertTo-Json -Compress))
