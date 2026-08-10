Set-StrictMode -Version Latest

function Get-MtrAndroidToolchainProperty {
    [CmdletBinding()]
    param(
        [AllowNull()]$Object,
        [Parameter(Mandatory=$true)][string]$Name
    )

    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-MtrAndroidToolchainFullPath {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)

    return [System.IO.Path]::GetFullPath(
        [Environment]::ExpandEnvironmentVariables($Path)
    ).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
}

function Resolve-MtrAndroidToolchainProjectPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$ProjectRoot,
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Label
    )

    if ([string]::IsNullOrWhiteSpace($Path)) { throw "$Label is empty." }
    $root = Get-MtrAndroidToolchainFullPath -Path $ProjectRoot
    $candidate = if ([System.IO.Path]::IsPathRooted($Path)) {
        Get-MtrAndroidToolchainFullPath -Path $Path
    } else {
        Get-MtrAndroidToolchainFullPath -Path (Join-Path $root $Path)
    }
    $rootPrefix = $root + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.Equals($root, [System.StringComparison]::OrdinalIgnoreCase) -and
        -not $candidate.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes project root: $candidate"
    }
    return $candidate
}

function Test-MtrAndroidToolchainExactProperties {
    [CmdletBinding()]
    param(
        [AllowNull()]$Object,
        [Parameter(Mandatory=$true)][string[]]$Names
    )

    if ($null -eq $Object) { return $false }
    $actual = @($Object.PSObject.Properties.Name)
    if ($actual.Count -ne $Names.Count) { return $false }
    foreach ($name in $Names) {
        if ($actual -notcontains $name) { return $false }
    }
    return $true
}

function Test-MtrAndroidToolchainNoReparsePoints {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$ProjectRoot,
        [Parameter(Mandatory=$true)][string]$CandidatePath
    )

    $root = Get-MtrAndroidToolchainFullPath -Path $ProjectRoot
    $candidate = Get-MtrAndroidToolchainFullPath -Path $CandidatePath
    $rootPrefix = $root + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.Equals($root, [System.StringComparison]::OrdinalIgnoreCase) -and
        -not $candidate.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $false
    }
    $current = $root
    $relative = $candidate.Substring($root.Length).TrimStart('\', '/')
    foreach ($segment in @($relative -split '[\\/]' | Where-Object { $_ })) {
        $current = Join-Path $current $segment
        if (-not (Test-Path -LiteralPath $current)) { continue }
        $item = Get-Item -LiteralPath $current -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            return $false
        }
    }
    return $true
}

function Test-MtrAndroidToolchainPathEqual {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][AllowEmptyString()][string]$Left,
        [Parameter(Mandatory=$true)][AllowEmptyString()][string]$Right
    )

    if ([string]::IsNullOrWhiteSpace($Left) -or [string]::IsNullOrWhiteSpace($Right)) {
        return $false
    }
    try {
        return (Get-MtrAndroidToolchainFullPath -Path $Left).Equals(
            (Get-MtrAndroidToolchainFullPath -Path $Right),
            [System.StringComparison]::OrdinalIgnoreCase
        )
    } catch {
        return $false
    }
}

function Get-MtrAndroidToolchainAuthoritativeUserProfile {
    [CmdletBinding()]
    param()

    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'The Android build toolchain profile binding requires Windows.'
    }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ($null -eq $identity.User) { throw 'Current Windows SID is unavailable.' }
    $profileKey = "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\$($identity.User.Value)"
    $profile = [string](Get-ItemProperty -LiteralPath $profileKey -Name ProfileImagePath -ErrorAction Stop).ProfileImagePath
    if ([string]::IsNullOrWhiteSpace($profile)) { throw 'Current Windows profile path is unavailable.' }
    return Get-MtrAndroidToolchainFullPath -Path $profile
}

function Resolve-MtrAndroidToolchainProjectFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$ProjectRoot,
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Label
    )

    $candidate = Resolve-MtrAndroidToolchainProjectPath `
        -ProjectRoot $ProjectRoot `
        -Path $Path `
        -Label $Label
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "$Label not found: $candidate"
    }
    return $candidate
}

function Read-MtrAndroidToolchainJson {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$ProjectRoot,
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Label
    )

    $resolved = Resolve-MtrAndroidToolchainProjectFile `
        -ProjectRoot $ProjectRoot `
        -Path $Path `
        -Label $Label
    try {
        $value = Get-Content -LiteralPath $resolved -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "$Label is not valid JSON: $($_.Exception.Message)"
    }
    return [pscustomobject]@{
        path = $resolved
        value = $value
    }
}

function Invoke-MtrAndroidToolchainVersionProbe {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string]$Arguments = '-version',
        [int]$TimeoutMilliseconds = 15000
    )

    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
        return [pscustomobject]@{
            found = $false
            path = $FilePath
            exitCode = $null
            timedOut = $false
            stdout = ''
            stderr = ''
            error = 'executable-not-found'
        }
    }

    $process = $null
    try {
        $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $FilePath
        $startInfo.Arguments = $Arguments
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $startInfo
        if (-not $process.Start()) {
            throw 'process-start-returned-false'
        }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutMilliseconds)) {
            try { $process.Kill() } catch { }
            return [pscustomobject]@{
                found = $true
                path = $FilePath
                exitCode = $null
                timedOut = $true
                stdout = ''
                stderr = ''
                error = 'probe-timeout'
            }
        }
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        return [pscustomobject]@{
            found = $true
            path = $FilePath
            exitCode = $process.ExitCode
            timedOut = $false
            stdout = $stdout
            stderr = $stderr
            error = $null
        }
    } catch {
        return [pscustomobject]@{
            found = $true
            path = $FilePath
            exitCode = $null
            timedOut = $false
            stdout = ''
            stderr = ''
            error = $_.Exception.Message
        }
    } finally {
        if ($process) { $process.Dispose() }
    }
}

function Get-MtrAndroidToolchainJavaMajor {
    [CmdletBinding()]
    param([AllowNull()][string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
    if ($Text -match '(?im)^\s*(?:openjdk|java)\s+version\s+"(?:1\.)?([0-9]+)') {
        return [int]$Matches[1]
    }
    if ($Text -match '(?im)^\s*javac\s+(?:1\.)?([0-9]+)(?:\.|\s|$)') {
        return [int]$Matches[1]
    }
    return $null
}

function Get-MtrAndroidToolchainJavaProperty {
    [CmdletBinding()]
    param(
        [AllowNull()][string]$Text,
        [Parameter(Mandatory=$true)][string]$Name
    )

    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
    $escaped = [regex]::Escape($Name)
    if ($Text -match "(?im)^\s*$escaped\s*=\s*(.+?)\s*$") {
        return $Matches[1].Trim()
    }
    return $null
}

function Read-MtrAndroidToolchainReleaseFile {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)

    $result = @{}
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $result }
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ($line -match '^([A-Z0-9_]+)="(.*)"$') {
            $result[$Matches[1]] = $Matches[2]
        }
    }
    return $result
}

function Get-MtrAndroidToolchainSourceProperty {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Name
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $escaped = [regex]::Escape($Name)
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ($line -match "^\s*$escaped\s*=\s*(.+?)\s*$") {
            return $Matches[1].Trim()
        }
    }
    return $null
}

