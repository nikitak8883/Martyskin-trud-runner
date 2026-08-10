# Control log checkpoint — M03.3C complete

Date: 2026-08-10 15:23 +03:00

**Status:** `completed` — runtime-адаптер M03.3C реализован, source package
M03.3 закрыт, Web и Android-emulator parity подтверждены. Production release
остаётся blocked.

**Roadmap position:** P1 `M03.3C` complete; source package `M03.3` complete;
`M03.4` ready.

**Progress:** execution ledger `5/65` complete (`7.7%`), остаётся `60`
обязательных execution units и `7` conditional. Source ledger `20/95`:
mandatory `20/85`, обязательный остаток `65`, conditional `10`.

## Evidence

- Единственный `GameRootDevEventAdapter` наблюдает существующий writer и не
  создаёт второй gameplay-state owner.
- Capacity `128`, export bound `32768`; release Web — `0` event/QA markers,
  DEBUG Web — `33/33` unique events и один exact READY marker.
- Canonical pre-commit gate: `15/15 PASS`, zero findings, source stable; run
  `qg.20260810123750.e72aea24a4c4`, report SHA-256
  `9F4E3457B94DC2A2B3698BF4EDEBBD73EA01F303CE0D216076DE7A0EDB82C298`.
- Web: fresh release build PASS; raw Cocos exit `36` принят только вместе с
  current terminal marker; required artifacts valid; matrix `34/34`, portrait
  и interaction PASS, restart `10/10`, diagnostics clean.
- Android: fresh x86_64 Cocos + Gradle build PASS; APK `142891427` bytes,
  SHA-256 `B2404E4A0DEAE5C8879576E87F39D34C692BBBA1E8BA191A991C4E998015C34C`.
- Android runtime: `33/33` unique events, matrix `28/28`, touch flow, custom
  name persistence и restart `10/10` PASS; targeted soak `30.598 s`, 34 input
  bursts, zero process loss and unexpected diagnostics.
- QA выполнялся только на QEMU `emulator-5554`; physical device не
  использовался. После QA приложение и эмулятор остановлены.
- Hygiene-gate: нет TODO/FIXME/HACK/XXX/debugger residue; temporary debug build
  `123875770` bytes и 8 superseded summaries удалены; final evidence retained.

## Review and corrected failures

- Cocos debug defines `DEBUG=true`, но `DEV=false`; первичная привязка к `DEV`
  давала zero events. Binding исправлен на compile-time `DEBUG`, после чего
  DEBUG Web и Android дали exact `33` events, release остался hard-off.
- Cocos иногда завершался с raw exit `36` между polling ticks после записи
  terminal marker. Router теперь выполняет финальный bounded scan только для
  exit `0` либо явно allowlisted caller-specific exit; marker обязан быть
  добавлен текущим запуском. Exit `7`, stale marker, markerless `36` и overflow
  остаются failure.
- Advisory-review верно указал на неоднозначный query parse: формы вроде `1e0`
  теперь отклоняются, допускаются только строки `1..10`. Finding о типе reset
  reason отклонён: union был валиден до review.
- Повторный heavy-review превысил 300 s и результата не вернул. Он не был
  принят как evidence; модель затем автоматически выгрузилась, unload
  подтверждён. Финальная проверка выполнена Codex и gates.
- Первая команда полного `tsc` использовала неверный локальный путь Cocos и не
  запускала компилятор. Точка входа исправлена на фактический bundled TypeScript
  под `C:\ProgramData\cocos\editors\Creator\3.8.8`; повтор — PASS.
- Первое закрытие source package выявило ошибку execution-plan validator: он
  считал историческую provenance-ссылку `complete unit -> complete source`
  повторным планированием. Алгоритм исправлен так, что только non-complete unit
  получает `COMPLETE_SOURCE_REPLANNED`; current plan и `10/10` tests — PASS.

## Scope exclusions

- Не выполнялись physical-device install/QA, production signing, Pages publish,
  Git push или release.
- Unrelated workspace, agent-monitor, Tasks, sticker-pack и project-library
  изменения не входят в checkpoint и не должны быть staged.

**Remaining:** `60` mandatory execution units и `7` conditional; ближайшая —
M03.4. Отдельные release blockers: production signing identity и immutable
Pages deployment/live parity.

**Next:** выполнить M03.4 как bounded input-adapter package: сначала inventory
jump/glide/dash/pause listener/debounce/side-effect order, затем один owner,
static contracts и полный Web + Android-emulator P4. Physical device не
использовать без отдельной команды.

## Restart receipt

1. Проверить commit, содержащий этот checkpoint, и clean-source canonical gate
   `temp/quality-gate-m03-3c/report-final-clean.json`.
2. Убедиться, что project scope чист, а посторонние root changes не staged.
3. Открыть `docs/global_modernization/v4/EXECUTION_UNIT_INDEX.json`: `M03.4`
   должен быть `ready`, ledger — `5/65`, remaining — `60`.
4. Перед правкой M03.4 сделать bounded inventory всех текущих input entrypoints
   и зафиксировать rollback boundary.
