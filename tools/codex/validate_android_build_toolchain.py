#!/usr/bin/env python3
"""Cross-platform exact-contract and negative-matrix validator for TC-01."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


CONFIGS = ("build-android.json", "build-android-emulator.json")
OUTPUTS = {
    "build-android.json": "android",
    "build-android-emulator.json": "android-emulator",
}
APPROVED_HOME = r"C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot"
APPROVED_COCOS = r"C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe"
JDK_HASHES = {
    r"bin\java.exe": "5B463CAD4FCD8E4C655CC1C6F45A3B2EBB002ADAC94EBAD2FDAA4F43E2AEE211",
    r"bin\javac.exe": "FA184CDE00F7E93CB55C10E961F1AE0829DFC5EC5A3460E2C7567C8EF8CEA607",
    r"bin\jar.exe": "30990B330846D520DA99EFD0323EC0C9FD890E8136A3A6A2EF149CD87898A278",
    "release": "8DAA64B69534C11C991450ABBDF7B0DDAB73BA0F91A9F79053A98F7020ECC4EA",
}
COCOS_HASH = "801334988540FA826A3016F21F8B7B039C855238E8F48BFA59B8BAE393C11CB5"
GRADLE_DISTRIBUTION_URL = "https://services.gradle.org/distributions/gradle-8.11.1-bin.zip"
GRADLEW_BAT_HASH = "C13C6E91B9A517783976DE213D46398C661EA9E17651376D7301E839EAEDCC62"
GRADLE_WRAPPER_JAR_HASH = "E2B82129AB64751FD40437007BD2F7F2AFB3C6E41A9198E628650B22D5824A14"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_windows_path(value: Any) -> str:
    return str(value or "").replace("/", "\\").rstrip("\\").casefold()


def exact_keys(value: Any, expected: set[str], code: str, errors: list[str]) -> bool:
    if not isinstance(value, dict) or set(value) != expected:
        errors.append(code)
        return False
    return True


def schema_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def validate_schema_instance(instance: Any, schema: Any, path: str = "$") -> list[str]:
    """Apply the Draft-2020-12 keywords used by this repository schema."""
    errors: list[str] = []
    if not isinstance(schema, dict):
        return [f"schema:{path}:schema_not_object"]
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not schema_type_matches(instance, expected_type):
        return [f"schema:{path}:type"]
    if "const" in schema and instance != schema["const"]:
        errors.append(f"schema:{path}:const")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for name in required:
                if name not in instance:
                    errors.append(f"schema:{path}:required:{name}")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        if schema.get("additionalProperties") is False:
            for name in instance:
                if name not in properties:
                    errors.append(f"schema:{path}:additional:{name}")
        for name, subschema in properties.items():
            if name in instance:
                errors.extend(validate_schema_instance(instance[name], subschema, f"{path}.{name}"))

    if isinstance(instance, list):
        if isinstance(schema.get("minItems"), int) and len(instance) < schema["minItems"]:
            errors.append(f"schema:{path}:minItems")
        if isinstance(schema.get("maxItems"), int) and len(instance) > schema["maxItems"]:
            errors.append(f"schema:{path}:maxItems")
        if schema.get("uniqueItems") is True:
            canonical = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in instance]
            if len(canonical) != len(set(canonical)):
                errors.append(f"schema:{path}:uniqueItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate_schema_instance(item, item_schema, f"{path}[{index}]"))

    if isinstance(instance, str):
        if isinstance(schema.get("minLength"), int) and len(instance) < schema["minLength"]:
            errors.append(f"schema:{path}:minLength")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, instance) is None:
            errors.append(f"schema:{path}:pattern")
    return errors


def normalize_project_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").strip("/")


def project_path_is_contained(value: Any) -> bool:
    raw = str(value or "").replace("\\", "/")
    if not raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        return False
    parts = PurePosixPath(raw).parts
    return bool(parts) and all(part not in ("", ".", "..") for part in parts)


def validate_contract(contract: Any, schema: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return ["contract_not_object"]
    errors.extend(validate_schema_instance(contract, schema))
    exact_keys(
        contract,
        {"schema_version", "contract", "java", "cocos_creator", "android", "build_configs", "generated_exports", "policy"},
        "contract_root_keys",
        errors,
    )
    if contract.get("schema_version") != 1:
        errors.append("contract_schema_version")
    if contract.get("contract") != "mtr.android_build_toolchain":
        errors.append("contract_identity")

    java = contract.get("java", {})
    exact_keys(
        java,
        {
            "required_major", "required_version", "required_vendor", "required_arch",
            "approved_home", "required_files", "required_file_sha256",
            "forbidden_environment_overrides",
        },
        "java_contract_keys",
        errors,
    )
    if java.get("required_major") != 17:
        errors.append("required_java_major")
    if java.get("required_version") != "17.0.20":
        errors.append("required_java_version")
    if java.get("required_vendor") != "Eclipse Adoptium":
        errors.append("required_java_vendor")
    if java.get("required_arch") != "x86_64":
        errors.append("required_java_arch")
    if normalize_windows_path(java.get("approved_home")) != normalize_windows_path(APPROVED_HOME):
        errors.append("approved_java_home")
    if set(java.get("required_files", [])) != set(JDK_HASHES):
        errors.append("required_jdk_files")
    if java.get("required_file_sha256") != JDK_HASHES:
        errors.append("required_jdk_hashes")
    expected_overrides = {
        "JAVA_TOOL_OPTIONS",
        "JAVA_OPTS",
        "JDK_JAVA_OPTIONS",
        "_JAVA_OPTIONS",
        "GRADLE_OPTS",
        "ORG_GRADLE_PROJECT_org.gradle.java.home",
        "GRADLE_USER_HOME",
    }
    if set(java.get("forbidden_environment_overrides", [])) != expected_overrides:
        errors.append("forbidden_environment_overrides")

    cocos = contract.get("cocos_creator", {})
    exact_keys(cocos, {"version", "executable", "executable_sha256"}, "cocos_contract_keys", errors)
    if cocos.get("version") != "3.8.8":
        errors.append("cocos_version")
    if normalize_windows_path(cocos.get("executable")) != normalize_windows_path(APPROVED_COCOS):
        errors.append("cocos_executable")
    if cocos.get("executable_sha256") != COCOS_HASH:
        errors.append("cocos_hash")

    android = contract.get("android", {})
    exact_keys(
        android,
        {
            "sdk_path", "configured_api_level", "generated_compile_sdk",
            "build_tools_version", "ndk_version", "cmake_version",
            "gradle_wrapper_version", "gradle_distribution_url",
            "gradlew_bat_sha256", "gradle_wrapper_jar_sha256",
            "android_gradle_plugin_version",
        },
        "android_contract_keys",
        errors,
    )
    expected_android = {
        "configured_api_level": 35,
        "generated_compile_sdk": 36,
        "build_tools_version": "36.0.0",
        "ndk_version": "23.2.8568313",
        "cmake_version": "3.22.1",
        "gradle_wrapper_version": "8.11.1",
        "gradle_distribution_url": GRADLE_DISTRIBUTION_URL,
        "gradlew_bat_sha256": GRADLEW_BAT_HASH,
        "gradle_wrapper_jar_sha256": GRADLE_WRAPPER_JAR_HASH,
        "android_gradle_plugin_version": "8.10.1",
    }
    for key, value in expected_android.items():
        if android.get(key) != value:
            errors.append(f"android_contract:{key}")

    if tuple(contract.get("build_configs", [])) != CONFIGS:
        errors.append("build_config_registry")
    exports = contract.get("generated_exports", [])
    if not isinstance(exports, list) or len(exports) != len(CONFIGS):
        errors.append("generated_export_registry")
    else:
        seen: set[str] = set()
        for entry in exports:
            if not exact_keys(entry, {"config", "output_name", "project"}, "generated_export_keys", errors):
                continue
            config_name = entry.get("config")
            if config_name not in OUTPUTS or config_name in seen:
                errors.append("generated_export_config")
                continue
            seen.add(config_name)
            expected_output = OUTPUTS[config_name]
            expected_project = f"build/{expected_output}/proj"
            if entry.get("output_name") != expected_output:
                errors.append(f"generated_export_output:{config_name}")
            if not project_path_is_contained(entry.get("project")):
                errors.append(f"generated_export_project_escape:{config_name}")
            if normalize_project_path(entry.get("project")) != expected_project:
                errors.append(f"generated_export_project:{config_name}")
        if seen != set(CONFIGS):
            errors.append("generated_export_coverage")

    policy = contract.get("policy", {})
    exact_keys(
        policy,
        {"configured_java_only", "ambient_fallback", "global_environment_mutation", "fresh_export_validation"},
        "policy_contract_keys",
        errors,
    )
    if policy != {
        "configured_java_only": True,
        "ambient_fallback": False,
        "global_environment_mutation": False,
        "fresh_export_validation": "DEFERRED_TO_FIRST_ANDROID_P4",
    }:
        errors.append("toolchain_policy")
    return errors


def validate_config(config: Any, contract: dict[str, Any], expected_name: str) -> list[str]:
    errors: list[str] = []
    if expected_name not in contract.get("build_configs", []):
        errors.append("config_not_registered")
    if not isinstance(config, dict) or config.get("platform") != "android":
        return errors + ["config_platform"]
    if config.get("buildPath") != "project://build":
        errors.append("config_build_path")
    if config.get("outputName") != OUTPUTS[expected_name]:
        errors.append("config_output_name")
    packages = config.get("packages")
    android = packages.get("android", {}) if isinstance(packages, dict) else {}
    if not isinstance(android, dict):
        android = {}
    java_home = android.get("javaHome")
    java_path = android.get("javaPath")
    approved_home = contract.get("java", {}).get("approved_home")
    if normalize_windows_path(java_home) != normalize_windows_path(approved_home):
        errors.append("config_java_home_not_approved")
    expected_bin = f"{java_home}\\bin" if isinstance(java_home, str) and java_home else ""
    if normalize_windows_path(java_path) != normalize_windows_path(expected_bin):
        errors.append("config_java_path_mismatch")
    android_contract = contract.get("android", {})
    if normalize_windows_path(android.get("sdkPath")) != normalize_windows_path(android_contract.get("sdk_path")):
        errors.append("config_sdk_path")
    expected_ndk = f"{android_contract.get('sdk_path')}\\ndk\\{android_contract.get('ndk_version')}"
    if normalize_windows_path(android.get("ndkPath")) != normalize_windows_path(expected_ndk):
        errors.append("config_ndk_path")
    if android.get("apiLevel") != android_contract.get("configured_api_level"):
        errors.append("config_api_level")
    return errors


def run_negative_matrix(
    contract: dict[str, Any], schema: dict[str, Any], base_config: dict[str, Any]
) -> tuple[list[str], int]:
    failures: list[str] = []
    case_count = 0

    def config_case(name: str, candidate: dict[str, Any], expected_error: str) -> None:
        nonlocal case_count
        case_count += 1
        if expected_error not in validate_config(candidate, contract, "build-android.json"):
            failures.append(f"negative_case_false_green:{name}")

    def contract_case(name: str, candidate: dict[str, Any], expected_error: str) -> None:
        nonlocal case_count
        case_count += 1
        if expected_error not in validate_contract(candidate, schema):
            failures.append(f"negative_case_false_green:{name}")

    missing_home = copy.deepcopy(base_config)
    del missing_home["packages"]["android"]["javaHome"]
    config_case("missing_java_home", missing_home, "config_java_home_not_approved")

    path_mismatch = copy.deepcopy(base_config)
    path_mismatch["packages"]["android"]["javaPath"] = r"C:\unexpected\bin"
    config_case("java_path_mismatch", path_mismatch, "config_java_path_mismatch")

    java_21 = copy.deepcopy(base_config)
    java_21["packages"]["android"]["javaHome"] = r"C:\Program Files\Eclipse Adoptium\jdk-21"
    java_21["packages"]["android"]["javaPath"] = java_21["packages"]["android"]["javaHome"] + r"\bin"
    config_case("configured_java_21", java_21, "config_java_home_not_approved")

    wrong_platform = copy.deepcopy(base_config)
    wrong_platform["platform"] = "web-mobile"
    config_case("wrong_platform", wrong_platform, "config_platform")

    wrong_api = copy.deepcopy(base_config)
    wrong_api["packages"]["android"]["apiLevel"] = 34
    config_case("wrong_api", wrong_api, "config_api_level")

    wrong_sdk = copy.deepcopy(base_config)
    wrong_sdk["packages"]["android"]["sdkPath"] = r"C:\unexpected-sdk"
    config_case("wrong_sdk", wrong_sdk, "config_sdk_path")

    wrong_output = copy.deepcopy(base_config)
    wrong_output["outputName"] = "android-unvalidated"
    config_case("wrong_output_name", wrong_output, "config_output_name")

    bad_major = copy.deepcopy(contract)
    bad_major["java"]["required_major"] = 21
    contract_case("required_major", bad_major, "required_java_major")

    bad_version = copy.deepcopy(contract)
    bad_version["java"]["required_version"] = "17.0.19"
    contract_case("required_version", bad_version, "required_java_version")

    bad_hash = copy.deepcopy(contract)
    bad_hash["java"]["required_file_sha256"][r"bin\java.exe"] = "0" * 64
    contract_case("jdk_hash", bad_hash, "required_jdk_hashes")

    fallback = copy.deepcopy(contract)
    fallback["policy"]["ambient_fallback"] = True
    contract_case("ambient_fallback", fallback, "toolchain_policy")

    escape = copy.deepcopy(contract)
    escape["generated_exports"][0]["project"] = "../outside-project"
    contract_case("generated_project_escape", escape, "generated_export_project_escape:build-android.json")

    mapping = copy.deepcopy(contract)
    mapping["generated_exports"][0]["project"] = "build/android-unvalidated/proj"
    contract_case("generated_project_mapping", mapping, "generated_export_project:build-android.json")

    extra = copy.deepcopy(contract)
    extra["unexpected"] = True
    case_count += 1
    if not any(error.startswith("schema:$:additional:unexpected") for error in validate_contract(extra, schema)):
        failures.append("negative_case_false_green:schema_additional_property")

    export_extra = copy.deepcopy(contract)
    export_extra["generated_exports"][0]["unexpected"] = True
    case_count += 1
    if not any("additional:unexpected" in error for error in validate_contract(export_extra, schema)):
        failures.append("negative_case_false_green:schema_nested_additional_property")
    return failures, case_count


def require_marker(text: str, marker: str, code: str, errors: list[str]) -> None:
    if marker not in text:
        errors.append(code)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    paths = {
        "contract": root / "tools/codex/android-build-toolchain.contract.json",
        "schema": root / "tools/codex/android-build-toolchain.contract.schema.json",
        "module": root / "tools/codex/MtrAndroidBuildToolchain.psm1",
        "preflight": root / "tools/codex/Test-MtrAndroidBuildToolchain.ps1",
        "behavioral": root / "tools/codex/test-android-build-toolchain.ps1",
        "build_wrapper": root / "tools/Run-MtrCocosBuild.ps1",
        "entrypoint": root / "tools/codex/MtrEntrypoint.psm1",
        "legacy_probe": root / "tools/codex/Test-MtrAndroidToolchain.ps1",
        "gate": root / "tools/codex/quality-gate/static-gates.json",
    }
    errors: list[str] = []
    for label, path in paths.items():
        if not path.is_file():
            errors.append(f"missing_file:{label}")
    for config_name in CONFIGS:
        if not (root / config_name).is_file():
            errors.append(f"missing_file:{config_name}")
    if errors:
        print(json.dumps({"errors": sorted(errors), "status": "FAIL"}, sort_keys=True))
        return 1

    try:
        contract = load_json(paths["contract"])
        schema = load_json(paths["schema"])
        gate = load_json(paths["gate"])
        configs = {name: load_json(root / name) for name in CONFIGS}
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"errors": [f"json_error:{exc}"], "status": "FAIL"}, sort_keys=True))
        return 1

    errors.extend(validate_contract(contract, schema))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("schema_draft")
    if schema.get("additionalProperties") is not False:
        errors.append("schema_root_additional_properties")
    if schema.get("properties", {}).get("contract", {}).get("const") != "mtr.android_build_toolchain":
        errors.append("schema_identity")
    generated_schema = schema.get("properties", {}).get("generated_exports", {}).get("items", {})
    if set(generated_schema.get("required", [])) != {"config", "output_name", "project"}:
        errors.append("schema_generated_export_binding")
    for name, config in configs.items():
        errors.extend(f"{name}:{error}" for error in validate_config(config, contract, name))

    arm_android = configs["build-android.json"]["packages"]["android"]
    emulator_android = configs["build-android-emulator.json"]["packages"]["android"]
    for key in ("javaHome", "javaPath", "sdkPath", "ndkPath", "apiLevel"):
        if arm_android.get(key) != emulator_android.get(key):
            errors.append(f"config_parity:{key}")

    negative_failures, negative_count = run_negative_matrix(
        contract, schema, configs["build-android.json"]
    )
    errors.extend(negative_failures)

    module = paths["module"].read_text(encoding="utf-8")
    preflight = paths["preflight"].read_text(encoding="utf-8")
    behavioral = paths["behavioral"].read_text(encoding="utf-8")
    wrapper = paths["build_wrapper"].read_text(encoding="utf-8")
    entrypoint = paths["entrypoint"].read_text(encoding="utf-8")
    legacy = paths["legacy_probe"].read_text(encoding="utf-8")
    for marker, code in (
        ("configured-java-only-no-path-or-java-home-fallback", "module_no_fallback_marker"),
        ("contract-java-policy-not-approved", "module_runtime_java_policy_pin"),
        ("contract-cocos-policy-not-approved", "module_runtime_cocos_policy_pin"),
        ("contract-android-policy-not-approved", "module_runtime_android_policy_pin"),
        ("configured-java-version-mismatch", "module_java_exact_version"),
        ("configured-jdk-file-hash-mismatch:", "module_jdk_hash_binding"),
        ("environment-override-active:", "module_override_guard"),
        ("if ($null -ne $value)", "module_defined_override_guard"),
        ("Get-MtrAndroidToolchainAuthoritativeUserProfile", "module_authoritative_user_profile"),
        ("configured-java-user-home-mismatch", "module_java_user_home_binding"),
        ("platforms\\android-$generatedCompileSdk", "module_generated_compile_platform"),
        ("config-output-name-not-approved", "module_output_name_binding"),
        ("generated-export-project-escapes-root", "module_generated_project_containment"),
        ("generated-export-reparse-point-not-allowed", "module_generated_project_reparse_guard"),
        ("generated-export-incomplete", "module_partial_export_guard"),
        ("generated-property-assignment-count:", "module_duplicate_property_guard"),
        ("generated-sdk-dir-assignment-count", "module_duplicate_sdk_guard"),
        ("java.util.Properties accepts", "module_java_properties_separator_guard"),
        ("Test-MtrAndroidToolchainEscapedPropertyKey", "module_escaped_property_key_guard"),
        ("gradle-property-continuation-not-allowed", "module_root_gradle_continuation_guard"),
        ("generated-sdk-path-mismatch", "module_generated_sdk_binding"),
        ("generated-gradle-wrapper-version-mismatch", "module_generated_wrapper_check"),
        ("generated-gradle-distribution-url-mismatch", "module_exact_distribution_url"),
        ("generated-gradlew-bat-hash-mismatch", "module_gradlew_hash_binding"),
        ("generated-wrapper-jar-hash-mismatch", "module_wrapper_jar_hash_binding"),
        ("generated-gradle-daemon-jvm-criteria-not-allowed", "module_daemon_jvm_criteria_guard"),
        ("generated-compile-sdk-mismatch", "module_generated_compile_sdk_check"),
        ("generated-target-sdk-mismatch", "module_generated_target_sdk_check"),
        ("generated-build-tools-version-mismatch", "module_generated_build_tools_check"),
        ("generated-ndk-version-mismatch", "module_generated_ndk_check"),
        ("android-ndk-metadata-mismatch", "module_ndk_metadata_check"),
        ("android-cmake-metadata-mismatch", "module_cmake_metadata_check"),
        ("cocos-executable-hash-mismatch", "module_cocos_hash_binding"),
        ("generated-gradle-java-home-override-active", "module_generated_gradle_override_check"),
        ("contract-path-not-canonical", "module_canonical_contract_path"),
        ("Get-MtrAndroidToolchainAmbientJava", "module_ambient_report"),
    ):
        require_marker(module, marker, code, errors)
    require_marker(preflight, "if ($result.status -ne 'PASS') { exit 2 }", "preflight_nonzero_default", errors)
    for marker in (
        "missing_configured_jdk_never_falls_back",
        "configured_java_21_cannot_replace_approved_patch",
        "contract_cannot_redefine_approved_jdk",
        "exact_jdk_version_mismatch_fails",
        "java_scope_binds_before_child_and_restores_after_success",
        "java_scope_restores_after_child_throw",
        "gradle_user_home_override_fails",
        "whitespace_gradle_user_home_override_fails",
        "userprofile_override_fails_and_authoritative_gradle_home_remains_bound",
        "java_opts_override_fails",
        "clean_checkout_without_generated_export_passes_not_present",
        "config_output_name_is_bound_to_generated_project",
        "generated_project_cannot_escape_project_root",
        "generated_project_reparse_point_fails",
        "generated_compile_sdk_mismatch_fails",
        "duplicate_generated_property_assignment_fails",
        "colon_delimited_generated_overrides_fail",
        "bare_and_escaped_generated_property_keys_fail",
        "root_gradle_property_continuation_fails",
        "lone_cr_generated_overrides_fail",
        "partial_existing_generated_export_fails_before_cocos",
        "generated_daemon_jvm_criteria_fails",
        "generated_gradlew_launcher_hash_mismatch_fails",
        "generated_distribution_url_must_match_exact_contract",
        "exact_jdk_file_hash_mismatch_fails",
        "preflight_only_rejects_unapproved_cocos_override",
        "wrapper_log_paths_are_unique_and_reuse_fails_closed",
        "caller_environment_is_unchanged",
    ):
        require_marker(behavioral, marker, f"behavioral_test_marker:{marker}", errors)

    real_branch = wrapper.find("if ($isAndroidBuild -and -not $ValidateContentIdentityOnly)")
    assert_index = wrapper.find("$androidToolchainPreflight = Assert-MtrAndroidBuildToolchain", real_branch)
    check_index = wrapper.find("-CheckGeneratedExport", assert_index)
    cocos_index = wrapper.find("$run = if ($isAndroidBuild)", assert_index)
    if min(real_branch, assert_index, check_index, cocos_index) < 0 or not (
        real_branch < assert_index < check_index < cocos_index
    ):
        errors.append("build_wrapper_preflight_order")
    for marker, code in (
        ("[switch]$ValidateAndroidToolchainOnly", "build_wrapper_preflight_switch"),
        ("Invoke-MtrAndroidBuildJavaScope -Toolchain $androidToolchainPreflight", "build_wrapper_cocos_java_binding"),
        ("Android build Cocos executable is not contract-approved", "build_wrapper_cocos_identity_binding"),
        ("generatedEvidenceScope = 'EXISTING_EXPORT_IF_PRESENT_NO_BUILD'", "build_wrapper_preflight_scope"),
        ("$androidProjRoot = [string]$androidToolchainPreflight.generatedExport.project", "build_wrapper_project_binding"),
        ("-RequireGeneratedExport", "build_wrapper_post_export_check"),
        ("-Dorg.gradle.java.home=$javaHome", "build_wrapper_gradle_java_binding"),
        ("Invoke-MtrAndroidBuildJavaScope `", "build_wrapper_gradle_java_scope"),
        ("Content-only validation remains host-independent", "content_only_boundary"),
        ("$run.completedBySuccessPattern", "build_wrapper_current_run_success_binding"),
        ("[Guid]::NewGuid()", "build_wrapper_unique_log_names"),
        ("Build run log path already exists; choose a unique path", "build_wrapper_reused_log_rejected"),
    ):
        require_marker(wrapper, marker, code, errors)
    if "$evidenceText -match" in wrapper:
        errors.append("build_wrapper_unbounded_success_log_scan")
    for marker, code in (
        ("$successLogStates", "entrypoint_success_log_baseline"),
        ("$state.offset", "entrypoint_success_log_cursor"),
        ("$stream.Length", "entrypoint_bounded_length_snapshot"),
        ("$exited -and $process.ExitCode -ne 0", "entrypoint_nonzero_precedence"),
        ("staleSuccessRejected", "entrypoint_stale_success_test"),
        ("currentSuccessAccepted", "entrypoint_current_success_test"),
        ("nonzeroExitPrecedence", "entrypoint_nonzero_success_test"),
        ("boundedSuccessLogOverflowRejected", "entrypoint_bounded_overflow_test"),
    ):
        require_marker(entrypoint, marker, code, errors)
    for marker, code in (
        ("function Invoke-MtrAndroidBuildJavaScope", "module_java_scope"),
        ("$env:JAVA_HOME = $previousJavaHome", "module_java_scope_restore"),
        ("finally", "module_java_scope_finally"),
    ):
        require_marker(module, marker, code, errors)
    if "elseif ($run.logicalExitCode -ne 0)" not in wrapper or re.search(r"else\s*\{\s*1\s*\}", wrapper) is None:
        errors.append("build_wrapper_post_stage_nonzero_report")
    if "Resolve-MtrToolCandidate -Name 'java'" in legacy:
        errors.append("legacy_probe_path_first_java")
    for marker in (
        "MtrAndroidBuildToolchain.psm1",
        "androidBuildToolchain = $androidBuildToolchain",
        "ambientJava = $androidBuildToolchain.ambientJava",
    ):
        require_marker(legacy, marker, f"legacy_probe_marker:{marker}", errors)

    steps = gate.get("steps", [])
    tc_steps = [step for step in steps if step.get("id") == "android-build-toolchain-contracts"]
    if len(tc_steps) != 1:
        errors.append("static_gate_step_count")
    else:
        step = tc_steps[0]
        expected_arguments = ["-B", "tools/codex/validate_android_build_toolchain.py", "--project-root", "."]
        if step.get("mandatory") is not True or step.get("enabled") is not True:
            errors.append("static_gate_step_disabled")
        if step.get("executable") != "python" or step.get("arguments") != expected_arguments:
            errors.append("static_gate_step_command")
        if step.get("expected_exit_codes") != [0]:
            errors.append("static_gate_step_exit_codes")

    result = {
        "config_count": len(configs),
        "errors": sorted(set(errors)),
        "host_paths_checked": False,
        "negative_cases": negative_count,
        "schema_applied": True,
        "static_gate_steps": len(steps),
        "status": "PASS" if not errors else "FAIL",
        "t4_fresh_export": "DEFERRED_TO_FIRST_ANDROID_P4",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
