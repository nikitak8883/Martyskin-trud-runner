# Android cold-boot cohort — bounded qualification PASS, overlay trigger open

Status: `partial` for ANDROID-NATIVE-BOOTSTRAP-001; this diagnostic cohort is
`completed`. Parent P2/M04-C-FAMILY-THEME-LOGISTICS/M12.7 remains incomplete.
No execution-unit credit:20/73 (27.3973%),53 mandatory +7 conditional remaining;
source ledger28/95. No Release, full campaign or all-skin acceptance.

## Frozen inputs and predeclared conditions

- Clean application scope at root8001ad7362173c80786a4b8572370d4af606475a.
  Native repair build rootb3b82b1364a85bab59381be89ab98969a26129c6; no rebuild,
  reinstall or product change in this cohort. Debug/x86_64 APK SHA-256:
  `D323FA64E4536634D8CCAAFA70FDDD2085EA1E994313F9C948E8DA1BE610392B`.
- Source-only repair9c0a9992d84174ec188ae9d6e20094becea6de86 was actually
  accepted by hosted run36875609617, Windows36/36 and Linux36/36, each72
  artifact hashes verified. Those receipts accept that repair, not later docs.
- Four independent immediate/settled pairs, order AB/BA/AB/BA fixed before
  outcomes. Every arm uses fresh no-snapshot process/boot, unchanged persistent
  AVD storage, API35/x86_64/SwiftShader/MTR_Pixel_8_Pro_API_35/emulator-5554/user0.
  Cold boot here is NOT cold storage, factory boot or fresh installation.
- Immediate means no artificial settling, toolchain receipt to helper handoff
  <=10s; actual helper start is separately recorded. Settled means30s from the
  same receipt boundary. These are admission controls, not performance samples.
- Exact installed APK verified every arm; menu timeout35s/zero retries.
  Normal launch/no debug fault injection. No forced overlay change, adb root,
  physical device, snapshot load/save, userdata clear or concurrent build/static/
  model work. Host `-no-audio` plus fail-closed media stream3=0 verified before
  each launch and the final matrix; product audio/preferences unchanged.

## Actual runtime results

Run2026-10-01T18:56:35+03 to19:15:07+03. Eight distinct boot process identities;
all exact APK/user0/focused/rendered menu assertions PASS, no fatal, no debug
request, one fresh Activity create per arm. Each owned AVD identity revalidated
before normal `adb emu kill`; broad primary/headless/qemu resident count ends0.

| Pair | Mode | Receipt -> helper handoff ms | Menu marker wait ms | Result |
| --- | --- | --- | --- | --- |
| 1 | immediate | 729 | 17418 | PASS |
| 1 | settled | 30509 | 10479 | PASS |
| 2 | settled | 30521 | 10592 | PASS |
| 2 | immediate | 522 | 17197 | PASS |
| 3 | immediate | 625 | 17948 | PASS |
| 3 | settled | 30511 | 11208 | PASS |
| 4 | settled | 30500 | 10514 | PASS |
| 4 | immediate | 575 | 16733 | PASS |

Each log has one broad resource-search candidate. Inspection classifies all
eight as the game's `MTR_LAYER_ORDER_READY ... >DEV_OVERLAY`, NOT an Android
system-overlay/resource event. Actual candidate system-resource events0;
natural pre-window DESTROY0, guard exit0, new instance0. Original early-boot
system-overlay trigger is **NOT_OBSERVED**, not reproduced or proven impossible.
No new product fix or broader issue closure is inferred from passing menus.

After arm8, one complete unchanged Android startup/UI/all15-level matrix passes
28/28 (13 UI starts +15 level starts),19:08:43+03 to19:14:46+03. Fatal,
deprecation, product warning and unexpected Cocos diagnostics0. Allowlisted
engine diagnostics remain84 errors/28 warnings, visible and not relabelled0.
Actual menu/level02/level15 screenshots sampled: no new confirmed startup/render
regression; this is NOT exhaustive visual/campaign/skin-bonus QA.

## Preserved caller failures and prevention

Both predecessors failed before game admission, not product runtime failures:

1. Short-lived boot launcher inherited output handles into its emulator, so a
   caller's unbounded stdout EOF wait hung after child exit. Recovery verified
   exact owned PID/parent/argv/AVD before stopping it. Corrected diagnostic driver
   keeps boot invocation in its persistent owner and bounds both process lifetime
   and stdout/stderr EOF for other clients. Four regression cycles5/5 (20/20)
   include inherited-descendant EOF, lifetime timeout, nonzero exit and typed args.
2. Current PowerShell JSON ISO-Z value is typed UTC DateTime. Parsing its implicit
   culture string moved2026-10-01 to2026-01-10 and lost timezone, producing a false
   immediate admission rejection (22816800.4733921s). Typed DateTimeOffset cast
   retains the instant; four cycles40 assertions across en-US/he-IL/ru-RU/string/
   typed inputs also guard30s settling. Permanent project tools contain no such
   Parse call. No admission/runtime threshold relaxed.

Caller fixes are private diagnostics, not global hooks/SDK/toolchain changes.
Broad emulator resident regex includes `qemu-system-*-headless.exe`; exact-name
only inventory is not zero-resident proof. Initial wrong tool/module/image reads
and one syntax error made no product mutation; corrected actual paths were used.

## Immutable evidence and next boundary

Evidence is ROOT-relative, not inside the application:
`temp/native-cold-cohort-20261001`.

- `runtime-successor2/report.json`,8/8:
  `BAE9B0F63BD49E9EFB0DFBB96F6239F41D159878DECA065817E9E43D795597E8`.
- `runtime-successor2/case8-pair4-immediate/post-cohort-matrix/android_matrix_cycle1_summary.json`,28/28:
  `E41FA777BA2285AF43B09876FC11C7DF7E8266B2D27E3B3529546A192AEB48F5`.
- `VERIFIED_RECEIPTS.json`,252 records, original failures/tools/logs/boot receipts/
  APK/audio/screenshots and explicit event classification:
  `0B5BBCB40A458CAEDA3DCB86570891E1A5BBC7BF17BB585B33F006B8814AB507`.
- Failed original report:
  `19324E12B2B2D2A812342EFD2774A0D2396171EFCFD2A3B6D615C5E1247E9F89`;
  failed successor1 report:
  `995F0DB5704B659323049732E43058C411D21F3AB16A6FA7251E1F9917817D3F`.

Full clean36-step local gate and exact post-documentation source-only hosted
receipts are separate; never infer them from the previous CI. Hygiene preserves
unrelated user work and immutable failures; no broad deletion or rejected cleanup
workaround. CodeRabbit/local-model review NOT_RUN for this diagnostic/doc slice.

Next: genuinely permitted current Web QA entrypoint, then separate overlay/
configuration acceptance and symmetric fresh atlas attempt02 input lock. Web
runtime NOT_RUN because prior localhost server-start was rejected; no alternate
shell/tool/encoding workaround. Attempt02 inputs/samples NOT_RUN; this cohort
is not evidence for fixing its load/FPS failure. Signed/device-valid Release,
owner/main/Pages and physical-device acceptance remain outstanding.
