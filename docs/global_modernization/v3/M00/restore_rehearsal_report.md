# M00 restore rehearsal report

Status: `PASS_AFTER_BOUNDED_RECOVERY`

## Restored anchors

- Source commit: `12670452ae4580ef5c685ff986476daf91522978`
- Source tree: `9faa768c9b81f94b7745c917b6d7d49b7cef884c`
- Annotated tag: `mtr-source-freeze-v3-20260719`
- Pages commit: `d7a7cc1b0f75cd7aed7ac831e86f79421014e96f`
- Restored source manifest SHA-256: `AD57113833A77E1FCD4E1DE8CE718C7F8204F54AD52E06D7F89F9CB002A7CC71`
- Manifest comparison: byte-identical.

The rehearsal used only the two local bundles. No source remote or network fetch was required.

## Required Windows restore contract

The first ordinary clone under the long `%TEMP%` path failed during checkout on 17 Cocos asset/meta paths with `Filename too long`. The bundle itself verified successfully.

The accepted restore command therefore uses both a short root and Git long-path support:

```powershell
git -c core.longpaths=true clone --branch codex/mtr-source-freeze-v3 --single-branch `
  "C:\Projects\Monkey Work\Tasks\5\checkpoints\MTR_SOURCE_FREEZE_V3_20260719_1267045.bundle" `
  "C:\mtr-r\1267045"
```

The Pages repository is restored independently into the pinned gitlink path from `MTR_PAGES_MAIN_20260719_D7A7CC1.bundle`, then registered with `git submodule init`.

## Cocos TypeScript prerequisite

A fresh source checkout intentionally has no tracked `temp/`. The first TypeScript attempt therefore reported missing generated declarations. The successful rehearsal copied the local Cocos Creator 3.8.8 generated seed into ignored `temp/`:

- `temp/tsconfig.cocos.json`
- `temp/declarations/cc.d.ts`
- `temp/declarations/cc.custom-macro.d.ts`
- `temp/declarations/cc.env.d.ts`
- `temp/declarations/jsb.d.ts`

The five files total 4063 bytes and have canonical aggregate SHA-256 `0225D18517E7FA95F0B690F9097B01A972AD5351F43D8078F03F717E400582B5`.

M01 must wrap this prerequisite explicitly; the files remain generated and are not source-controlled.

## Repeated gates

| Gate | Result |
| --- | --- |
| Bundle verification and complete-history declaration | PASS |
| Source HEAD/tree/tag identity | PASS |
| Pages gitlink and `.gitmodules` mapping | PASS |
| Parent and Pages status clean | PASS |
| Deterministic source manifest | PASS, 4170 files / 925653734 bytes |
| `validate-mtr-config.ps1` | PASS, 15 levels / 15 backgrounds / Android-Web QA parity |
| Cocos-compatible project TypeScript | PASS |
| Asset validator | PASS, 1528 PNG / 0 blockers |
| Skin/bonus validator | PASS, 576/576 / 0 warnings |
| UI IR validator | PASS, 14/14 / 0 problems |

No build, Web runtime, Android emulator, physical device, signing or publication action was performed in M00.

## Cleanup

The failed long-path clone, successful short-path clone, generated Cocos temp seed and temporary raw reports were removed after their compact summaries and hashes were captured. The two protected bundles remain under `Tasks/5/checkpoints`.