function Get-MtrAndroidToolchainAssignmentValues {
    [CmdletBinding()]
    param(
        [AllowNull()][string]$Text,
        [Parameter(Mandatory=$true)][string]$Name
    )

    if ([string]::IsNullOrWhiteSpace($Text)) { return @() }
    $normalizedText = $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    $escaped = [regex]::Escape($Name)
    # java.util.Properties accepts '=', ':', or unescaped whitespace as the
    # key/value separator. Count every active spelling so a later value cannot
    # override the validated one invisibly.
    $matches = [regex]::Matches(
        $normalizedText,
        "(?m)^[ \t\f]*$escaped(?:(?:[ \t\f]*[=:][ \t\f]*)|[ \t\f]+)([^\n]*?)$"
    )
    $values = [System.Collections.Generic.List[string]]::new()
    foreach ($match in $matches) { $values.Add($match.Groups[1].Value.Trim()) }
    $bareMatches = [regex]::Matches($normalizedText, "(?m)^[ \t\f]*$escaped$")
    foreach ($match in $bareMatches) { $values.Add('') }
    return @($values)
}

function Test-MtrAndroidToolchainPropertyContinuation {
    [CmdletBinding()]
    param([AllowNull()][string]$Text)

    if ([string]::IsNullOrEmpty($Text)) { return $false }
    $normalizedText = $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    foreach ($line in ($normalizedText -split "`n")) {
        $trimmed = $line.TrimEnd(' ', "`t")
        $slashCount = 0
        for ($index = $trimmed.Length - 1; $index -ge 0 -and $trimmed[$index] -eq '\'; $index--) {
            $slashCount += 1
        }
        if (($slashCount % 2) -eq 1) { return $true }
    }
    return $false
}

function Test-MtrAndroidToolchainEscapedPropertyKey {
    [CmdletBinding()]
    param([AllowNull()][string]$Text)

    if ([string]::IsNullOrEmpty($Text)) { return $false }
    $normalizedText = $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    foreach ($line in ($normalizedText -split "`n")) {
        $candidate = $line.TrimStart(' ', "`t", "`f")
        if ([string]::IsNullOrEmpty($candidate) -or $candidate[0] -in @('#', '!')) { continue }
        for ($index = 0; $index -lt $candidate.Length; $index++) {
            $character = $candidate[$index]
            if ($character -eq '\') {
                # Escaped and Unicode-spelled keys are rejected rather than
                # partially decoded; canonical generated keys never need them.
                return $true
            }
            if ($character -in @('=', ':', ' ', "`t", "`f")) { break }
        }
    }
    return $false
}

function Get-MtrAndroidToolchainAmbientJava {
    [CmdletBinding()]
    param([switch]$SkipProbe)

    $command = Get-Command -Name 'java' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command -or -not $command.Source) {
        return [pscustomobject]@{
            found = $false
            path = $null
            major = $null
            selectedForBuild = $false
            probeSkipped = [bool]$SkipProbe
        }
    }
    $path = $command.Source
    $major = $null
    if (-not $SkipProbe) {
        $probe = Invoke-MtrAndroidToolchainVersionProbe -FilePath $path
        $major = Get-MtrAndroidToolchainJavaMajor -Text ($probe.stdout + "`n" + $probe.stderr)
    }
    return [pscustomobject]@{
        found = $true
        path = $path
        major = $major
        selectedForBuild = $false
        probeSkipped = [bool]$SkipProbe
    }
}

function Add-MtrAndroidToolchainBlocker {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][AllowEmptyCollection()][System.Collections.Generic.List[string]]$Blockers,
        [Parameter(Mandatory=$true)][string]$Code
    )

    if (-not $Blockers.Contains($Code)) { $Blockers.Add($Code) }
}

