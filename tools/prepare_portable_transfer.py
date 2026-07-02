# -*- coding: utf-8 -*-
"""Prepare a local portable transfer package for the Martyskin project.

This script is intentionally conservative:
- it never deletes files;
- it uses an allow-list for canonical project content;
- it excludes Cocos/Gradle caches and transient build state;
- it writes an archive, archive manifest, checksums, and environment report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_NAME = ROOT.name

INCLUDE_DIRS = {
    ".creator",
    "assets",
    "assets_seed",
    "docs",
    "Martyshkin world pictures",
    "native",
    "nessesary",
    "releases",
    "settings",
    "texture",
    "tools",
}

INCLUDE_ROOT_FILES = {
    ".gitignore",
    "AGENTS.md",
    "MARTYSKIN_UNIVERSE_FULL_TEXT.txt",
    "README_RU.md",
    "assets.meta",
    "build-android.json",
    "build-web-mobile.json",
    "package.json",
    "tsconfig.json",
}

EXCLUDE_DIR_NAMES = {
    ".git",
    ".gradle",
    ".idea",
    ".cxx",
    ".externalNativeBuild",
    "__pycache__",
    "_archive",
    "_backup",
    "backup",
    "build",
    "dist",
    "intermediates",
    "library",
    "local",
    "node_modules",
    "obj",
    "out",
    "outputs",
    "portable_transfer",
    "profiles",
    "temp",
    "transfer",
}

EXCLUDE_SUFFIXES = {
    ".7z",
    ".apks",
    ".bak",
    ".bundle",
    ".err.log",
    ".iml",
    ".ipa",
    ".log",
    ".old",
    ".orig",
    ".out.log",
    ".pyc",
    ".pyo",
    ".rar",
    ".tmp",
    ".xapk",
    ".zip",
}

FINAL_RELEASE_BINARY_DIRS = {
    Path("releases/android"),
}


def rel(path: Path) -> Path:
    return path.relative_to(ROOT)


def rel_posix(path: Path) -> str:
    return rel(path).as_posix()


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def is_top_level_included(path: Path) -> bool:
    relative = rel(path)
    first = relative.parts[0]
    return first in INCLUDE_DIRS or (len(relative.parts) == 1 and first in INCLUDE_ROOT_FILES)


def is_final_release_binary(path: Path) -> bool:
    relative = rel(path)
    return any(is_under(relative, release_dir) for release_dir in FINAL_RELEASE_BINARY_DIRS)


def should_include(path: Path) -> tuple[bool, str]:
    relative = rel(path)
    parts = relative.parts

    if not is_top_level_included(path):
        return False, "not in canonical transfer allow-list"

    if any(part in EXCLUDE_DIR_NAMES for part in parts[:-1]):
        return False, "inside generated/cache/build directory"

    name = path.name
    lower_name = name.lower()

    if lower_name == "9.zip" and relative.parts[:1] == ("nessesary",):
        return False, "duplicate source zip; extracted nessesary/9 is included"

    for suffix in EXCLUDE_SUFFIXES:
        if lower_name.endswith(suffix):
            if path.suffix.lower() in {".apk", ".aab"} and is_final_release_binary(path):
                return True, "final release binary"
            return False, f"excluded transient/archive suffix {suffix}"

    if path.suffix.lower() in {".apk", ".aab"} and not is_final_release_binary(path):
        return False, "non-final Android binary"

    return True, "included"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: list[str]) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
        )
        return {
            "command": " ".join(command),
            "exitCode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except FileNotFoundError:
        return {"command": " ".join(command), "error": "not found"}
    except subprocess.TimeoutExpired:
        return {"command": " ".join(command), "error": "timeout"}


def dir_size(path: Path) -> int:
    total = 0
    for current, dirnames, filenames in os.walk(path):
        dirnames[:] = [name for name in dirnames if name not in {".git"}]
        current_path = Path(current)
        for filename in filenames:
            file_path = current_path / filename
            try:
                total += file_path.stat().st_size
            except OSError:
                pass
    return total


def collect_project_stats() -> dict[str, object]:
    top_dirs = []
    for item in sorted(ROOT.iterdir(), key=lambda p: p.name.lower()):
        if item.is_dir():
            size = dir_size(item)
            top_dirs.append({"path": item.name, "bytes": size, "mb": round(size / 1024 / 1024, 2)})

    large_files = []
    total_bytes = 0
    total_files = 0
    for current, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [name for name in dirnames if name != ".git"]
        current_path = Path(current)
        for filename in filenames:
            file_path = current_path / filename
            try:
                size = file_path.stat().st_size
            except OSError:
                continue
            total_files += 1
            total_bytes += size
            if size > 50 * 1024 * 1024:
                large_files.append({"path": rel_posix(file_path), "bytes": size, "mb": round(size / 1024 / 1024, 2)})

    return {
        "totalFiles": total_files,
        "totalBytes": total_bytes,
        "totalGb": round(total_bytes / 1024 / 1024 / 1024, 3),
        "topLevelDirectories": sorted(top_dirs, key=lambda row: row["bytes"], reverse=True),
        "largeFilesOver50Mb": sorted(large_files, key=lambda row: row["bytes"], reverse=True),
    }


def collect_files() -> tuple[list[Path], dict[str, list[str]]]:
    included: list[Path] = []
    excluded_reasons: dict[str, list[str]] = {}

    for current, dirnames, filenames in os.walk(ROOT):
        current_path = Path(current)

        kept_dirnames = []
        for dirname in dirnames:
            candidate = current_path / dirname
            try:
                relative = rel(candidate)
            except ValueError:
                continue
            first = relative.parts[0]
            if first not in INCLUDE_DIRS and first not in INCLUDE_ROOT_FILES:
                excluded_reasons.setdefault("top-level not allowed", []).append(relative.as_posix())
                continue
            if dirname in EXCLUDE_DIR_NAMES:
                excluded_reasons.setdefault("generated/cache/build directory", []).append(relative.as_posix())
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for filename in filenames:
            path = current_path / filename
            try:
                include, reason = should_include(path)
            except ValueError:
                include, reason = False, "outside project root"
            if include:
                included.append(path)
            else:
                excluded_reasons.setdefault(reason, []).append(rel_posix(path))

    return sorted(included, key=lambda p: rel_posix(p).lower()), excluded_reasons


def write_project_docs(date_id: str, out_dir: Path, stats: dict[str, object]) -> None:
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)

    audit_path = docs_dir / f"PORTABLE_TRANSFER_AUDIT_{date_id}.md"
    guide_path = docs_dir / f"PORTABLE_TRANSFER_NEW_MACHINE_GUIDE_{date_id}.md"

    top_dirs_lines = "\n".join(
        f"- `{row['path']}`: {row['mb']} MB" for row in stats["topLevelDirectories"]
    )
    large_lines = "\n".join(
        f"- `{row['path']}`: {row['mb']} MB" for row in stats["largeFilesOver50Mb"]
    ) or "- none"

    audit_path.write_text(
        f"""# Portable Transfer Audit {date_id}

