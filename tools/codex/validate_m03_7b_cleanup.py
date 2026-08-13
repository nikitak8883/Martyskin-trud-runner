#!/usr/bin/env python3
"""Fail-closed M03.7B deletion, hidden-reference, and rollback validator."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def require(condition: bool, code: str, errors: list[str]) -> None:
    if not condition:
        errors.append(code)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def git_output(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    manifest_path = root / "docs/global_modernization/v3/M03/M03_7B_CLEANUP_MANIFEST.json"
    game_root_path = root / "assets/scripts/GameRoot.ts"
    lifecycle_path = root / "assets/scripts/qa/LifecycleEpoch.ts"
    adapter_path = root / "assets/scripts/qa/GameRootDevEventAdapter.ts"
    owner_path = root / "assets/scripts/gameplay/lifecycle/GameRuntimeLifecycleOwner.ts"
    reference_path = root / "docs/global_modernization/v4/library/reference/LifecycleEpoch.reference.ts"
    gate_path = root / "tools/codex/quality-gate/static-gates.json"
    validator_path = root / "tools/codex/validate_m03_7b_cleanup.py"
    errors: list[str] = []

    for path in (manifest_path, game_root_path, lifecycle_path, adapter_path, owner_path, reference_path, gate_path):
        require(path.is_file(), f"missing:{path.relative_to(root)}", errors)
    if errors:
        print(json.dumps({"errors": sorted(errors), "status": "FAIL"}, sort_keys=True))
        return 1

    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"errors": [f"invalid_manifest:{exc}"], "status": "FAIL"}, sort_keys=True))
        return 1

    require(manifest.get("schema_version") == 1, "manifest_schema_version", errors)
    require(manifest.get("contract") == "mtr.m03_7b_cleanup_manifest", "manifest_contract", errors)
    require(manifest.get("execution_unit") == "M03.7B", "manifest_execution_unit", errors)

    rollback = manifest.get("rollback", {})
    require(isinstance(rollback, dict), "rollback_not_object", errors)
    anchor = rollback.get("anchor_commit", "") if isinstance(rollback, dict) else ""
    prefix = rollback.get("project_prefix", "") if isinstance(rollback, dict) else ""
    blobs = rollback.get("pre_change_blobs", {}) if isinstance(rollback, dict) else {}
    require(bool(re.fullmatch(r"[0-9a-f]{40}", str(anchor))), "rollback_anchor_format", errors)
    require(isinstance(blobs, dict) and len(blobs) == 10, "rollback_blob_count", errors)

    repo = root
    while repo.parent != repo and not (repo / ".git").exists():
        repo = repo.parent
    require((repo / ".git").exists(), "git_root_not_found", errors)
    verified_blobs = 0
    if (repo / ".git").exists() and re.fullmatch(r"[0-9a-f]{40}", str(anchor)) and isinstance(blobs, dict):
        try:
            require(git_output(repo, "cat-file", "-t", str(anchor)) == "commit", "rollback_anchor_missing", errors)
            for relative, expected_blob in sorted(blobs.items()):
                require(bool(re.fullmatch(r"[0-9a-f]{40}", str(expected_blob))), f"rollback_blob_format:{relative}", errors)
                actual_blob = git_output(repo, "rev-parse", f"{anchor}:{prefix}{relative}")
                require(actual_blob == expected_blob, f"rollback_blob_mismatch:{relative}", errors)
                if actual_blob == expected_blob:
                    verified_blobs += 1
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            errors.append(f"rollback_git_error:{type(exc).__name__}:{exc}")

    game_root = game_root_path.read_text(encoding="utf-8")
    lifecycle = lifecycle_path.read_text(encoding="utf-8")
    adapter = adapter_path.read_text(encoding="utf-8")
    owner = owner_path.read_text(encoding="utf-8")
    reference = reference_path.read_text(encoding="utf-8")
    active_sources: list[tuple[Path, str]] = []
    for relative_root in manifest.get("active_hidden_reference_roots", []):
        scan_root = root / str(relative_root)
        require(scan_root.is_dir(), f"hidden_reference_root_missing:{relative_root}", errors)
        if scan_root.is_dir():
            for suffix in ("*.ts", "*.java", "*.kt", "*.cpp", "*.h"):
                for path in scan_root.rglob(suffix):
                    active_sources.append((path, path.read_text(encoding="utf-8", errors="replace")))

    legacy_patterns = {
        "guard_session_callback": r"\bguardSessionCallback\b",
        "lifecycle_capture": r"\b(?:public\s+)?capture\s*\(",
        "lifecycle_guard": r"\b(?:public\s+)?guard(?:<[^>]+>)?\s*\(",
    }
    hidden_hits: list[str] = []
    for path, source in active_sources:
        for label, pattern in legacy_patterns.items():
            if re.search(pattern, source):
                hidden_hits.append(f"{label}:{path.relative_to(root).as_posix()}")
    require(not hidden_hits, "active_hidden_legacy_references", errors)
    require("guardSessionCallback" not in adapter + game_root, "legacy_adapter_guard_present", errors)
    for source_name, source in (("runtime", lifecycle), ("reference", reference)):
        require(re.search(r"public\s+capture\s*\(", source) is None, f"legacy_capture_present:{source_name}", errors)
        require(re.search(r"public\s+guard(?:<|\s*\()", source) is None, f"legacy_guard_present:{source_name}", errors)

    direct_route_patterns = (
        r"scheduleSessionOnce\('qa\.obstacle-spawn',\s*\(\)\s*=>",
        r"scheduleSessionOnce\('qa\.bonus-spawn',\s*\(\)\s*=>",
        r"scheduleSessionOnce\('qa\.pause-after-start',\s*\(\)\s*=>",
        r"scheduleSessionOnce\('qa\.collision-matrix',\s*\(\)\s*=>",
        r"scheduleSessionOnce\('qa\.powerup-lifecycle',\s*\(\)\s*=>",
        r"scheduleSessionOnce\(\s*'qa\.runtime-ownership',\s*\(\)\s*=>",
        r"scheduleSessionOnce\('qa\.bonus-spawn-retry',\s*\(\)\s*=>",
    )
    direct_routes = sum(len(re.findall(pattern, game_root, re.DOTALL)) for pattern in direct_route_patterns)
    expected = manifest.get("expected", {})
    require(direct_routes == expected.get("direct_session_owned_routes"), "direct_session_owned_routes", errors)
    require(game_root.count("this.scheduleOnce(") == expected.get("game_root_direct_schedule_once"), "direct_schedule_once_count", errors)
    require(game_root.count("scheduleSessionOnce(") == expected.get("game_root_session_schedule_routes"), "session_schedule_route_count", errors)
    require("scope === 'session' && epoch !== this.options.getEpoch()" in owner, "owner_stale_epoch_guard_missing", errors)
    require("this.runtimeLifecycle.scheduleOnce(key, scope, callback, delaySeconds)" in game_root, "owner_schedule_bridge_missing", errors)
    require(game_root.count("this.runtimeLifecycle.cancelSession(") == 2, "owner_cancel_route_count", errors)
    require(game_root.count("this.runtimeLifecycle.destroy(") == 1, "owner_destroy_route_count", errors)

    gate = load_json(gate_path)
    steps = gate.get("steps", [])
    cleanup_steps = [step for step in steps if step.get("id") == "m03-7b-cleanup-contracts"]
    require(len(cleanup_steps) == 1, "static_gate_step_count", errors)
    if cleanup_steps:
        step = cleanup_steps[0]
        require(step.get("mandatory") is True, "static_gate_not_mandatory", errors)
        require(step.get("enabled") is True, "static_gate_not_enabled", errors)
        require(step.get("executable") == "python", "static_gate_executable", errors)
        require(
            step.get("arguments") == ["-B", "tools/codex/validate_m03_7b_cleanup.py", "--project-root", "."],
            "static_gate_arguments",
            errors,
        )
        require(step.get("expected_exit_codes") == [0], "static_gate_exit_codes", errors)

    current_hashes = {
        str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest().upper()
        for path in (game_root_path, lifecycle_path, adapter_path, owner_path, reference_path, validator_path)
    }
    result = {
        "active_hidden_legacy_references": hidden_hits,
        "direct_session_owned_routes": direct_routes,
        "errors": sorted(errors),
        "implementation_sha256": current_hashes,
        "rollback_anchor": anchor,
        "rollback_blobs_verified": verified_blobs,
        "static_gate_steps": len(steps),
        "status": "PASS" if not errors else "FAIL",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