function Test-MtrAndroidBuildToolchain {
    [CmdletBinding()]
    param(
        [string]$ProjectRoot = (Get-Location).Path,
        [string]$ConfigPath = 'build-android-emulator.json',
        [string]$ContractPath = 'tools/codex/android-build-toolchain.contract.json',
        [switch]$CheckGeneratedExport,
        [switch]$RequireGeneratedExport
    )

    $blockers = [System.Collections.Generic.List[string]]::new()
    $root = Get-MtrAndroidToolchainFullPath -Path $ProjectRoot
    $contractRecord = Read-MtrAndroidToolchainJson `
        -ProjectRoot $root `
        -Path $ContractPath `
        -Label 'Android toolchain contract'
    $configRecord = Read-MtrAndroidToolchainJson `
        -ProjectRoot $root `
        -Path $ConfigPath `
        -Label 'Android build config'
    $contract = $contractRecord.value
    $config = $configRecord.value

    if (-not (Test-MtrAndroidToolchainExactProperties $contract @(
        'schema_version', 'contract', 'java', 'cocos_creator', 'android',
        'build_configs', 'generated_exports', 'policy'
    ))) {
        Add-MtrAndroidToolchainBlocker $blockers 'contract-root-shape-invalid'
    }

    $canonicalContractPath = Join-Path $root 'tools\codex\android-build-toolchain.contract.json'
    if (-not (Test-MtrAndroidToolchainPathEqual $contractRecord.path $canonicalContractPath)) {
        Add-MtrAndroidToolchainBlocker $blockers 'contract-path-not-canonical'
    }

    if ((Get-MtrAndroidToolchainProperty $contract 'schema_version') -ne 1 -or
        [string](Get-MtrAndroidToolchainProperty $contract 'contract') -ne 'mtr.android_build_toolchain') {
        Add-MtrAndroidToolchainBlocker $blockers 'contract-identity-invalid'
    }

    $relativeConfig = $configRecord.path.Substring($root.Length).TrimStart('\', '/').Replace('\', '/')
    $allowedConfigs = @((Get-MtrAndroidToolchainProperty $contract 'build_configs') | ForEach-Object { ([string]$_).Replace('\', '/') })
    $canonicalConfigs = @('build-android.json', 'build-android-emulator.json')
    if ($allowedConfigs.Count -ne $canonicalConfigs.Count -or
        @($canonicalConfigs | Where-Object { $allowedConfigs -notcontains $_ }).Count -gt 0) {
        Add-MtrAndroidToolchainBlocker $blockers 'build-config-registry-invalid'
    }
    if ($allowedConfigs -notcontains $relativeConfig) {
        Add-MtrAndroidToolchainBlocker $blockers 'config-not-approved'
    }
    if ([string](Get-MtrAndroidToolchainProperty $config 'platform') -ne 'android') {
        Add-MtrAndroidToolchainBlocker $blockers 'config-platform-not-android'
    }

    $packages = Get-MtrAndroidToolchainProperty $config 'packages'
    $androidConfig = Get-MtrAndroidToolchainProperty $packages 'android'
    $javaContract = Get-MtrAndroidToolchainProperty $contract 'java'
    $androidContract = Get-MtrAndroidToolchainProperty $contract 'android'
    $cocosContract = Get-MtrAndroidToolchainProperty $contract 'cocos_creator'
    $policyContract = Get-MtrAndroidToolchainProperty $contract 'policy'
    if ($null -eq $androidConfig -or $null -eq $javaContract -or $null -eq $androidContract -or $null -eq $cocosContract) {
        Add-MtrAndroidToolchainBlocker $blockers 'contract-or-config-shape-invalid'
    }
    if (-not (Test-MtrAndroidToolchainExactProperties $javaContract @(
        'required_major', 'required_version', 'required_vendor', 'required_arch',
        'approved_home', 'required_files', 'required_file_sha256',
        'forbidden_environment_overrides'
    ))) { Add-MtrAndroidToolchainBlocker $blockers 'contract-java-shape-invalid' }
    if (-not (Test-MtrAndroidToolchainExactProperties $androidContract @(
        'sdk_path', 'configured_api_level', 'generated_compile_sdk',
        'build_tools_version', 'ndk_version', 'cmake_version',
        'gradle_wrapper_version', 'gradle_distribution_url',
        'gradlew_bat_sha256', 'gradle_wrapper_jar_sha256',
        'android_gradle_plugin_version'
    ))) { Add-MtrAndroidToolchainBlocker $blockers 'contract-android-shape-invalid' }
    if (-not (Test-MtrAndroidToolchainExactProperties $cocosContract @(
        'version', 'executable', 'executable_sha256'
    ))) { Add-MtrAndroidToolchainBlocker $blockers 'contract-cocos-shape-invalid' }
    if (-not (Test-MtrAndroidToolchainExactProperties $policyContract @(
        'configured_java_only', 'ambient_fallback', 'global_environment_mutation',
        'fresh_export_validation'
    )) -or
        (Get-MtrAndroidToolchainProperty $policyContract 'configured_java_only') -ne $true -or
        (Get-MtrAndroidToolchainProperty $policyContract 'ambient_fallback') -ne $false -or
        (Get-MtrAndroidToolchainProperty $policyContract 'global_environment_mutation') -ne $false -or
        [string](Get-MtrAndroidToolchainProperty $policyContract 'fresh_export_validation') -ne 'DEFERRED_TO_FIRST_ANDROID_P4') {
        Add-MtrAndroidToolchainBlocker $blockers 'contract-policy-invalid'
    }

    # The executable preflight must enforce the approved policy independently
    # of the JSON/schema static gate. A caller may not redefine both config and
    # contract to make an ambient or newly installed toolchain self-consistent.
    $pinnedJdkFiles = @('bin\java.exe', 'bin\javac.exe', 'bin\jar.exe', 'release')
    $pinnedJdkHashes = [ordered]@{
        'bin\java.exe' = '5B463CAD4FCD8E4C655CC1C6F45A3B2EBB002ADAC94EBAD2FDAA4F43E2AEE211'
        'bin\javac.exe' = 'FA184CDE00F7E93CB55C10E961F1AE0829DFC5EC5A3460E2C7567C8EF8CEA607'
        'bin\jar.exe' = '30990B330846D520DA99EFD0323EC0C9FD890E8136A3A6A2EF149CD87898A278'
        'release' = '8DAA64B69534C11C991450ABBDF7B0DDAB73BA0F91A9F79053A98F7020ECC4EA'
    }
    $pinnedOverrides = @(
        'JAVA_TOOL_OPTIONS', 'JAVA_OPTS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS',
        'GRADLE_OPTS', 'ORG_GRADLE_PROJECT_org.gradle.java.home', 'GRADLE_USER_HOME'
    )
    $contractJdkFiles = @((Get-MtrAndroidToolchainProperty $javaContract 'required_files') | ForEach-Object { [string]$_ })
    $contractJdkHashes = Get-MtrAndroidToolchainProperty $javaContract 'required_file_sha256'
    $contractOverrides = @((Get-MtrAndroidToolchainProperty $javaContract 'forbidden_environment_overrides') | ForEach-Object { [string]$_ })
    $javaPolicyMismatch = (
        (Get-MtrAndroidToolchainProperty $javaContract 'required_major') -ne 17 -or
        [string](Get-MtrAndroidToolchainProperty $javaContract 'required_version') -ne '17.0.20' -or
        [string](Get-MtrAndroidToolchainProperty $javaContract 'required_vendor') -ne 'Eclipse Adoptium' -or
        [string](Get-MtrAndroidToolchainProperty $javaContract 'required_arch') -ne 'x86_64' -or
        -not (Test-MtrAndroidToolchainPathEqual ([string](Get-MtrAndroidToolchainProperty $javaContract 'approved_home')) 'C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot') -or
        $contractJdkFiles.Count -ne $pinnedJdkFiles.Count -or
        @($pinnedJdkFiles | Where-Object { $contractJdkFiles -notcontains $_ }).Count -gt 0 -or
        $contractOverrides.Count -ne $pinnedOverrides.Count -or
        @($pinnedOverrides | Where-Object { $contractOverrides -notcontains $_ }).Count -gt 0
    )
    foreach ($pinnedFile in $pinnedJdkFiles) {
        if ([string](Get-MtrAndroidToolchainProperty $contractJdkHashes $pinnedFile) -ne $pinnedJdkHashes[$pinnedFile]) {
            $javaPolicyMismatch = $true
        }
    }
    if ($javaPolicyMismatch) {
        Add-MtrAndroidToolchainBlocker $blockers 'contract-java-policy-not-approved'
    }

    if ([string](Get-MtrAndroidToolchainProperty $cocosContract 'version') -ne '3.8.8' -or
        -not (Test-MtrAndroidToolchainPathEqual ([string](Get-MtrAndroidToolchainProperty $cocosContract 'executable')) 'C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe') -or
        [string](Get-MtrAndroidToolchainProperty $cocosContract 'executable_sha256') -ne '801334988540FA826A3016F21F8B7B039C855238E8F48BFA59B8BAE393C11CB5') {
        Add-MtrAndroidToolchainBlocker $blockers 'contract-cocos-policy-not-approved'
    }

    if (-not (Test-MtrAndroidToolchainPathEqual ([string](Get-MtrAndroidToolchainProperty $androidContract 'sdk_path')) 'C:\Users\nikit\AppData\Local\Android\Sdk') -or
        (Get-MtrAndroidToolchainProperty $androidContract 'configured_api_level') -ne 35 -or
        (Get-MtrAndroidToolchainProperty $androidContract 'generated_compile_sdk') -ne 36 -or
        [string](Get-MtrAndroidToolchainProperty $androidContract 'build_tools_version') -ne '36.0.0' -or
        [string](Get-MtrAndroidToolchainProperty $androidContract 'ndk_version') -ne '23.2.8568313' -or
        [string](Get-MtrAndroidToolchainProperty $androidContract 'cmake_version') -ne '3.22.1' -or
        [string](Get-MtrAndroidToolchainProperty $androidContract 'gradle_wrapper_version') -ne '8.11.1' -or
        [string](Get-MtrAndroidToolchainProperty $androidContract 'gradle_distribution_url') -ne 'https://services.gradle.org/distributions/gradle-8.11.1-bin.zip' -or
        [string](Get-MtrAndroidToolchainProperty $androidContract 'gradlew_bat_sha256') -ne 'C13C6E91B9A517783976DE213D46398C661EA9E17651376D7301E839EAEDCC62' -or
        [string](Get-MtrAndroidToolchainProperty $androidContract 'gradle_wrapper_jar_sha256') -ne 'E2B82129AB64751FD40437007BD2F7F2AFB3C6E41A9198E628650B22D5824A14' -or
        [string](Get-MtrAndroidToolchainProperty $androidContract 'android_gradle_plugin_version') -ne '8.10.1') {
        Add-MtrAndroidToolchainBlocker $blockers 'contract-android-policy-not-approved'
    }

    $expectedOutputName = if ($relativeConfig -eq 'build-android.json') {
        'android'
    } elseif ($relativeConfig -eq 'build-android-emulator.json') {
        'android-emulator'
    } else { '' }
    $configuredOutputName = [string](Get-MtrAndroidToolchainProperty $config 'outputName')
    if ([string](Get-MtrAndroidToolchainProperty $config 'buildPath') -ne 'project://build') {
        Add-MtrAndroidToolchainBlocker $blockers 'config-build-path-not-approved'
    }
    if ([string]::IsNullOrWhiteSpace($expectedOutputName) -or $configuredOutputName -ne $expectedOutputName) {
        Add-MtrAndroidToolchainBlocker $blockers 'config-output-name-not-approved'
    }

    $generatedExports = @((Get-MtrAndroidToolchainProperty $contract 'generated_exports'))
    $exportMatches = @($generatedExports | Where-Object {
        ([string](Get-MtrAndroidToolchainProperty $_ 'config')).Replace('\', '/') -eq $relativeConfig
    })
    $exportEntry = if ($exportMatches.Count -eq 1) { $exportMatches[0] } else { $null }
    $generatedRoot = $null
    if ($null -eq $exportEntry) {
        Add-MtrAndroidToolchainBlocker $blockers 'generated-export-contract-missing-or-duplicate'
    } else {
        if (-not (Test-MtrAndroidToolchainExactProperties $exportEntry @('config', 'output_name', 'project'))) {
            Add-MtrAndroidToolchainBlocker $blockers 'generated-export-contract-shape-invalid'
        }
        $contractOutputName = [string](Get-MtrAndroidToolchainProperty $exportEntry 'output_name')
        $projectRelative = ([string](Get-MtrAndroidToolchainProperty $exportEntry 'project')).Replace('\', '/').Trim('/')
        $canonicalProjectRelative = "build/$expectedOutputName/proj"
        if ($contractOutputName -ne $expectedOutputName -or $projectRelative -ne $canonicalProjectRelative) {
            Add-MtrAndroidToolchainBlocker $blockers 'generated-export-binding-mismatch'
        }
        try {
            $generatedRoot = Resolve-MtrAndroidToolchainProjectPath `
                -ProjectRoot $root `
                -Path $projectRelative `
                -Label 'Generated Android project'
        } catch {
            Add-MtrAndroidToolchainBlocker $blockers 'generated-export-project-escapes-root'
        }
        if ($null -ne $generatedRoot -and
            -not (Test-MtrAndroidToolchainNoReparsePoints -ProjectRoot $root -CandidatePath $generatedRoot)) {
            Add-MtrAndroidToolchainBlocker $blockers 'generated-export-reparse-point-not-allowed'
        }
    }

    $configuredHome = [string](Get-MtrAndroidToolchainProperty $androidConfig 'javaHome')
    $configuredBin = [string](Get-MtrAndroidToolchainProperty $androidConfig 'javaPath')
    $approvedHome = [string](Get-MtrAndroidToolchainProperty $javaContract 'approved_home')
    $requiredMajor = [int](Get-MtrAndroidToolchainProperty $javaContract 'required_major')
    $requiredVersion = [string](Get-MtrAndroidToolchainProperty $javaContract 'required_version')
    $requiredVendor = [string](Get-MtrAndroidToolchainProperty $javaContract 'required_vendor')
    $requiredArch = [string](Get-MtrAndroidToolchainProperty $javaContract 'required_arch')
    $expectedBin = if ([string]::IsNullOrWhiteSpace($configuredHome)) { '' } else { Join-Path $configuredHome 'bin' }

    if ([string]::IsNullOrWhiteSpace($configuredHome)) {
        Add-MtrAndroidToolchainBlocker $blockers 'configured-java-home-missing'
    } elseif (-not (Test-MtrAndroidToolchainPathEqual $configuredHome $approvedHome)) {
        Add-MtrAndroidToolchainBlocker $blockers 'configured-java-home-not-approved'
    }
    if ([string]::IsNullOrWhiteSpace($configuredBin) -or
        [string]::IsNullOrWhiteSpace($expectedBin) -or
        -not (Test-MtrAndroidToolchainPathEqual $configuredBin $expectedBin)) {
        Add-MtrAndroidToolchainBlocker $blockers 'configured-java-path-mismatch'
    }

    $requiredFiles = @((Get-MtrAndroidToolchainProperty $javaContract 'required_files'))
    $requiredFileHashes = Get-MtrAndroidToolchainProperty $javaContract 'required_file_sha256'
    $requiredFileActualHashes = [ordered]@{}
    if (-not (Test-MtrAndroidToolchainExactProperties $requiredFileHashes @($requiredFiles | ForEach-Object { [string]$_ }))) {
        Add-MtrAndroidToolchainBlocker $blockers 'contract-jdk-hash-registry-invalid'
    }
    foreach ($relative in $requiredFiles) {
        $requiredPath = if ([string]::IsNullOrWhiteSpace($configuredHome)) { '' } else { Join-Path $configuredHome ([string]$relative) }
        if ([string]::IsNullOrWhiteSpace($requiredPath) -or
            -not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
            Add-MtrAndroidToolchainBlocker $blockers ("configured-jdk-file-missing:{0}" -f ([string]$relative).Replace('\', '/'))
        } else {
            $expectedHash = [string](Get-MtrAndroidToolchainProperty $requiredFileHashes ([string]$relative))
            $actualHash = (Get-FileHash -LiteralPath $requiredPath -Algorithm SHA256).Hash
            $requiredFileActualHashes[[string]$relative] = $actualHash
            if ([string]::IsNullOrWhiteSpace($expectedHash) -or $actualHash -ne $expectedHash) {
                Add-MtrAndroidToolchainBlocker $blockers ("configured-jdk-file-hash-mismatch:{0}" -f ([string]$relative).Replace('\', '/'))
            }
        }
    }

    $overrideNames = @((Get-MtrAndroidToolchainProperty $javaContract 'forbidden_environment_overrides'))
    $activeOverrides = [System.Collections.Generic.List[string]]::new()
    foreach ($name in $overrideNames) {
        $value = [Environment]::GetEnvironmentVariable([string]$name, 'Process')
        # A defined override is active even when its value is whitespace-only.
        # In particular, Gradle treats GRADLE_USER_HOME as a selected location;
        # silently trimming it here would let validation inspect a different home.
        if ($null -ne $value) {
            $activeOverrides.Add([string]$name)
            Add-MtrAndroidToolchainBlocker $blockers ("environment-override-active:{0}" -f [string]$name)
        }
    }

    $authoritativeUserProfile = $null
    try {
        $authoritativeUserProfile = Get-MtrAndroidToolchainAuthoritativeUserProfile
    } catch {
        Add-MtrAndroidToolchainBlocker $blockers 'authoritative-user-profile-unavailable'
    }
    $processUserProfile = [Environment]::GetEnvironmentVariable('USERPROFILE', 'Process')
    if (-not [string]::IsNullOrWhiteSpace($processUserProfile) -and
        -not [string]::IsNullOrWhiteSpace($authoritativeUserProfile) -and
        -not (Test-MtrAndroidToolchainPathEqual $processUserProfile $authoritativeUserProfile)) {
        Add-MtrAndroidToolchainBlocker $blockers 'userprofile-environment-mismatch'
    }

    $gradlePropertyPaths = [System.Collections.Generic.List[string]]::new()
    $gradlePropertyPaths.Add((Join-Path $root 'gradle.properties'))
    if (-not [string]::IsNullOrWhiteSpace($authoritativeUserProfile)) {
        $gradlePropertyPaths.Add((Join-Path $authoritativeUserProfile '.gradle\gradle.properties'))
    }

    $javaExe = if ([string]::IsNullOrWhiteSpace($configuredHome)) { '' } else { Join-Path $configuredHome 'bin\java.exe' }
    $javacExe = if ([string]::IsNullOrWhiteSpace($configuredHome)) { '' } else { Join-Path $configuredHome 'bin\javac.exe' }
    $javaProbe = $null
    $javacProbe = $null
    $javaMajor = $null
    $javacMajor = $null
    $javaHomeReported = $null
    $javaUserHomeReported = $null
    $javaVendorReported = $null
    $javaArchReported = $null
    $javaVersionReported = $null
    if ($blockers.Count -eq 0) {
        $javaProbe = Invoke-MtrAndroidToolchainVersionProbe `
            -FilePath $javaExe `
            -Arguments '-XshowSettings:properties -version'
        $javaText = $javaProbe.stdout + "`n" + $javaProbe.stderr
        $javaMajor = Get-MtrAndroidToolchainJavaMajor -Text $javaText
        $javaHomeReported = Get-MtrAndroidToolchainJavaProperty -Text $javaText -Name 'java.home'
        $javaUserHomeReported = Get-MtrAndroidToolchainJavaProperty -Text $javaText -Name 'user.home'
        $javaVersionReported = Get-MtrAndroidToolchainJavaProperty -Text $javaText -Name 'java.version'
        $javaVendorReported = Get-MtrAndroidToolchainJavaProperty -Text $javaText -Name 'java.vendor'
        $javaArchReported = Get-MtrAndroidToolchainJavaProperty -Text $javaText -Name 'os.arch'
        if ($javaProbe.exitCode -ne 0) { Add-MtrAndroidToolchainBlocker $blockers 'configured-java-probe-failed' }
        if ($javaMajor -ne $requiredMajor) { Add-MtrAndroidToolchainBlocker $blockers 'configured-java-major-mismatch' }
        if ($javaVersionReported -ne $requiredVersion) { Add-MtrAndroidToolchainBlocker $blockers 'configured-java-version-mismatch' }
        if ([string]::IsNullOrWhiteSpace($javaHomeReported) -or
            -not (Test-MtrAndroidToolchainPathEqual $javaHomeReported $configuredHome)) {
            Add-MtrAndroidToolchainBlocker $blockers 'configured-java-home-report-mismatch'
        }
        if ([string]::IsNullOrWhiteSpace($javaUserHomeReported) -or
            [string]::IsNullOrWhiteSpace($authoritativeUserProfile) -or
            -not (Test-MtrAndroidToolchainPathEqual $javaUserHomeReported $authoritativeUserProfile)) {
            Add-MtrAndroidToolchainBlocker $blockers 'configured-java-user-home-mismatch'
        }
        if ($javaVendorReported -ne $requiredVendor) { Add-MtrAndroidToolchainBlocker $blockers 'configured-java-vendor-mismatch' }
        if ($javaArchReported -ne $requiredArch -and $javaArchReported -ne 'amd64') {
            Add-MtrAndroidToolchainBlocker $blockers 'configured-java-arch-mismatch'
        }

        $javacProbe = Invoke-MtrAndroidToolchainVersionProbe -FilePath $javacExe
        $javacMajor = Get-MtrAndroidToolchainJavaMajor -Text ($javacProbe.stdout + "`n" + $javacProbe.stderr)
        if ($javacProbe.exitCode -ne 0) { Add-MtrAndroidToolchainBlocker $blockers 'configured-javac-probe-failed' }
        if ($javacMajor -ne $requiredMajor) { Add-MtrAndroidToolchainBlocker $blockers 'configured-javac-major-mismatch' }
    }

    # USERPROFILE is caller-controlled. Gradle user properties stay bound to
    # the SID-backed profile and the approved JDK must report the same user.home.
    foreach ($candidate in $gradlePropertyPaths) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $candidateText = Get-Content -LiteralPath $candidate -Raw -Encoding UTF8
            if (Test-MtrAndroidToolchainPropertyContinuation -Text $candidateText) {
                Add-MtrAndroidToolchainBlocker $blockers 'gradle-property-continuation-not-allowed'
            }
            if (Test-MtrAndroidToolchainEscapedPropertyKey -Text $candidateText) {
                Add-MtrAndroidToolchainBlocker $blockers 'gradle-property-escaped-key-not-allowed'
            }
            if (@(Get-MtrAndroidToolchainAssignmentValues -Text $candidateText -Name 'org.gradle.java.home').Count -gt 0) {
                Add-MtrAndroidToolchainBlocker $blockers 'gradle-java-home-override-active'
            }
        }
    }

    $releasePath = if ([string]::IsNullOrWhiteSpace($configuredHome)) { '' } else { Join-Path $configuredHome 'release' }
    $release = if ([string]::IsNullOrWhiteSpace($releasePath)) { @{} } else { Read-MtrAndroidToolchainReleaseFile -Path $releasePath }
    if ($release.Count -gt 0) {
        if ([string]$release['JAVA_VERSION'] -ne $requiredVersion) { Add-MtrAndroidToolchainBlocker $blockers 'jdk-release-version-mismatch' }
        if ([string]$release['IMPLEMENTOR'] -ne $requiredVendor) { Add-MtrAndroidToolchainBlocker $blockers 'jdk-release-vendor-mismatch' }
        if ([string]$release['OS_ARCH'] -ne $requiredArch) { Add-MtrAndroidToolchainBlocker $blockers 'jdk-release-arch-mismatch' }
        if ([string]$release['IMAGE_TYPE'] -ne 'JDK') { Add-MtrAndroidToolchainBlocker $blockers 'jdk-release-image-type-mismatch' }
    }

    $sdkPath = [string](Get-MtrAndroidToolchainProperty $androidConfig 'sdkPath')
    $ndkPath = [string](Get-MtrAndroidToolchainProperty $androidConfig 'ndkPath')
    $apiLevel = Get-MtrAndroidToolchainProperty $androidConfig 'apiLevel'
    $approvedSdk = [string](Get-MtrAndroidToolchainProperty $androidContract 'sdk_path')
    $ndkVersion = [string](Get-MtrAndroidToolchainProperty $androidContract 'ndk_version')
    $cmakeVersion = [string](Get-MtrAndroidToolchainProperty $androidContract 'cmake_version')
    $buildToolsVersion = [string](Get-MtrAndroidToolchainProperty $androidContract 'build_tools_version')
    $configuredApi = [int](Get-MtrAndroidToolchainProperty $androidContract 'configured_api_level')
    $generatedCompileSdk = [int](Get-MtrAndroidToolchainProperty $androidContract 'generated_compile_sdk')
    if (-not (Test-MtrAndroidToolchainPathEqual $sdkPath $approvedSdk)) { Add-MtrAndroidToolchainBlocker $blockers 'android-sdk-path-mismatch' }
    if (-not (Test-MtrAndroidToolchainPathEqual $ndkPath (Join-Path $approvedSdk "ndk\$ndkVersion"))) {
        Add-MtrAndroidToolchainBlocker $blockers 'android-ndk-path-mismatch'
    }
    if ($apiLevel -ne $configuredApi) { Add-MtrAndroidToolchainBlocker $blockers 'android-api-level-mismatch' }
    foreach ($requiredDirectory in @(
        $approvedSdk,
        (Join-Path $approvedSdk "platforms\android-$configuredApi"),
        (Join-Path $approvedSdk "platforms\android-$generatedCompileSdk"),
        (Join-Path $approvedSdk "build-tools\$buildToolsVersion"),
        (Join-Path $approvedSdk "ndk\$ndkVersion"),
        (Join-Path $approvedSdk "cmake\$cmakeVersion")
    )) {
        if (-not (Test-Path -LiteralPath $requiredDirectory -PathType Container)) {
            Add-MtrAndroidToolchainBlocker $blockers ("android-tool-directory-missing:{0}" -f $requiredDirectory)
        }
    }
    $ndkSourceProperties = Join-Path (Join-Path $approvedSdk "ndk\$ndkVersion") 'source.properties'
    $cmakeSourceProperties = Join-Path (Join-Path $approvedSdk "cmake\$cmakeVersion") 'source.properties'
    if ((Get-MtrAndroidToolchainSourceProperty -Path $ndkSourceProperties -Name 'Pkg.Revision') -ne $ndkVersion) {
        Add-MtrAndroidToolchainBlocker $blockers 'android-ndk-metadata-mismatch'
    }
    if ((Get-MtrAndroidToolchainSourceProperty -Path $cmakeSourceProperties -Name 'Pkg.Revision') -ne $cmakeVersion) {
        Add-MtrAndroidToolchainBlocker $blockers 'android-cmake-metadata-mismatch'
    }
    $nativeAndroidGradle = Join-Path $root 'native\engine\android\app\build.gradle'
    if (-not (Test-Path -LiteralPath $nativeAndroidGradle -PathType Leaf)) {
        Add-MtrAndroidToolchainBlocker $blockers 'native-android-gradle-missing'
    } else {
        $nativeAndroidGradleText = Get-Content -LiteralPath $nativeAndroidGradle -Raw -Encoding UTF8
        $cmakeVersionMatches = [regex]::Matches(
            $nativeAndroidGradleText,
            ('(?m)^\s*version\s+"{0}"\s*$' -f [regex]::Escape($cmakeVersion))
        )
        if ($cmakeVersionMatches.Count -ne 1) {
            Add-MtrAndroidToolchainBlocker $blockers 'native-cmake-version-mismatch'
        }
    }

    $packagePath = Join-Path $root 'package.json'
    try {
        $package = Get-Content -LiteralPath $packagePath -Raw -Encoding UTF8 | ConvertFrom-Json
        $creatorVersion = [string](Get-MtrAndroidToolchainProperty (Get-MtrAndroidToolchainProperty $package 'creator') 'version')
    } catch {
        $creatorVersion = ''
    }
    $expectedCreatorVersion = [string](Get-MtrAndroidToolchainProperty $cocosContract 'version')
    $cocosExe = [string](Get-MtrAndroidToolchainProperty $cocosContract 'executable')
    $expectedCocosHash = [string](Get-MtrAndroidToolchainProperty $cocosContract 'executable_sha256')
    if ($creatorVersion -ne $expectedCreatorVersion) { Add-MtrAndroidToolchainBlocker $blockers 'cocos-project-version-mismatch' }
    $cocosFileVersion = $null
    if (-not (Test-Path -LiteralPath $cocosExe -PathType Leaf)) {
        Add-MtrAndroidToolchainBlocker $blockers 'cocos-executable-missing'
    } else {
        $cocosFileVersion = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($cocosExe).ProductVersion
        if ($cocosFileVersion -ne $expectedCreatorVersion) { Add-MtrAndroidToolchainBlocker $blockers 'cocos-file-version-mismatch' }
        if ((Get-FileHash -LiteralPath $cocosExe -Algorithm SHA256).Hash -ne $expectedCocosHash) {
            Add-MtrAndroidToolchainBlocker $blockers 'cocos-executable-hash-mismatch'
        }
    }

    $generatedEvidence = [pscustomobject]@{
        checked = [bool]$CheckGeneratedExport
        required = [bool]$RequireGeneratedExport
        project = $null
        wrapperVersion = $null
        distributionUrl = $null
        gradlewBatSha256 = $null
        wrapperJarSha256 = $null
        daemonJvmCriteriaAbsent = $null
        androidGradlePluginVersion = $null
        compileSdk = $null
        targetSdk = $null
        buildToolsVersion = $null
        ndkVersion = $null
        sdkPath = $null
        status = 'NOT_CHECKED'
    }
    if ($CheckGeneratedExport -or $RequireGeneratedExport) {
        if ($null -eq $exportEntry -or [string]::IsNullOrWhiteSpace([string]$generatedRoot)) {
            Add-MtrAndroidToolchainBlocker $blockers 'generated-export-contract-missing'
            $generatedEvidence.status = 'MISSING'
        } else {
            $generatedEvidence.project = $generatedRoot
            $wrapperPath = Join-Path $generatedRoot 'gradle\wrapper\gradle-wrapper.properties'
            $wrapperJarPath = Join-Path $generatedRoot 'gradle\wrapper\gradle-wrapper.jar'
            $gradlewBatPath = Join-Path $generatedRoot 'gradlew.bat'
            $daemonJvmCriteriaPath = Join-Path $generatedRoot 'gradle\gradle-daemon-jvm.properties'
            $buildGradlePath = Join-Path $generatedRoot 'build.gradle'
            $generatedGradleProperties = Join-Path $generatedRoot 'gradle.properties'
            $generatedLocalProperties = Join-Path $generatedRoot 'local.properties'
            if (-not (Test-Path -LiteralPath $generatedRoot -PathType Container)) {
                if ($RequireGeneratedExport) { Add-MtrAndroidToolchainBlocker $blockers 'generated-export-missing' }
                $generatedEvidence.status = 'NOT_PRESENT'
            } elseif (-not (Test-Path -LiteralPath $wrapperPath -PathType Leaf) -or
                -not (Test-Path -LiteralPath $wrapperJarPath -PathType Leaf) -or
                -not (Test-Path -LiteralPath $gradlewBatPath -PathType Leaf) -or
                -not (Test-Path -LiteralPath $buildGradlePath -PathType Leaf) -or
                -not (Test-Path -LiteralPath $generatedGradleProperties -PathType Leaf) -or
                -not (Test-Path -LiteralPath $generatedLocalProperties -PathType Leaf)) {
                Add-MtrAndroidToolchainBlocker $blockers 'generated-export-incomplete'
                $generatedEvidence.status = 'FAIL'
            } else {
                $wrapperText = Get-Content -LiteralPath $wrapperPath -Raw -Encoding UTF8
                $buildGradleText = Get-Content -LiteralPath $buildGradlePath -Raw -Encoding UTF8
                $generatedPropertiesText = Get-Content -LiteralPath $generatedGradleProperties -Raw -Encoding UTF8
                $generatedLocalPropertiesText = Get-Content -LiteralPath $generatedLocalProperties -Raw -Encoding UTF8
                if (Test-MtrAndroidToolchainPropertyContinuation -Text $wrapperText) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-wrapper-property-continuation-not-allowed'
                }
                if (Test-MtrAndroidToolchainEscapedPropertyKey -Text $wrapperText) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-wrapper-escaped-key-not-allowed'
                }
                if (Test-MtrAndroidToolchainEscapedPropertyKey -Text $generatedPropertiesText) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-gradle-escaped-key-not-allowed'
                }
                if (Test-MtrAndroidToolchainEscapedPropertyKey -Text $generatedLocalPropertiesText) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-local-escaped-key-not-allowed'
                }
                if (Test-MtrAndroidToolchainPropertyContinuation -Text $generatedPropertiesText) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-gradle-property-continuation-not-allowed'
                }
                if (Test-MtrAndroidToolchainPropertyContinuation -Text $generatedLocalPropertiesText) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-local-property-continuation-not-allowed'
                }
                $expectedGradle = [string](Get-MtrAndroidToolchainProperty $androidContract 'gradle_wrapper_version')
                $expectedDistributionUrl = [string](Get-MtrAndroidToolchainProperty $androidContract 'gradle_distribution_url')
                $expectedGradlewBatHash = [string](Get-MtrAndroidToolchainProperty $androidContract 'gradlew_bat_sha256')
                $expectedWrapperJarHash = [string](Get-MtrAndroidToolchainProperty $androidContract 'gradle_wrapper_jar_sha256')
                $expectedAgp = [string](Get-MtrAndroidToolchainProperty $androidContract 'android_gradle_plugin_version')
                $expectedCompileSdk = [int](Get-MtrAndroidToolchainProperty $androidContract 'generated_compile_sdk')
                $assignmentCountsValid = $true
                $generatedEvidence.gradlewBatSha256 = (Get-FileHash -LiteralPath $gradlewBatPath -Algorithm SHA256).Hash
                $generatedEvidence.wrapperJarSha256 = (Get-FileHash -LiteralPath $wrapperJarPath -Algorithm SHA256).Hash
                if ($generatedEvidence.gradlewBatSha256 -ne $expectedGradlewBatHash) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-gradlew-bat-hash-mismatch'
                }
                if ($generatedEvidence.wrapperJarSha256 -ne $expectedWrapperJarHash) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-wrapper-jar-hash-mismatch'
                }
                $generatedEvidence.daemonJvmCriteriaAbsent = -not (Test-Path -LiteralPath $daemonJvmCriteriaPath)
                if (-not $generatedEvidence.daemonJvmCriteriaAbsent) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-gradle-daemon-jvm-criteria-not-allowed'
                }
                $wrapperUrls = @(Get-MtrAndroidToolchainAssignmentValues -Text $wrapperText -Name 'distributionUrl')
                if ($wrapperUrls.Count -ne 1) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-wrapper-distribution-url-count'
                    $assignmentCountsValid = $false
                } else {
                    $generatedEvidence.distributionUrl = $wrapperUrls[0].Replace('\:', ':')
                    if ($generatedEvidence.distributionUrl -ne $expectedDistributionUrl) {
                        Add-MtrAndroidToolchainBlocker $blockers 'generated-gradle-distribution-url-mismatch'
                    } elseif ($generatedEvidence.distributionUrl -match 'gradle-([0-9.]+)-bin\.zip$') {
                        $generatedEvidence.wrapperVersion = $Matches[1]
                    }
                }
                $agpMatches = [regex]::Matches($buildGradleText, 'com\.android\.tools\.build:gradle:([0-9.]+)')
                if ($agpMatches.Count -ne 1) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-agp-dependency-count'
                    $assignmentCountsValid = $false
                } else {
                    $generatedEvidence.androidGradlePluginVersion = $agpMatches[0].Groups[1].Value
                }
                $compileValues = @(Get-MtrAndroidToolchainAssignmentValues -Text $generatedPropertiesText -Name 'PROP_COMPILE_SDK_VERSION')
                $targetValues = @(Get-MtrAndroidToolchainAssignmentValues -Text $generatedPropertiesText -Name 'PROP_TARGET_SDK_VERSION')
                $buildToolsValues = @(Get-MtrAndroidToolchainAssignmentValues -Text $generatedPropertiesText -Name 'PROP_BUILD_TOOLS_VERSION')
                $ndkValues = @(Get-MtrAndroidToolchainAssignmentValues -Text $generatedPropertiesText -Name 'PROP_NDK_VERSION')
                foreach ($assignment in @(
                    [pscustomobject]@{ name = 'PROP_COMPILE_SDK_VERSION'; values = $compileValues },
                    [pscustomobject]@{ name = 'PROP_TARGET_SDK_VERSION'; values = $targetValues },
                    [pscustomobject]@{ name = 'PROP_BUILD_TOOLS_VERSION'; values = $buildToolsValues },
                    [pscustomobject]@{ name = 'PROP_NDK_VERSION'; values = $ndkValues }
                )) {
                    if (@($assignment.values).Count -ne 1) {
                        Add-MtrAndroidToolchainBlocker $blockers ("generated-property-assignment-count:{0}" -f $assignment.name)
                        $assignmentCountsValid = $false
                    }
                }
                if ($compileValues.Count -eq 1 -and $compileValues[0] -match '^[0-9]+$') { $generatedEvidence.compileSdk = [int]$compileValues[0] }
                if ($targetValues.Count -eq 1 -and $targetValues[0] -match '^[0-9]+$') { $generatedEvidence.targetSdk = [int]$targetValues[0] }
                if ($buildToolsValues.Count -eq 1) { $generatedEvidence.buildToolsVersion = $buildToolsValues[0] }
                if ($ndkValues.Count -eq 1) { $generatedEvidence.ndkVersion = $ndkValues[0] }
                if ($generatedEvidence.wrapperVersion -ne $expectedGradle) { Add-MtrAndroidToolchainBlocker $blockers 'generated-gradle-wrapper-version-mismatch' }
                if ($generatedEvidence.androidGradlePluginVersion -ne $expectedAgp) { Add-MtrAndroidToolchainBlocker $blockers 'generated-agp-version-mismatch' }
                if ($generatedEvidence.compileSdk -ne $expectedCompileSdk) { Add-MtrAndroidToolchainBlocker $blockers 'generated-compile-sdk-mismatch' }
                if ($generatedEvidence.targetSdk -ne $configuredApi) { Add-MtrAndroidToolchainBlocker $blockers 'generated-target-sdk-mismatch' }
                if ($generatedEvidence.buildToolsVersion -ne $buildToolsVersion) { Add-MtrAndroidToolchainBlocker $blockers 'generated-build-tools-version-mismatch' }
                if ($generatedEvidence.ndkVersion -ne $ndkVersion) { Add-MtrAndroidToolchainBlocker $blockers 'generated-ndk-version-mismatch' }
                $generatedSdkPath = $null
                $sdkDirValues = @(Get-MtrAndroidToolchainAssignmentValues -Text $generatedLocalPropertiesText -Name 'sdk.dir')
                if ($sdkDirValues.Count -ne 1) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-sdk-dir-assignment-count'
                    $assignmentCountsValid = $false
                } else {
                    $generatedSdkPath = $sdkDirValues[0].Replace('\:', ':').Replace('\\', '\')
                }
                if (-not (Test-MtrAndroidToolchainPathEqual ([string]$generatedSdkPath) $approvedSdk)) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-sdk-path-mismatch'
                }
                $generatedEvidence.sdkPath = $generatedSdkPath
                $generatedOverrideActive = $false
                if (@(Get-MtrAndroidToolchainAssignmentValues -Text $generatedPropertiesText -Name 'org.gradle.java.home').Count -gt 0) {
                    Add-MtrAndroidToolchainBlocker $blockers 'generated-gradle-java-home-override-active'
                    $generatedOverrideActive = $true
                }
                $generatedEvidence.status = if (
                    $generatedEvidence.wrapperVersion -eq $expectedGradle -and
                    $generatedEvidence.distributionUrl -eq $expectedDistributionUrl -and
                    $generatedEvidence.gradlewBatSha256 -eq $expectedGradlewBatHash -and
                    $generatedEvidence.wrapperJarSha256 -eq $expectedWrapperJarHash -and
                    $generatedEvidence.daemonJvmCriteriaAbsent -and
                    $generatedEvidence.androidGradlePluginVersion -eq $expectedAgp -and
                    $generatedEvidence.compileSdk -eq $expectedCompileSdk -and
                    $generatedEvidence.targetSdk -eq $configuredApi -and
                    $generatedEvidence.buildToolsVersion -eq $buildToolsVersion -and
                    $generatedEvidence.ndkVersion -eq $ndkVersion -and
                    (Test-MtrAndroidToolchainPathEqual ([string]$generatedSdkPath) $approvedSdk) -and
                    $assignmentCountsValid -and
                    -not $generatedOverrideActive
                ) { 'PASS' } else { 'FAIL' }
            }
        }
    }

    $ambientJava = Get-MtrAndroidToolchainAmbientJava -SkipProbe:($activeOverrides.Count -gt 0)
    $result = [pscustomobject][ordered]@{
        contract = 'mtr.android_build_toolchain_preflight'
        schemaVersion = 1
        status = if ($blockers.Count -eq 0) { 'PASS' } else { 'BLOCKED' }
        projectRoot = $root
        configPath = $relativeConfig
        contractPath = $contractRecord.path.Substring($root.Length).TrimStart('\', '/').Replace('\', '/')
        contractSha256 = (Get-FileHash -LiteralPath $contractRecord.path -Algorithm SHA256).Hash
        configuredJavaOnly = $true
        ambientFallbackAllowed = $false
        androidBuildJava = [pscustomobject][ordered]@{
            home = $configuredHome
            bin = $configuredBin
            executable = $javaExe
            major = $javaMajor
            version = $javaVersionReported
            javacMajor = $javacMajor
            vendor = $javaVendorReported
            arch = $javaArchReported
            userHome = $javaUserHomeReported
            fileSha256 = [pscustomobject]$requiredFileActualHashes
            resolution = 'config-approved'
            selectedForBuild = ($blockers.Count -eq 0)
        }
        ambientJava = $ambientJava
        environmentOverrides = @($activeOverrides)
        gradlePropertiesChecked = @($gradlePropertyPaths)
        cocosCreator = [pscustomobject]@{
            version = $creatorVersion
            fileVersion = $cocosFileVersion
            executable = $cocosExe
            sha256 = if (Test-Path -LiteralPath $cocosExe -PathType Leaf) { (Get-FileHash -LiteralPath $cocosExe -Algorithm SHA256).Hash } else { $null }
        }
        android = [pscustomobject]@{
            sdkPath = $sdkPath
            apiLevel = $apiLevel
            generatedCompileSdk = $generatedCompileSdk
            ndkPath = $ndkPath
            ndkVersion = $ndkVersion
            cmakeVersion = $cmakeVersion
            buildToolsVersion = $buildToolsVersion
        }
        generatedExport = $generatedEvidence
        blockers = @($blockers)
        preventions = @(
            'configured-java-only-no-path-or-java-home-fallback',
            'explicit-java-and-javac-major-17-probes',
            'java-home-vendor-architecture-identity',
            'jdk-not-jre-required-files',
            'hidden-java-and-gradle-override-rejection',
            'process-only-environment-binding',
            'fresh-export-validation-deferred-to-first-android-p4'
        )
    }
    return $result
}

