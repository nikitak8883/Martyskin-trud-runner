# Release Gate Checklist

A release candidate is blocked if any item below fails.

## Hard blockers

- [ ] No missing skin/bonus texture bindings.
- [ ] No null SpriteFrame or missing resource load in smoke tests.
- [ ] No checkerboard/white matte visible in runtime assets.
- [ ] No HUD/menu overlap with safe area.
- [ ] No debug colliders/debug overlays in production.
- [ ] No Android black screen or native startup fatal error.
- [ ] No Web fatal console error.
- [ ] No broken remote/local bundle resolution.
- [ ] No invalid generated level segment in live queue.

## Build artifacts

- [ ] Web build generated.
- [ ] Android debug APK generated for smoke.
- [ ] Release APK or AAB generated when requested.
- [ ] Release APK/AAB is device-valid when delivered as final Android artifact.
- [ ] SHA256 generated for each artifact.
- [ ] Release notes include content manifest version.

## Post-release plan

- [ ] Android vitals monitoring plan written.
- [ ] Crash/ANR/logcat triage process written.
- [ ] Rollback/fallback plan written.

