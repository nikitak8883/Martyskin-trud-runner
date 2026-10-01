"""Exact immutable rollback proof in monorepo or source-only Git history."""
from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any, Callable


def verify_rollback_proof(
    rollback: dict[str, Any], *, projection: dict[str, Any] | None,
    manifest_sha256_utf8_lf: str, source_only: bool, git_query: Callable[..., str],
) -> dict[str, Any]:
    result: dict[str, Any] = {"mode": "unverified", "anchor": None, "verified_blobs": 0, "errors": []}
    errors = result["errors"]
    anchor, prefix, blobs = (rollback.get(key) for key in ("anchor_commit", "project_prefix", "pre_change_blobs"))
    valid_sha = lambda value: isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None
    valid_relative = lambda value: (isinstance(value, str) and bool(value) and "\\" not in value and ":" not in value
                                    and not PurePosixPath(value).is_absolute()
                                    and all(part not in {"", ".", ".."} for part in value.split("/")))
    if not valid_sha(anchor) or not isinstance(prefix, str) or not prefix.endswith("/") or not valid_relative(prefix[:-1]):
        errors.append("rollback_identity_invalid")
        return result
    if not isinstance(blobs, dict) or len(blobs) != 10 or any(not valid_relative(p) or not valid_sha(h) for p, h in blobs.items()):
        errors.append("rollback_blob_set_invalid")
        return result
    try:
        try:
            kind = git_query("cat-file", "-t", anchor)
        except RuntimeError:
            kind = None
        if kind == "commit":
            mode = "original-monorepo"
        elif kind is not None:
            errors.append("rollback_anchor_not_commit")
            return result
        else:
            if not source_only:
                errors.append("rollback_original_anchor_unavailable")
                return result
            if not isinstance(projection, dict):
                errors.append("rollback_projection_missing")
                return result
            p = projection
            if (p.get("schema_version") != 1 or p.get("contract") != "mtr.m03_7b_source_rollback_projection"
                    or p.get("legacy_anchor") != anchor or p.get("legacy_project_prefix") != prefix
                    or p.get("cleanup_manifest_sha256_utf8_lf") != manifest_sha256_utf8_lf
                    or p.get("pre_change_blobs") != blobs):
                errors.append("rollback_projection_identity_mismatch")
                return result
            if (not valid_sha(p.get("source_anchor")) or not valid_sha(p.get("source_tree"))
                    or p.get("source_tree") != p.get("legacy_project_tree")):
                errors.append("rollback_projection_tree_identity_mismatch")
                return result
            anchor, prefix = p["source_anchor"], ""
            if git_query("cat-file", "-t", anchor) != "commit":
                errors.append("rollback_projection_anchor_not_commit")
                return result
            if git_query("rev-parse", f"{anchor}^{{tree}}") != p["source_tree"]:
                errors.append("rollback_projection_tree_mismatch")
                return result
            # A floating/divergent lookalike checkpoint is not accepted.
            git_query("merge-base", "--is-ancestor", anchor, "HEAD")
            mode = "verified-source-projection"
        result.update(mode=mode, anchor=anchor)
        for relative, expected in sorted(blobs.items()):
            observed = git_query("rev-parse", f"{anchor}:{prefix}{relative}")
            if observed != expected:
                errors.append(f"rollback_blob_mismatch:{relative}")
            else:
                result["verified_blobs"] += 1
    except (OSError, RuntimeError) as exc:
        errors.append(f"rollback_git_error:{type(exc).__name__}:{exc}")
    return result
