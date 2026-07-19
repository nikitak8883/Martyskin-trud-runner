#!/usr/bin/env python3
"""Deterministic M01.2 contract, registry, adapter, and fixture self-test."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


LIBRARY_ROOT = Path(__file__).resolve().parents[1]
ADAPTERS_DIR = LIBRARY_ROOT / "adapters"
SCHEMAS_DIR = LIBRARY_ROOT / "schemas"
FIXTURES_DIR = LIBRARY_ROOT / "fixtures" / "quality_evidence"
PROJECT_ROOT = LIBRARY_ROOT.parents[3]
sys.path.insert(0, str(ADAPTERS_DIR))

from quality_evidence_adapter import (  # noqa: E402
    AdapterError,
    HANDLERS,
    adapt_report,
    validate_envelope,
)


class TestFailure(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TestFailure(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TestFailure(f"Cannot parse {path}: {exc}") from exc
    require(isinstance(document, dict), f"Top-level JSON must be an object: {path}")
    return document


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def validate_schema_documents() -> dict[str, Any]:
    expected = {
        "quality_evidence_envelope.schema.json": "https://schemas.mtr.local/quality/v1/quality-evidence-envelope.schema.json",
        "quality_adapter_registry.schema.json": "https://schemas.mtr.local/quality/v1/quality-adapter-registry.schema.json",
        "quality_fixture_suite.schema.json": "https://schemas.mtr.local/quality/v1/quality-fixture-suite.schema.json",
        "quality_gate_config.schema.json": "https://schemas.mtr.local/quality/v1/quality-gate-config.schema.json",
        "quality_gate_report.schema.json": "https://schemas.mtr.local/quality/v1/quality-gate-report.schema.json",
    }
    found = {path.name: load_json(path) for path in sorted(SCHEMAS_DIR.glob("*.schema.json"))}
    require(set(found) == set(expected), f"Canonical schema set drift: {sorted(found)}")
    ids: list[str] = []
    for name, schema in found.items():
        require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"Wrong draft in {name}")
        require(schema.get("$id") == expected[name], f"Wrong canonical $id in {name}")
        require(schema.get("type") == "object", f"Top-level type must be object in {name}")
        require(schema.get("additionalProperties") is False, f"Top-level schema must reject unknown fields in {name}")
        ids.append(schema["$id"])
    require(len(ids) == len(set(ids)), "Canonical schema $id values must be unique")
    require(len(found["quality_evidence_envelope.schema.json"].get("allOf", [])) == 2, "Envelope schema must encode PASS and non-PASS invariants")
    fixture_expected = found["quality_fixture_suite.schema.json"]["$defs"]["case"]["properties"]["expected"]
    require(len(fixture_expected.get("allOf", [])) == 2, "Fixture schema must conditionally require status/error_code")
    return {"count": len(found), "ids": ids}


def validate_registry() -> tuple[dict[str, Any], dict[str, Any]]:
    path = ADAPTERS_DIR / "quality_adapter_registry.json"
    registry = load_json(path)
    require(registry.get("schema_version") == 1, "Registry schema_version must be 1")
    require(registry.get("contract") == "mtr.quality_adapter_registry", "Registry contract mismatch")
    require(registry.get("namespace") == "https://schemas.mtr.local/quality/v1/", "Registry namespace mismatch")
    adapters = registry.get("adapters")
    require(isinstance(adapters, list) and adapters, "Registry adapters must be a non-empty list")
    ids = [entry.get("id") for entry in adapters]
    sources = [entry.get("source_schema") for entry in adapters]
    require(len(ids) == len(set(ids)), "Adapter ids must be unique")
    require(len(sources) == len(set(sources)), "Source schemas must map to exactly one registry entry")
    support_counts = {kind: 0 for kind in ("active", "historical_only", "data_not_quality_evidence")}
    active_handlers: set[str] = set()
    for entry in adapters:
        require(isinstance(entry, dict), "Every registry entry must be an object")
        support = entry.get("support")
        require(support in support_counts, f"Unknown support state: {support}")
        support_counts[support] += 1
        require(entry.get("version") == "1.0.0", f"Unexpected adapter version: {entry.get('id')}")
        if support == "active":
            handler = entry.get("handler")
            require(handler in HANDLERS, f"Missing implemented handler: {handler}")
            require(isinstance(entry.get("strict_requirements"), list) and entry["strict_requirements"], f"Missing strict requirements: {entry.get('id')}")
            active_handlers.add(handler)
        else:
            require("handler" not in entry, f"Non-active source cannot expose a handler: {entry.get('id')}")
    require(support_counts == {"active": 11, "historical_only": 5, "data_not_quality_evidence": 2}, f"Registry classification drift: {support_counts}")
    require(active_handlers == set(HANDLERS), f"Registry/code handler mismatch: registry={sorted(active_handlers)}, code={sorted(HANDLERS)}")
    return registry, {"entry_count": len(adapters), "support_counts": support_counts, "active_handler_count": len(active_handlers)}


def validate_fixture_shape(suite: dict[str, Any], expected_kind: str) -> None:
    require(suite.get("schema_version") == 1, f"{expected_kind} fixture schema_version must be 1")
    require(suite.get("contract") == "mtr.quality_fixture_suite", f"{expected_kind} fixture contract mismatch")
    require(suite.get("suite_kind") == expected_kind, f"Fixture suite kind mismatch: {expected_kind}")
    require(isinstance(suite.get("defaults"), dict), f"{expected_kind} defaults must be an object")
    cases = suite.get("cases")
    require(isinstance(cases, list) and cases, f"{expected_kind} cases must be non-empty")
    case_ids = [case.get("case_id") for case in cases]
    require(len(case_ids) == len(set(case_ids)), f"Duplicate case ids in {expected_kind} fixtures")
    for case in cases:
        require(set(case).issubset({"case_id", "description", "input", "context", "expected"}), f"Unknown fixture field in {case.get('case_id')}")
        require(all(key in case for key in ("case_id", "description", "input", "expected")), f"Incomplete fixture case: {case}")
        require(case["expected"].get("outcome") in {"envelope", "error"}, f"Invalid expected outcome: {case['case_id']}")


def run_fixture_suite(suite: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    envelopes: list[dict[str, Any]] = []
    for case in suite["cases"]:
        context = deep_merge(suite["defaults"], case.get("context", {}))
        context["evidence_id"] = case["case_id"]
        expected = case["expected"]
        if expected["outcome"] == "error":
            try:
                adapt_report(case["input"], context)
            except AdapterError as exc:
                require(exc.code == expected["error_code"], f"{case['case_id']}: expected error {expected['error_code']}, got {exc.code}")
                results.append({"case_id": case["case_id"], "outcome": "error", "error_code": exc.code, "passed": True})
            else:
                raise TestFailure(f"{case['case_id']}: expected AdapterError")
            continue

        envelope = adapt_report(case["input"], context)
        validate_envelope(envelope)
        second = adapt_report(copy.deepcopy(case["input"]), copy.deepcopy(context))
        require(second == envelope, f"{case['case_id']}: adapter output is not deterministic")
        require(envelope["status"] == expected["status"], f"{case['case_id']}: expected {expected['status']}, got {envelope['status']}")
        actual_codes = {finding["code"] for finding in envelope["findings"]}
        expected_codes = set(expected.get("finding_codes", []))
        if expected_codes:
            require(expected_codes.issubset(actual_codes), f"{case['case_id']}: missing findings {sorted(expected_codes - actual_codes)}")
        else:
            require(not actual_codes, f"{case['case_id']}: unexpected findings {sorted(actual_codes)}")
        results.append({"case_id": case["case_id"], "outcome": "envelope", "status": envelope["status"], "finding_codes": sorted(actual_codes), "passed": True})
        envelopes.append(envelope)
    return results, envelopes


def run_guard_mutation_tests(reference: dict[str, Any]) -> list[dict[str, Any]]:
    mutations: list[tuple[str, dict[str, Any], str]] = []
    unknown_field = copy.deepcopy(reference)
    unknown_field["unexpected"] = True
    mutations.append(("reject_unknown_top_level_field", unknown_field, "INVALID_ENVELOPE"))
    false_pass = copy.deepcopy(reference)
    false_pass["fresh"] = False
    mutations.append(("reject_pass_when_stale", false_pass, "INVALID_ENVELOPE"))
    missing_finding = copy.deepcopy(reference)
    missing_finding["status"] = "FAIL"
    mutations.append(("reject_fail_without_blocking_finding", missing_finding, "INVALID_ENVELOPE"))
    results: list[dict[str, Any]] = []
    for name, document, expected_code in mutations:
        try:
            validate_envelope(document)
        except AdapterError as exc:
            require(exc.code == expected_code, f"{name}: unexpected error {exc.code}")
            results.append({"case_id": name, "error_code": exc.code, "passed": True})
        else:
            raise TestFailure(f"{name}: invalid envelope was accepted")
    return results


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_representative_reports() -> dict[str, Any]:
    """Prove adapter compatibility with current report shapes, not evidence freshness."""

    anchor_path = PROJECT_ROOT / "docs/global_modernization/v3/M00/source_content_manifest.json"
    anchor = load_json(anchor_path)
    source = {"commit": anchor["source_commit"], "content_version": anchor["content_version"]}
    samples = [
        ("assets", "docs/qa/evidence/20260714_two_cycle_resume/final_gate_static/assets.json", "tools/validate-assets.py", "static", "project-source", ["--fail-on-white-matte"]),
        ("skins", "docs/qa/evidence/20260714_two_cycle_resume/final_gate_static/skin_bonus_matrix.json", "tools/validate-skin-bonus-matrix.py", "static", "project-source", ["--fail-on-warnings"]),
        ("ui-ir", "docs/qa/evidence/20260714_two_cycle_resume/final_gate_static/ui_ir.json", "tools/validate-ui-ir.py", "static", "project-source", []),
        ("android-toolchain", "docs/qa/evidence/20260630_next_big_patch/android_toolchain_resume_20260701.json", "tools/codex/Test-MtrAndroidToolchain.ps1", "android-emulator", "emulator-5554", ["-FailOnNotReady"]),
        ("android-matrix", "docs/qa/evidence/20260714_two_cycle_resume/cycle2_android_matrix/android_matrix_cycle2_summary.json", "tools/codex/Run-MtrAndroidEmulatorMatrixQa.ps1", "android-emulator", "emulator-5554", []),
        ("android-interaction", "docs/qa/evidence/20260714_two_cycle_resume/cycle2_android_interaction_soak/android_interaction_cycle2_summary.json", "tools/codex/Run-MtrAndroidEmulatorInteractionQa.ps1", "android-emulator", "emulator-5554", []),
        ("web-matrix", "docs/qa/evidence/20260714_two_cycle_resume/cycle2_web/web_matrix_cycle2_summary.json", "tools/codex/web_matrix_playwright_function.js", "web", "http://127.0.0.1:9491", []),
        ("web-soak", "docs/qa/evidence/20260714_two_cycle_resume/cycle2_web/web_soak_cycle2_summary.json", "tools/codex/web_soak_playwright_function.js", "web", "http://127.0.0.1:9491", []),
        ("source-fingerprint", "docs/global_modernization/v3/M00/source_content_manifest.json", "tools/codex/build_source_content_manifest.py", "source", "source-tree", []),
    ]
    results: list[dict[str, Any]] = []
    for sample_id, report_rel, tool_rel, platform, identity, flags in samples:
        report_path = PROJECT_ROOT / report_rel
        tool_path = PROJECT_ROOT / tool_rel
        require(report_path.is_file(), f"Missing representative report: {report_rel}")
        require(tool_path.is_file(), f"Missing representative tool: {tool_rel}")
        context = {
            "evidence_id": f"shape-smoke.{sample_id}",
            "source_report": {"relative_path": report_rel, "sha256": sha256_file(report_path)},
            "source": source,
            "expected_source_commit": source["commit"],
            "target": {"platform": platform, "identity": identity, "profile": "compatibility-smoke"},
            "tool": {"relative_path": tool_rel, "sha256": sha256_file(tool_path), "command_id": f"shape-smoke.{sample_id}", "strict": True, "flags": flags},
            "timing": {"started_at": "2026-07-19T08:00:00Z", "finished_at": "2026-07-19T08:01:00Z"},
            "mandatory": True,
            "applicable": True,
            "fresh": True,
            "physical_device_authorized": False,
        }
        envelope = adapt_report(load_json(report_path), context)
        require(envelope["status"] == "PASS", f"Representative shape {sample_id} was not accepted: {envelope['status']}")
        results.append({"sample_id": sample_id, "source_schema": envelope["source_report"]["schema_name"], "status": envelope["status"]})
    return {
        "status": "PASS",
        "sample_count": len(results),
        "claim_scope": "shape_compatibility_only_not_freshness_or_current_product_qa",
        "results": results,
    }


def optional_json_schema_validation(
    registry: dict[str, Any],
    suites: list[dict[str, Any]],
    envelopes: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except ImportError:
        return {
            "status": "deferred_missing_pinned_dependency",
            "blocking": False,
            "reason": "M01.3 owns an isolated pinned Draft 2020-12 validator; global Python was not mutated.",
        }
    mapping = {
        "quality_adapter_registry.schema.json": [registry],
        "quality_fixture_suite.schema.json": suites,
        "quality_evidence_envelope.schema.json": envelopes,
    }
    checked = 0
    for schema_name, documents in mapping.items():
        validator = Draft202012Validator(load_json(SCHEMAS_DIR / schema_name))
        for document in documents:
            errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
            require(not errors, f"Draft 2020-12 validation failed for {schema_name}: {[error.message for error in errors]}")
            checked += 1
    return {"status": "pass", "blocking": False, "document_count": checked}


def main() -> int:
    try:
        schema_summary = validate_schema_documents()
        registry, registry_summary = validate_registry()
        positive = load_json(FIXTURES_DIR / "positive_cases.json")
        negative = load_json(FIXTURES_DIR / "negative_cases.json")
        validate_fixture_shape(positive, "positive")
        validate_fixture_shape(negative, "negative")
        positive_results, positive_envelopes = run_fixture_suite(positive)
        negative_results, negative_envelopes = run_fixture_suite(negative)
        require(all(item.get("status") == "PASS" for item in positive_results), "Every positive fixture must produce PASS")
        guard_results = run_guard_mutation_tests(positive_envelopes[0])
        representative_reports = validate_representative_reports()
        schema_engine = optional_json_schema_validation(registry, [positive, negative], positive_envelopes + negative_envelopes)
        summary = {
            "schema": "mtr.m01_2_contract_validation.v1",
            "status": "PASS",
            "schemas": schema_summary,
            "registry": registry_summary,
            "fixtures": {
                "positive_count": len(positive_results),
                "negative_count": len(negative_results),
                "positive_results": positive_results,
                "negative_results": negative_results,
            },
            "runtime_guard_mutations": guard_results,
            "representative_report_smoke": representative_reports,
            "deterministic_rerun_count": len(positive_results) + sum(1 for item in negative_results if item["outcome"] == "envelope"),
            "generic_json_schema_engine": schema_engine,
        }
    except (TestFailure, AdapterError) as exc:
        detail = exc.as_dict() if isinstance(exc, AdapterError) else {"message": str(exc)}
        print(json.dumps({"schema": "mtr.m01_2_contract_validation.v1", "status": "FAIL", "error": detail}, ensure_ascii=False, indent=2, sort_keys=True))
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