Project root: `{ROOT}`

## Source size before transfer packaging
- Files: {stats['totalFiles']}
- Bytes: {stats['totalBytes']}
- GB: {stats['totalGb']}

## Top-level directory sizes
{top_dirs_lines}

## Large files over 50 MB
{large_lines}

## Transfer policy
Included in portable archive:
- Cocos source assets: `assets/`, `assets.meta`
- Project settings: `settings/`, `.creator/` metadata when explicitly allowed by Cocos source files
- Native/project support: `native/`, root build configs, `package.json`, `tsconfig.json`
- Source/reference assets: `nessesary/`, `Martyshkin world pictures/`, `texture/`, `assets_seed/`
- Documentation and tools: `docs/`, `tools/`, `AGENTS.md`, `README_RU.md`
- Final user-facing outputs: `releases/android/`, `releases/web/`, `releases/checksums/`

Excluded from portable archive:
- Cocos and Gradle generated folders: `build/`, `library/`, `temp/`
- IDE/user folders: `.idea/`, `profiles/`
- QA scratch evidence: `qa/`
- Transient logs and duplicate archives: `*.log`, `*.tmp`, `*.zip`, except extracted source folders
- Non-final Android outputs outside `releases/android/`

No files were deleted by this transfer preparation.

Generated transfer output directory:
`{out_dir}`
""",
        encoding="utf-8",
    )

    guide_path.write_text(
        f"""# New Machine Restore Guide {date_id}

