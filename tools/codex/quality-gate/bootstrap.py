#!/usr/bin/env python3
"""Create/reuse the exact isolated quality-gate venv, then run the gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import venv
from importlib import metadata
from pathlib import Path
from typing import Any


TOOL_ROOT = Path(__file__).resolve().parent
LOCK_PATH = TOOL_ROOT / "requirements.lock"
RUNNER_PATH = TOOL_ROOT / "runner.py"
MINIMUM_PYTHON = (3, 10)
PROBE_TIMEOUT_SECONDS = 30
PIP_INSTALL_TIMEOUT_SECONDS = 600
BOOTSTRAP_LOCK_WAIT_SECONDS = PIP_INSTALL_TIMEOUT_SECONDS + 120


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _cache_root() -> Path:
    override = os.environ.get("MTR_QUALITY_GATE_CACHE")
    if override:
        candidate = Path(override).expanduser().resolve()
        if str(candidate).startswith(("\\\\", "//")):
            raise RuntimeError("MTR_QUALITY_GATE_CACHE must be a local path, not a UNC/network share")
        return candidate
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if not local:
            raise RuntimeError("LOCALAPPDATA is required for the isolated quality-gate cache")
        candidate = (Path(local) / "MTR" / "quality-gate").resolve()
        if str(candidate).startswith(("\\\\", "//")):
            raise RuntimeError("LOCALAPPDATA resolved to a UNC/network share; a local cache is required")
        return candidate
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    candidate = (base / "mtr" / "quality-gate").resolve()
    if str(candidate).startswith("//"):
        raise RuntimeError("XDG cache resolved to a network share; a local cache is required")
    return candidate


def _venv_python(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _locked_packages() -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.count("==") != 1:
            raise RuntimeError(f"Unsupported lock entry: {line!r}")
        name, version = line.split("==", 1)
        result[name.strip().lower().replace("_", "-")] = version.strip()
    return result


def _probe(environment: Path, lock_sha: str) -> bool:
    python_path = _venv_python(environment)
    marker_path = environment / "mtr-quality-gate-environment.json"
    if not python_path.is_file() or not marker_path.is_file():
        return False
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if marker.get("lock_sha256") != lock_sha or marker.get("base_python") != str(Path(sys.executable).resolve()):
        return False
    expected_packages = _locked_packages()
    probe_code = (
        "import json, importlib.metadata as m; "
        f"names={json.dumps(sorted(expected_packages))}; "
        "print(json.dumps({name:m.version(name) for name in names}, sort_keys=True))"
    )
    completed = subprocess.run(
        [str(python_path), "-c", probe_code],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=PROBE_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        return False
    try:
        return json.loads(completed.stdout) == expected_packages
    except json.JSONDecodeError:
        return False


def _atomic_json(path: Path, document: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    payload = (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _install(environment: Path, lock_sha: str) -> None:
    if environment.exists():
        shutil.rmtree(environment)
    venv.EnvBuilder(with_pip=True, clear=False, symlinks=False).create(environment)
    python_path = _venv_python(environment)
    subprocess.run(
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--requirement",
            str(LOCK_PATH),
        ],
        check=True,
        timeout=PIP_INSTALL_TIMEOUT_SECONDS,
    )
    packages = _locked_packages()
    probe_script = (
        "import json, importlib.metadata as m, sys; "
        f"names={json.dumps(sorted(packages))}; "
        "print(json.dumps({name:m.version(name) for name in names}, sort_keys=True))"
    )
    completed = subprocess.run(
        [str(python_path), "-c", probe_script],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=60,
    )
    actual = json.loads(completed.stdout)
    if actual != packages:
        raise RuntimeError(f"Installed packages do not match requirements.lock: {actual!r} != {packages!r}")
    _atomic_json(
        environment / "mtr-quality-gate-environment.json",
        {
            "schema_version": 1,
            "lock_sha256": lock_sha,
            "base_python": str(Path(sys.executable).resolve()),
            "python_version": ".".join(str(value) for value in sys.version_info[:3]),
            "packages": actual,
        },
    )


def ensure_environment() -> tuple[Path, str]:
    if sys.version_info < MINIMUM_PYTHON:
        raise RuntimeError(f"Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}+ is required")
    lock_sha = _sha256(LOCK_PATH)
    cache_root = _cache_root()
    cache_root.mkdir(parents=True, exist_ok=True)
    environment = cache_root / f"venv-py{sys.version_info.major}{sys.version_info.minor}-{lock_sha[:12].lower()}"
    if _probe(environment, lock_sha):
        return environment, lock_sha

    lock_directory = cache_root / f".{environment.name}.bootstrap.lock"
    deadline = time.monotonic() + BOOTSTRAP_LOCK_WAIT_SECONDS
    while True:
        try:
            lock_directory.mkdir()
            break
        except FileExistsError:
            if _probe(environment, lock_sha):
                return environment, lock_sha
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Timed out waiting for bootstrap lock {lock_directory}; "
                    "inspect the owning process before removing the lock"
                )
            time.sleep(0.5)

    try:
        if not _probe(environment, lock_sha):
            try:
                _install(environment, lock_sha)
            except Exception:
                if environment.exists():
                    shutil.rmtree(environment)
                raise
    finally:
        lock_directory.rmdir()
    if not _probe(environment, lock_sha):
        raise RuntimeError("Isolated validator environment did not pass its post-install probe")
    return environment, lock_sha


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-only", action="store_true")
    parser.add_argument("--module", help="Run a Python module in the isolated environment instead of runner.py")
    parser.add_argument("runner_arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        environment, lock_sha = ensure_environment()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "BLOCKED", "code": "VALIDATOR_BOOTSTRAP_FAILED", "detail": str(exc)}), file=sys.stderr)
        return 3
    python_path = _venv_python(environment)
    if args.bootstrap_only:
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "environment": str(environment),
                    "lock_sha256": lock_sha,
                    "python": str(python_path),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    runner_arguments = list(args.runner_arguments)
    if runner_arguments and runner_arguments[0] == "--":
        runner_arguments.pop(0)
    environment_variables = os.environ.copy()
    environment_variables["MTR_QUALITY_GATE_ISOLATED"] = "1"
    environment_variables["MTR_QUALITY_GATE_LOCK_SHA256"] = lock_sha
    if args.module and args.module not in {"unittest"}:
        print(json.dumps({"status": "BLOCKED", "code": "UNAPPROVED_BOOTSTRAP_MODULE", "detail": args.module}), file=sys.stderr)
        return 3
    command = [str(python_path), "-m", args.module, *runner_arguments] if args.module else [str(python_path), str(RUNNER_PATH), *runner_arguments]
    completed = subprocess.run(
        command,
        check=False,
        env=environment_variables,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
