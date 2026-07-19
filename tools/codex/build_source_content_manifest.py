#!/usr/bin/env python3
"""Build a deterministic SHA-256 source manifest from one Git commit.

The manifest reads blobs through `git cat-file --batch`; it never trusts a
possibly dirty working tree and intentionally contains no timestamp or
absolute machine path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def git_text(root: Path, *args: str) -> str:
    return git_bytes(root, *args).decode("utf-8").strip()


def parse_tree(root: Path, commit: str, project_relative: str) -> list[dict[str, object]]:
    raw = git_bytes(root, "-c", "core.quotepath=false", "ls-tree", "-r", "-l", "-z", commit, "--", project_relative)
    records: list[dict[str, object]] = []
    prefix = f"{project_relative.rstrip('/')}/"
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, path_bytes = item.split(b"\t", 1)
        mode_bytes, type_bytes, object_bytes, size_bytes = metadata.split(None, 3)
        object_type = type_bytes.decode("ascii")
        if object_type != "blob":
            raise RuntimeError(f"Unexpected {object_type} entry inside project tree: {path_bytes!r}")
        repository_path = path_bytes.decode("utf-8")
        if not repository_path.startswith(prefix):
            raise RuntimeError(f"Path escaped project boundary: {repository_path}")
        records.append(
            {
                "mode": mode_bytes.decode("ascii"),
                "git_blob": object_bytes.decode("ascii"),
                "bytes": int(size_bytes),
                "path": repository_path[len(prefix) :],
            }
        )
    records.sort(key=lambda entry: str(entry["path"]))
    return records


def read_blob_hashes(root: Path, object_ids: list[str]) -> dict[str, str]:
    process = subprocess.Popen(
        ["git", "-C", str(root), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdin is None or process.stdout is None:
        raise RuntimeError("Unable to open git cat-file pipes")

    hashes: dict[str, str] = {}
    try:
        for object_id in dict.fromkeys(object_ids):
            process.stdin.write(object_id.encode("ascii") + b"\n")
            process.stdin.flush()
            header = process.stdout.readline().rstrip(b"\n")
            fields = header.split()
            if len(fields) != 3 or fields[1] != b"blob":
                raise RuntimeError(f"Unexpected git cat-file header for {object_id}: {header!r}")
            size = int(fields[2])
            content = process.stdout.read(size)
            terminator = process.stdout.read(1)
            if len(content) != size or terminator != b"\n":
                raise RuntimeError(f"Truncated git blob stream for {object_id}")
            hashes[object_id] = hashlib.sha256(content).hexdigest().upper()
    finally:
        process.stdin.close()
        return_code = process.wait(timeout=30)
        if return_code != 0:
            stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            raise RuntimeError(f"git cat-file failed with {return_code}: {stderr}")
    return hashes


def read_gitlink(root: Path, commit: str, gitlink_path: str) -> dict[str, str]:
    raw = git_text(root, "ls-tree", commit, "--", gitlink_path)
    metadata, path = raw.split("\t", 1)
    mode, object_type, object_id = metadata.split()
    if mode != "160000" or object_type != "commit" or path != gitlink_path:
        raise RuntimeError(f"Invalid gitlink entry: {raw}")
    return {"path": path, "commit": object_id}


def build_manifest(root: Path, commit_ref: str, project_relative: str, gitlink_path: str) -> dict[str, object]:
    commit = git_text(root, "rev-parse", f"{commit_ref}^{{commit}}")
    source_tree = git_text(root, "rev-parse", f"{commit}^{{tree}}")
    project_tree = git_text(root, "rev-parse", f"{commit}:{project_relative}")
    object_format = git_text(root, "rev-parse", "--show-object-format")
    records = parse_tree(root, commit, project_relative)
    blob_hashes = read_blob_hashes(root, [str(entry["git_blob"]) for entry in records])

    aggregate = hashlib.sha256()
    total_bytes = 0
    files: list[dict[str, object]] = []
    for entry in records:
        size = int(entry["bytes"])
        sha256 = blob_hashes[str(entry["git_blob"])]
        path = str(entry["path"])
        mode = str(entry["mode"])
        total_bytes += size
        aggregate.update(f"{mode}\t{size}\t{sha256}\t{path}\n".encode("utf-8"))
        files.append(
            {
                "path": path,
                "mode": mode,
                "bytes": size,
                "sha256": sha256,
                "git_blob": entry["git_blob"],
            }
        )

    return {
        "schema_version": 1,
        "manifest_kind": "mtr_source_content_fingerprint",
        "content_version": f"mtr-v3-freeze-{commit[:12]}",
        "source_commit": commit,
        "source_tree": source_tree,
        "project_tree": project_tree,
        "git_object_format": object_format,
        "project_relative": project_relative,
        "hash_algorithm": "sha256",
        "canonical_record_format": "mode\\tbytes\\tsha256\\tpath\\n",
        "file_count": len(files),
        "total_bytes": total_bytes,
        "aggregate_sha256": aggregate.hexdigest().upper(),
        "pages_gitlink": read_gitlink(root, commit, gitlink_path),
        "excluded_local_only": ["docs/qa/evidence/**", "output/**"],
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--git-root", type=Path, required=True)
    parser.add_argument("--project-relative", required=True)
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--gitlink-path", default="_github/Martyskin-trud-runner")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.git_root.resolve()
    manifest = build_manifest(root, args.commit, args.project_relative.replace("\\", "/").rstrip("/"), args.gitlink_path)
    encoded = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    print(
        json.dumps(
            {
                "output": str(output),
                "source_commit": manifest["source_commit"],
                "file_count": manifest["file_count"],
                "total_bytes": manifest["total_bytes"],
                "aggregate_sha256": manifest["aggregate_sha256"],
                "manifest_sha256": hashlib.sha256(encoded).hexdigest().upper(),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