## 1. Copy and verify
1. Copy the portable archive from:
   `{out_dir}`
2. On the new machine, extract the zip.
3. Verify the archive checksum with the generated `SHA256SUMS.txt`.

PowerShell example:

```powershell
Get-FileHash "MTRCocosCreator-portable-{date_id}.zip" -Algorithm SHA256
```

Compare it with the `ARCHIVE_SHA256` line in `SHA256SUMS.txt`.

## 2. Expected extracted folder
The archive extracts into:

```text
{PROJECT_NAME}/
```

## 3. Required tools
- Cocos Creator matching the project runtime
- Node.js/npm for project tooling if needed
- Python 3 for helper scripts
- Android Studio / Android SDK / adb for Android installs
- JDK compatible with the Gradle project
- Git, if using the backup bundle

## 4. Restore Git backup from bundle
If using the generated bundle:

```powershell
git clone "MTRCocosCreator-git-backup-{date_id}.bundle" "MTRCocosCreator"
cd "MTRCocosCreator"
```

The local zip archive is the primary transfer artifact; Git is an additional backup.

## 5. Android install command
After extraction, install the final APK:

```powershell
& "$env:LOCALAPPDATA\\Android\\Sdk\\platform-tools\\adb.exe" install -r ".\\releases\\android\\Martyshkin-Trud-texture10-clean-20260612-release.apk"
```

If Android reports a signature mismatch:

```powershell
& "$env:LOCALAPPDATA\\Android\\Sdk\\platform-tools\\adb.exe" uninstall com.martyskin.trudrunner
& "$env:LOCALAPPDATA\\Android\\Sdk\\platform-tools\\adb.exe" install ".\\releases\\android\\Martyshkin-Trud-texture10-clean-20260612-release.apk"
```

## 6. Web local run

```powershell
cd ".\\releases\\web"
python -m http.server 8088
```

Open:

