# Control checkpoint — M02.5 complete; WSL reboot pending

Date: 2026-07-22  
Status: `M02.5 PASS / M03.1 NEXT / WSL REBOOT REQUIRED / RELEASE BLOCKED`

## Project restart point

- Parent branch: `codex/mtr-source-freeze-v3`.
- Last clean M02.4 checkpoint commit: `0f57322`.
- Accepted M02.5 implementation/evidence commit: `fee3c8026fed2c4b1b6144b59ecd1d8769b14a85`.
- Project: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator`.
- Shared identity: `mtr-v3-source-a5c4bdbb2fca`.
- Arm APK: `157,054,042` bytes; SHA-256 `761FE83F4DE11AD5502A8FE18E3ED4123C2A86118EC2A8DC1AD259C0D5B69279`.
- ABI proof: arm64 ELF64/AArch64 `0x00B7`; armv7 ELF32/ARM `0x0028`.
- Package/signature/payload: PASS; physical install not performed.
- Development static gate: `qg.20260722082348.cb31e1f5e6da`, `8/8 PASS`, zero findings, source stable.
- Clean-source static gate on `fee3c8026fed2c4b1b6144b59ecd1d8769b14a85`: `qg.20260722082553.cb31e1f5e6da`, `8/8 PASS`, zero findings, source clean/stable; report SHA-256 `D82A591C8374F82DAF8354D1C28442D1A6544411766CE5E585B2DCD9E2D33F1E`.

## WSL / CodeRabbit state

- User requested WSL and CodeRabbit CLI installation plus browser authentication.
- Official WSL route was followed; elevated `wsl --install -d Ubuntu --no-launch` returned exit `0`.
- Installed WSL runtime: `2.7.10.0`, kernel package `6.18.33.2-2`; default version `2`.
- Firmware virtualization reports enabled.
- Windows reports Virtual Machine Platform activation and a system reboot pending; Ubuntu is not yet registered.
- CodeRabbit CLI cannot be installed or authenticated until the reboot and Ubuntu first launch complete.
- After explicit reboot approval: install/register Ubuntu, complete Linux user initialization, run official `curl -fsSL https://cli.coderabbit.ai/install.sh | sh`, verify version, then run `coderabbit auth login` in a visible terminal and verify `coderabbit auth status`.

## Next safe actions

1. Obtain explicit permission before rebooting Windows.
2. Complete Ubuntu and CodeRabbit setup/auth after reboot.
3. Resume project at M03.1 read-only GameRoot inventory.

Release remains blocked by production signing/distribution and Pages topology/deployment.
