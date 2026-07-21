# M01.5 evidence-retention policy

Дата: 2026-07-21  
Статус: `ACTIVE FOR INDEX-FIRST DRY RUN / NO DELETE AUTHORITY`

## Область

Политика действует только на SHA-индексированный corpus `docs/qa/evidence` из `docs/current_audit/live_evidence_index.json`. Source, runtime assets, builds, release artifacts, Tasks/5, Hermes checkpoints и внешние M00 anchors не являются кандидатами этого dry-run.

## Классы и приоритет

1. `protected` — Markdown checkpoints, manifests, summaries, reports, results, `*final*.json`, indexes, hashes, rollback backups, replay/harness scripts, certificate/signing fingerprints и final-gate JSON. Эти файлы нельзя переводить в rotation автоматически.
2. `retained_recent` — все незащищённые файлы двух самых новых датированных evidence-групп, а также текущий failure corpus.
3. `rotatable` — более старые superseded screenshots, verbose logs и прочее evidence, которое не является anchor. Это только список для будущего ручного review, не разрешение на удаление.

При совпадении правил применяется порядок `protected` → `retained_recent` → `rotatable`. Каждый индексированный файл обязан получить ровно один класс.

## Index-first и path guards

- Сначала проверяются единичные byte snapshots policy/index и их SHA-256.
- Absolute, `..`, обратные слеши, Windows ADS (`:`), пустые сегменты и symlink/reparse escape блокируют dry-run.
- Absolute root из M00 index обязан совпасть с resolved `docs/qa/evidence`.
- Все 801 indexed paths должны существовать с тем же размером; unindexed files блокируют отчёт.
- Полный rehash 1.05 GB не выполняется: M00 SHA-256 остаются canonical, пока path/size reconciliation зелёный.
- Output разрешён только по exact reviewed path `docs/global_modernization/v3/M01/evidence_retention_dry_run.json`, внутри project root, вне evidence tree и вне protected inputs.
- Policy, index, accepted-run links и metadata всего corpus повторно проверяются непосредственно перед atomic replacement.

## Accepted-run links и identity

Dry-run проверяет и хеширует M00 evidence anchor, принятую M01.4 validation summary и checkpoint двух полных Web/Android QA-циклов. Current Git commit записывается отдельно от исторического `sourceHead` индекса.

Content version намеренно имеет статус `UNAVAILABLE_UNTIL_M02_2`. M01.5 не придумывает отсутствующую identity.

## Запрет Apply

Реализация не имеет аргумента, функции или ветви удаления evidence. `rotatable` означает `REVIEW_ONLY_FOR_FUTURE_APPROVED_ROTATION`. Единственный `unlink` очищает собственный same-directory `.tmp.<pid>` после неудачной atomic-записи отчёта и не может адресовать evidence tree.

Будущий cleanup возможен только отдельным bounded package после:

1. явного approval;
2. backup/rollback manifest с SHA-256;
3. повторного hidden-reference и path-guard аудита;
4. измерения свободного места;
5. rebuild и targeted/full QA после каждого approved batch.

До выполнения этих условий удаление запрещено.
