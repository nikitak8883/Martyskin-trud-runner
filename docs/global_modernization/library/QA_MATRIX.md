# QA Matrix — Mandatory 7-Cycle Engineering QA

## Cycle 1 — Build and Smoke

- [ ] Run static validators.
- [ ] Build Web Mobile when runtime JS/assets changed.
- [ ] Build Android debug APK when runtime JS/assets/native Android changed.
- [ ] Launch Web smoke to menu and level 1.
- [ ] Install/launch Android on emulator by default.
- [ ] Scan console/logcat for fatal errors.

## Cycle 2 — Visual and UI

- [ ] Check main menu, level select, primate select, settings, achievements, records, dev mode, pause, death screen.
- [ ] Check 5 aspect ratios.
- [ ] Check no ghost legacy layer.
- [ ] Check Cyrillic text fits.
- [ ] Check buttons have no double labels.

## Cycle 3 — Gameplay and Physics

- [ ] Test jump/glide/dash/pause on Android and Web.
- [ ] Run 10 restart loop.
- [ ] Test all collision categories.
- [ ] Test level completion and fail paths.
- [ ] Verify no debug colliders in production.

## Cycle 4 — Skins and Bonuses

- [ ] Run all 8 skins.
- [ ] Run all base animations.
- [ ] Run all bonus visuals.
- [ ] Check helmet/vest/magnet/blueprint/radio/shield/banana_boost/boots/key_pass/coffee mappings.
- [ ] Check no visual leftovers after bonus expiry.

## Cycle 5 — Audio and VFX

- [ ] Test all audio buses.
- [ ] Test Web audio unlock.
- [ ] Test settings persistence.
- [ ] Test collect/hit/fail/achievement sounds.
- [ ] Check VFX readability and performance.

## Cycle 6 — Performance and Device

- [ ] 5-minute gameplay run.
- [ ] Capture memory/PSS.
- [ ] Capture FPS/frame pacing if available.
- [ ] Check APK/AAB/Web size.
- [ ] Check load times and bundle load failures.

## Cycle 7 — Release Regression and Cleanup

- [ ] Re-run critical smoke after optimization.
- [ ] Create release artifacts.
- [ ] Generate SHA256 for artifacts.
- [ ] Run cleanup dry-run.
- [ ] Confirm no runtime assets accidentally removed.
- [ ] Produce final release report.

## Project-specific override

Android runtime QA defaults to emulator-only. Physical phone testing/install is allowed only after explicit user authorization.

