from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


IGNORE_DIRS = {
    ".git",
    ".idea",
    "library",
    "temp",
    "tmp",
    ".tmp",
    "build",
    "native",
    "profiles",
}


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def rel(project_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        return str(path)


def is_under(path: Path, names: set[str]) -> bool:
    parts = set(path.parts)
    return any(name in parts for name in names)


def collect_candidates(project_root: Path) -> dict[str, list[dict[str, object]]]:
    candidates: dict[str, list[dict[str, object]]] = {
        "temporaryDirectories": [],
        "rootBuildLogs": [],
        "runtimeWholeSheetsRisk": [],
        "largeRuntimeImages": [],
        "generatedPythonCache": [],
    }

    for name in [".tmp", "tmp", "temp"]:
        path = project_root / name
        if path.exists():
            candidates["temporaryDirectories"].append({
                "path": rel(project_root, path),
                "reason": "temporary workspace directory; review before deletion",
            })

    for path in project_root.glob("*.log"):
        candidates["rootBuildLogs"].append({
            "path": rel(project_root, path),
            "sizeBytes": file_size(path),
            "reason": "root build log; archive or delete only after QA evidence is preserved",
        })

    for path in project_root.glob("**/__pycache__"):
        if is_under(path, {"library", "temp", "build", "native"}):
            continue
        candidates["generatedPythonCache"].append({
            "path": rel(project_root, path),
            "reason": "Python bytecode cache; safe to remove if no Python process is using it",
        })

    runtime_roots = [
        project_root / "assets" / "resources" / "objectives",
        project_root / "assets" / "resources" / "objectives" / "themed",
    ]
    for root in runtime_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.png"):
            size = file_size(path)
            name = path.name.lower()
            width_hint = 0
            height_hint = 0
            try:
                from PIL import Image

                with Image.open(path) as img:
                    width_hint, height_hint = img.size
            except Exception:
                pass
            if "sheet" in name or "photo" in name or "chatgpt image" in name:
                candidates["runtimeWholeSheetsRisk"].append({
                    "path": rel(project_root, path),
                    "sizeBytes": size,
                    "resolution": [width_hint, height_hint],
                    "reason": "filename suggests whole-sheet/source image inside runtime resources",
                })
            if width_hint >= 1800 or height_hint >= 1400 or size >= 2_500_000:
                candidates["largeRuntimeImages"].append({
                    "path": rel(project_root, path),
                    "sizeBytes": size,
                    "resolution": [width_hint, height_hint],
                    "reason": "large runtime image; verify it is intentional and preloaded/optimized",
                })

    for key in candidates:
        candidates[key].sort(key=lambda item: str(item.get("path", "")))
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run cleanup audit for Martyskin Cocos project.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--report", default="qa/cleanup_audit_20260603.json")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    report_path = project_root / args.report
    candidates = collect_candidates(project_root)
    report = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "mode": "dry-run",
        "projectRoot": str(project_root),
        "candidateCounts": {key: len(value) for key, value in candidates.items()},
        "candidates": candidates,
        "note": "This tool does not delete files. Review candidates manually before any cleanup.",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "mode": report["mode"],
        "report": str(report_path),
        "candidateCounts": report["candidateCounts"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
