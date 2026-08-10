# Control log checkpoint — M03.3B + TC-01 complete

Date: 2026-08-09 18:41 +03:00

**Status:** `completed` — pure lifecycle contract and fail-closed Android
no-build toolchain acceptance; runtime/release remain blocked.

**Roadmap position:** P0 `TC-01` complete; P1 `M03.3B` complete;
`M03.3C` ready. Source package `M03.3` remains pending until C.

**Progress:** execution ledger `4/65` complete (`6.2%`), `61` mandatory units
remain and `7` are conditional. Source ledger remains `19/95`, mandatory
`19/85`, with `66` mandatory and `10` conditional source packages remaining.
The 65-unit execution denominator is provisional until M04/M05/M10 child
batches are instantiated.

**Evidence:**

- LifecycleEpoch: `16/16` Node groups, strict TypeScript 5.8.2/ES2015,
  Python structural PASS, no GameRoot wiring.
- TC-01: `35/35` PowerShell groups and `15/15` Python negative cases PASS;
  schema applied and current-run bounded entrypoint self-test PASS.
- Two direct + two wrapper host preflights PASS on exact Adoptium 17.0.20;
  ambient Adoptium Java 21 observed and not selected.
- Existing arm/emulator exports match Gradle 8.11.1, AGP 8.10.1, compile 36,
  target 35, build-tools 36.0.0, NDK 23.2.8568313 and approved SDK. They are
  historical no-build evidence, not fresh artifacts.
- Exact Gradle distribution URL, launcher/wrapper hashes and absence of daemon
  JVM criteria are bound; clean-checkout and reparse-point negatives PASS.
- Executable preflight independently pins JDK/Cocos/Android policy; a
  self-consistent JDK 21 contract+config redefinition is rejected.
- Two content-identity regressions PASS with `state=NOT_BUILT`.
- M03.3A/M03.2 regressions and accepted full-source no-emit PASS.
- Canonical cumulative gate after the runtime policy-pin fix: `14/14 PASS`,
  run `qg.20260809154115.ee34f3f3acbc`, zero findings; dirty source was
  explicitly authorized and remained stable.
- Protected GameRoot, state contract, scene, resources and package/lock remain
  unchanged; no Cocos, Gradle, adb, emulator, import, build, deploy or push.

**Remaining:** M03.3C GameRoot adapter + fresh Web/Android-emulator P4; source
M03.3 closure; signing/deployment/release-assurance and final RC/cleanup gates.

**Next:** request a separate explicit approval for M03.3C because it changes
runtime ownership and requires fresh builds plus emulator QA.

## Restart receipt

1. Confirm HEAD/diff still matches this checkpoint.
2. Run M03.3A, M03.3B and M03.2 Node/Python regressions.
3. Run `tools/codex/test-android-build-toolchain.ps1` and both no-build wrapper
   preflights; do not use the legacy adb/emulator probe for TC evidence.
4. Run the 14-step canonical gate and compare the final report.
5. Only with explicit approval, start M03.3C and its full P4.