function Assert-MtrAndroidBuildToolchain {
    [CmdletBinding()]
    param(
        [string]$ProjectRoot = (Get-Location).Path,
        [string]$ConfigPath = 'build-android-emulator.json',
        [string]$ContractPath = 'tools/codex/android-build-toolchain.contract.json',
        [switch]$CheckGeneratedExport,
        [switch]$RequireGeneratedExport
    )

    $result = Test-MtrAndroidBuildToolchain @PSBoundParameters
    if ($result.status -ne 'PASS') {
        throw "Android build toolchain preflight blocked: $(@($result.blockers) -join ', ')"
    }
    return $result
}

function Invoke-MtrAndroidBuildJavaScope {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Toolchain,
        [Parameter(Mandatory=$true)][scriptblock]$ScriptBlock
    )

    if ($null -eq $Toolchain -or $Toolchain.status -ne 'PASS') {
        throw 'Android build Java scope requires a passing toolchain preflight.'
    }
    $javaHome = [string]$Toolchain.androidBuildJava.home
    $javaBin = [string]$Toolchain.androidBuildJava.bin
    if ([string]::IsNullOrWhiteSpace($javaHome) -or
        [string]::IsNullOrWhiteSpace($javaBin) -or
        -not (Test-Path -LiteralPath (Join-Path $javaBin 'java.exe') -PathType Leaf)) {
        throw 'Android build Java scope received an invalid configured JDK.'
    }

    $previousJavaHome = $env:JAVA_HOME
    $previousPath = $env:Path
    try {
        $env:JAVA_HOME = $javaHome
        $env:Path = "{0}{1}{2}" -f $javaBin, [System.IO.Path]::PathSeparator, $previousPath
        return & $ScriptBlock
    } finally {
        $env:JAVA_HOME = $previousJavaHome
        $env:Path = $previousPath
    }
}

Export-ModuleMember -Function @(
    'Assert-MtrAndroidBuildToolchain',
    'Get-MtrAndroidToolchainJavaMajor',
    'Invoke-MtrAndroidBuildJavaScope',
    'Test-MtrAndroidBuildToolchain'
)
