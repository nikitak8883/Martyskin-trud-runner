#!/usr/bin/env python3
"""Small deterministic subprocess fixture for quality-gate self-tests."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def atomic_json(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=("pass", "fail", "sleep", "write-runtime", "write-text", "spawn-child", "delayed-marker"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--marker", type=Path)
    parser.add_argument("--delay", type=float, default=5.0)
    parser.add_argument("--parent-sleep", type=float, default=20.0)
    parser.add_argument("--stderr", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "pass":
        print("fixture-pass")
        if args.stderr:
            print("fixture-stderr", file=sys.stderr)
        return 0
    if args.mode == "fail":
        print("fixture-fail", file=sys.stderr)
        return 7
    if args.mode == "sleep":
        time.sleep(args.delay)
        return 0
    if args.mode == "write-runtime":
        if args.output is None:
            parser.error("--output is required for write-runtime")
        atomic_json(args.output, {"runtimeReady": True})
        print(f"runtime-report={args.output}")
        return 0
    if args.mode == "write-text":
        if args.output is None:
            parser.error("--output is required for write-text")
        args.output.write_text("mutated by fixture\n", encoding="utf-8")
        print(f"text-output={args.output}")
        return 0
    if args.mode == "delayed-marker":
        if args.marker is None:
            parser.error("--marker is required for delayed-marker")
        time.sleep(args.delay)
        args.marker.parent.mkdir(parents=True, exist_ok=True)
        args.marker.write_text("child-survived\n", encoding="utf-8")
        return 0
    if args.mode == "spawn-child":
        if args.marker is None:
            parser.error("--marker is required for spawn-child")
        child = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--mode",
                "delayed-marker",
                "--marker",
                str(args.marker),
                "--delay",
                str(args.delay),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        print(f"child-pid={child.pid}", flush=True)
        time.sleep(args.parent_sleep)
        return 0
    return 9


if __name__ == "__main__":
    raise SystemExit(main())
