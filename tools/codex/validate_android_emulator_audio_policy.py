#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re


def has_am_start(text: str) -> bool:
    return re.search(r"['\"]am['\"]\s*,\s*['\"]start['\"]", text) is not None


def require(text: str, needle: str, label: str, errors: list[str]) -> None:
    if needle not in text:
        errors.append(f"{label}: missing {needle!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    tools = root / "tools" / "codex"
    errors: list[str] = []

    guard_path = tools / "MtrAndroidQaAudioGuard.ps1"
    if not guard_path.is_file():
        errors.append(f"missing audio guard: {guard_path}")
    else:
        guard = guard_path.read_text(encoding="utf-8")
        for needle in (
            "function Assert-MtrAndroidQaAudioMuted",
            "'emu', 'avd', 'name'",
            "-no-audio",
            "'media_session', 'volume', '--stream', '3', '--set', '0'",
            "'media_session', 'volume', '--stream', '3', '--get'",
            "volume is (?<volume>",
        ):
            require(guard, needle, guard_path.name, errors)

    launcher_path = tools / "Test-MtrAndroidToolchain.ps1"
    launcher = launcher_path.read_text(encoding="utf-8")
    require(launcher, "MtrAndroidQaBootPolicy.psm1", launcher_path.name, errors)
    require(launcher, "Get-MtrAndroidQaEmulatorArguments", launcher_path.name, errors)
    boot_policy_path = tools / "MtrAndroidQaBootPolicy.psm1"
    if not boot_policy_path.is_file():
        errors.append(f"missing boot policy: {boot_policy_path}")
    else:
        boot_policy = boot_policy_path.read_text(encoding="utf-8")
        require(boot_policy, "'-no-audio'", boot_policy_path.name, errors)
        require(boot_policy, "'-no-snapshot-load'", boot_policy_path.name, errors)
    for filename in ("Run-MtrWebAtlasPilotQa.js", "Run-MtrWebMatrixQa.js", "run_web_playwright_function.js"):
        source = (tools / filename).read_text(encoding="utf-8")
        require(source, "--mute-audio", filename, errors)

    qa_scripts: list[Path] = []
    for path in sorted(tools.glob("Run-MtrAndroid*Qa.ps1")):
        text = path.read_text(encoding="utf-8")
        if has_am_start(text):
            qa_scripts.append(path)
            require(text, "MtrAndroidQaAudioGuard.ps1", path.name, errors)
            require(text, "Assert-MtrAndroidQaAudioMuted", path.name, errors)
            require(text, "$audioPolicy", path.name, errors)

    if not qa_scripts:
        errors.append("no Android runtime QA launch scripts discovered")

    agents_path = root / "AGENTS.md"
    agents = agents_path.read_text(encoding="utf-8")
    require(agents, "-no-audio", agents_path.name, errors)
    require(agents, "media stream 3", agents_path.name, errors)

    if errors:
        print("Android emulator silent-policy validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Android emulator silent-policy validation: PASS "
        f"({len(qa_scripts)} runtime QA launch scripts guarded)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