```text
http://127.0.0.1:8088/
```
""",
        encoding="utf-8",
    )


def write_environment_report(json_path: Path, md_path: Path, date_id: str) -> None:
    commands = [
        ["git", "--version"],
        ["node", "--version"],
        ["npm", "--version"],
        ["python", "--version"],
        ["java", "-version"],
        ["adb", "version"],
        ["gradle", "--version"],
    ]
    command_results = [run_command(command) for command in commands]
    where_results = []
    if platform.system().lower().startswith("win"):
        for exe in ["git", "node", "npm", "python", "java", "adb", "gradle"]:
            where_results.append(run_command(["where.exe", exe]))

    env_keys = [
        "ANDROID_HOME",
        "ANDROID_SDK_ROOT",
        "JAVA_HOME",
        "COCOS_CREATOR",
        "PATH",
    ]

    report = {
        "dateId": date_id,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "projectRoot": str(ROOT),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python": sys.version,
        },
        "environment": {key: os.environ.get(key, "") for key in env_keys},
        "toolVersions": command_results,
        "toolPaths": where_results,
        "buildConfigs": {
            "android": str(ROOT / "build-android.json"),
            "web": str(ROOT / "build-web-mobile.json"),
        },
    }
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    tool_lines = []
    for item in command_results:
        command = item.get("command", "")
        if "error" in item:
            tool_lines.append(f"- `{command}`: {item['error']}")
            continue
        stdout = str(item.get("stdout", "")).splitlines()
        stderr = str(item.get("stderr", "")).splitlines()
        first_line = stdout[0] if stdout else (stderr[0] if stderr else "")
        tool_lines.append(f"- `{command}`: exit {item.get('exitCode')}, {first_line}")

    env_lines = []
    for key in env_keys:
        value = os.environ.get(key, "")
        if key == "PATH" and value:
            value = value[:500] + ("..." if len(value) > 500 else "")
        env_lines.append(f"- `{key}`: `{value}`")

    md_path.write_text(
        "\n".join(
            [
                f"# Old Machine Environment {date_id}",
                "",
                f"- Project root: `{ROOT}`",
                f"- Generated UTC: `{report['generatedAt']}`",
                f"- OS: `{platform.system()} {platform.release()} {platform.version()}`",
                f"- Machine: `{platform.machine()}`",
                f"- Python runtime: `{sys.version.splitlines()[0]}`",
                "",
                "## Tool Versions",
                *tool_lines,
                "",
                "## Important Environment Variables",
                *env_lines,
                "",
                "## Build Configs",
                f"- Android build config: `{ROOT / 'build-android.json'}`",
                f"- Web build config: `{ROOT / 'build-web-mobile.json'}`",
                "",
                "## Notes For Restore",
                "- Install Cocos Creator 3.8.x; `package.json` declares creator version 3.8.8.",
                "- Install Android SDK, adb, JDK and Gradle-compatible tooling before rebuilding Android.",
                "- The portable zip is the primary local transfer artifact; Git bundle is an additional source backup.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def create_archive(files: list[Path], archive_path: Path) -> list[dict[str, object]]:
    manifest_entries: list[dict[str, object]] = []
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for index, path in enumerate(files, start=1):
            relative = rel_posix(path)
            digest = sha256_file(path)
            stat = path.stat()
            zf.write(path, f"{PROJECT_NAME}/{relative}")
            manifest_entries.append(
                {
                    "path": relative,
                    "bytes": stat.st_size,
                    "mtimeUtc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "sha256": digest,
                }
            )
            if index % 250 == 0:
                print(f"Archived {index}/{len(files)} files...")
    return manifest_entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date-id", default=datetime.now().strftime("%Y%m%d"))
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    date_id = args.date_id
    out_dir = Path(args.output_dir) if args.output_dir else ROOT.parent / f"{PROJECT_NAME}_portable_transfer_{date_id}"
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = collect_project_stats()
    write_project_docs(date_id, out_dir, stats)

    files, excluded_reasons = collect_files()
    archive_path = out_dir / f"{PROJECT_NAME}-portable-{date_id}.zip"
    manifest_json_path = out_dir / f"{PROJECT_NAME}-portable-{date_id}.manifest.json"
    manifest_md_path = out_dir / f"{PROJECT_NAME}-portable-{date_id}.manifest.md"
    checksums_path = out_dir / "SHA256SUMS.txt"
    env_path = out_dir / f"{PROJECT_NAME}-old-machine-environment-{date_id}.json"
    env_md_path = out_dir / f"{PROJECT_NAME}-old-machine-environment-{date_id}.md"

    if archive_path.exists():
        archive_path.unlink()

    entries = create_archive(files, archive_path)
    archive_sha = sha256_file(archive_path)

    manifest = {
        "project": PROJECT_NAME,
        "dateId": date_id,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "projectRoot": str(ROOT),
        "archive": str(archive_path),
        "archiveSha256": archive_sha,
        "includedFileCount": len(entries),
        "includedBytes": sum(entry["bytes"] for entry in entries),
        "excludedSummary": {reason: len(paths) for reason, paths in sorted(excluded_reasons.items())},
        "policy": {
            "noDeletionPerformed": True,
            "primaryTransfer": "zip archive",
            "gitRole": "additional backup",
        },
        "files": entries,
    }
    manifest_json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest_md_path.write_text(
        "\n".join(
            [
                f"# {PROJECT_NAME} Portable Archive Manifest {date_id}",
                "",
                f"- Archive: `{archive_path}`",
                f"- Archive SHA256: `{archive_sha}`",
                f"- Included files: {len(entries)}",
                f"- Included bytes: {manifest['includedBytes']}",
                "",
                "## Excluded Summary",
                *[f"- {reason}: {count}" for reason, count in manifest["excludedSummary"].items()],
                "",
                "## Included Roots",
                *[f"- `{name}`" for name in sorted(INCLUDE_DIRS | INCLUDE_ROOT_FILES)],
            ]
        ),
        encoding="utf-8",
    )

    checksum_lines = [f"{archive_sha}  {archive_path.name}"]
    checksum_lines.extend(f"{entry['sha256']}  {PROJECT_NAME}/{entry['path']}" for entry in entries)
    checksums_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    write_environment_report(env_path, env_md_path, date_id)

    print(json.dumps(
        {
            "archive": str(archive_path),
            "manifest": str(manifest_json_path),
            "checksums": str(checksums_path),
            "environment": str(env_path),
            "environmentMarkdown": str(env_md_path),
            "includedFiles": len(entries),
            "archiveSha256": archive_sha,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
