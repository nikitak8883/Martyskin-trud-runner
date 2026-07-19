# Code Review Checklist

## Scope

- [ ] Patch scope matches approved module.
- [ ] No unrelated files changed.
- [ ] No generated junk committed into runtime paths.
- [ ] No destructive cleanup without approval.

## Architecture

- [ ] No direct UI/gameplay circular dependency.
- [ ] No hardcoded runtime asset path where registry/manifest should be used.
- [ ] No duplicated state machine or skin resolver.
- [ ] No old/new UI system mixed on same active screen.

## Runtime safety

- [ ] No missing null checks for asset loads.
- [ ] Asset load failures log structured errors.
- [ ] Bonus fallback does not hide release blocker in QA.
- [ ] Timers/events are cleaned on scene restart.

## Performance

- [ ] No per-frame allocations in hot loops unless justified.
- [ ] Object pooling used for repeated obstacles/VFX where relevant.
- [ ] No full-directory load of optional skins at startup.
- [ ] No uncontrolled dynamic atlas expansion.

## Release

- [ ] Web and Android use same content manifest version.
- [ ] Debug flags off by default for release claims.
- [ ] Release artifact SHA256 generated.
- [ ] Reports match actually executed commands.

