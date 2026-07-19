# Compatibility and conflict report — Tasks/5 v3 vs live MTR

Вердикт: `compatible_after_adaptation`; прямое копирование toolchain/runtime запрещено.

## Подтверждённая совместимость

- ожидаемый Cocos Creator 3.8 LTS совпадает с живым 3.8.8;
- порядок source truth → release recovery → seams → presentation/content → performance в целом корректен;
- M00–M12 покрывают все незавершённые пункты отчёта 14 июля;
- strangler-подход к `GameRoot.ts`, manifest ownership, fail-closed release gate и dry-run cleanup соответствуют проектным правилам;
- Web и Android должны строиться из общих configs/content contracts;
- PCG/DDA правильно отложены до telemetry, deterministic schemas и performance baseline.

## Реестр конфликтов и решений

| ID | Конфликт | Риск | Решение |
| --- | --- | --- | --- |
| C-001 | Пакет видел только отчёт 14 июля, не live repo | устаревшие статусы | M00 live revalidation выполнен; upstream статусы больше не считаются фактом сами по себе |
| C-002 | v3 допускает 1–2 risk-based цикла, AGENTS требует минимум 4, v2 содержит 7-domain QA | ложное сокращение QA | четыре инженерных gate обязательны для каждого patch; для module/release дополнительно сохраняются v2 QA7 и v3 two-pass/RC2 |
| C-003 | M10/чеклисты предполагают physical-device run | нарушение глобального emulator-only default | physical QA остаётся отдельным optional gate только по явной команде пользователя |
| C-004 | `AGENTS.template.md` неполон относительно live AGENTS/lore | потеря канона и Android/Web правил | template не копируется поверх AGENTS; полезные пункты включены только в этот план |
| C-005 | Рекомендуемая branch policy предполагает чистый baseline | потеря/смешение 592 project changes | branch/commit запрещены до diff classification и одобрения checkpoint contents |
| C-006 | M00 требует commit/tag/bundle в первой фазе | несанкционированная мутация | текущая фаза завершена на read-only inventory; freeze выделен в M00.B |
| C-007 | Actions Pages deployment предполагает source remote | основной remote отсутствует | сначала topology/remote ADR; существующий nested repo временно только независимый deployment source |
| C-008 | CI example использует `npm ci`, `npx tsc` и неверные working directories; прямой bundled `tsc -p` также падает на engine declarations/старом lib target | workflow гарантированно красный или проверяет не то | workflow принят только как reference; сохранить принятую project-only команду с `--skipLibCheck --lib es2020,dom --isolatedModules false` и протестировать wrapper |
| C-009 | Pages workflow содержит намеренный placeholder/failure | случайное включение блокирует deploy | не устанавливать; заменить только после воспроизводимого Cocos build command и artifact manifest |
| C-010 | `run-mtr-quality-gate.ps1` исполняет trusted command strings через `cmd.exe`, не обеспечивает заявленный timeout и ненадёжно пишет report paths | injection/false-green/hang | перепроектировать как typed step registry + `Start-Process` timeout + normalized absolute paths + structured stdout/stderr |
| C-011 | `verify-android-artifact.ps1` не гарантирует проверку `$LASTEXITCODE` native tools и почти не проверяет AAB | false PASS signing/ABI | заменить fail-closed verifier; отдельно тестировать invalid signature, missing ABI и bundletool path |
| C-012 | `verify-git-topology.ps1` ищет только `.git` directories | пропуск worktree/submodule `.git` files | использовать `git rev-parse`, porcelain worktree/submodule data и оба вида marker |
| C-013 | `sync-pages-dry-run.ps1 -Apply` использует `robocopy /MIR` | удаление destination и path escape | default dry-run сохранить; Apply требует отдельного approval, resolved-path containment и manifest comparison |
| C-014 | `scan_png_assets.py` слабее уже принятого asset/white-matte pipeline | false negatives/positives и деградация | не заменять `validate-assets.py` и `scan_and_fix_white_matte_edges.py`; использовать только как тестовый fixture/reference |
| C-015 | `build_content_manifest.py` называет output deterministic, но пишет absolute root и generatedAt | несравнимые byte-level manifests | разделить reproducible content fingerprint и run metadata; paths только relative/canonical |
| C-016 | Пакет формулирует Web/Android manifests как «match» | сырые platform outputs закономерно различаются | сравнивать shared logical content IDs/hashes/config aliases; platform-specific files проверять отдельными artifact manifests |
| C-017 | TypeScript seams компилируются, но неполны: state machine не валидирует transitions; audio router не реализует priority/maxSimultaneous; save fallback теряет corrupt payload | скрытая смена поведения/данных | хранить только в `library/drafts/reference_code`; перед runtime нужны project adapters и contract tests |
| C-018 | Новые schemas не имеют единого namespace/version migration с v2/current manifests | два конкурирующих source of truth | схемы помещены в `drafts`; M01 создаёт canonical IDs, adapters и migration matrix до их активации |
| C-019 | Смена signing key может нарушить update compatibility установленного package | невозможность обновления поверх приложения | сначала зафиксировать текущие fingerprints и distribution target; key migration — отдельное решение, secrets вне Git |
| C-020 | AAB объявлен P0 conditional без утверждённой Play цели | лишняя инфраструктура | direct APK и Play/AAB развести; AAB обязателен только после явного выбора Google Play |
| C-021 | Граф v3 одновременно делает X0/PCG блокером R2 и optional dependency | противоречивый release path | PCG остаётся отдельным experimental track, feature flag off; R2 не блокируется отсутствием M11 |
| C-022 | Внешние module statuses не учитывают реально выполненные v2 UI/skin/graphics этапы | повторная работа и риск регрессий | выполненное переводится в `revalidate_then_extend`, не в `redo` |
| C-023 | Evidence retention предлагает rotation, а живой corpus уже 1.05 GB | потеря важных якорей либо рост мусора | сначала SHA index и protected/recent/rotatable classification; delete только отдельным approved bounded batch |
| C-024 | External JSON Schema test требует необязательный `jsonschema` | неповторимый gate на текущей машине | dependency не установлена молча; M01 pin-ит isolated tool environment или выбирает уже доступный валидатор |
| C-025 | Tasks/5 extraction находится внутри dirty parent workspace | случайное попадание внешнего пакета в source commit | `Tasks/5/**` всегда исключать из MTR source checkpoint; хранить только provenance/hash и curated project contracts |

## Блокирующие решения пользователя перед release engineering

1. Git/Pages topology и remote основного source.
2. Distribution: direct APK, Google Play или оба.
3. Signing identity и backup ownership.
4. Разрешение на future physical-device QA, если оно понадобится; по умолчанию его нет.

Эти решения не блокируют дальнейшую подготовку M01/M03 contracts после source freeze, но блокируют production release claim.
