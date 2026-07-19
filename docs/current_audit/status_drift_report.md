# Status drift report — 2026-07-19 vs 2026-07-14

Источник сравнения: `docs/qa/EXTERNAL_AUDIT_CURRENT_STATUS_AND_REMAINING_PLAN_20260714.md`.

## Подтверждено живой проверкой

| Утверждение 14 июля | Состояние 19 июля | Решение |
| --- | --- | --- |
| Основной HEAD `76bac6c...`, remote отсутствует | совпадает | confirmed |
| Основное дерево dirty | подтверждено; до создания v3-отчётов project scope содержал 592 записи: 8 modified, 2 deleted, 582 untracked | confirmed |
| Pages repo clean, HEAD `d7a7cc1...` | совпадает | confirmed |
| Pages topology неоднозначна | подтверждено: mode 160000 без `.gitmodules`, `git submodule status` падает | confirmed, severity raised |
| Web/Pages расходятся | подтверждено: 1 left-only, 5 right-only, 5 changed | confirmed |
| Текущий emulator APK — x86_64 | подтверждено через ZIP ABI inspection | confirmed |
| Arm APK устарел | последний build найден от 1 июля, до принятой линии 14 июля | confirmed |
| Signing не production-grade | emulator = Android Debug; arm = CocosCreator certificate | confirmed |
| AAB отсутствует | в build/releases/output не найден | confirmed |
| `GameRoot.ts` = 5 428 строк | совпадает, SHA-256 зафиксирован | confirmed |
| Cocos Creator 3.8.x | package и локальный executable подтверждают 3.8.8 | confirmed |
| QA evidence существует | 801 файл / 1 051 135 677 байт, полный SHA-256 index создан | confirmed |

## Изменения после отчёта

- Runtime/source файлов с `LastWriteTime` позже отчёта не обнаружено.
- Два emulator build log в evidence завершили запись в 19:26 14 июля; более новых runtime-артефактов нет.
- Добавлен и распакован Tasks/5 v3 audit package. Это внешнее рабочее сырьё, а не часть source baseline.
- В ходе текущего задания созданы только M00 audit indexes и проектная planning library v3.

## Не подтверждено повторным runtime

- сегодняшняя запускаемость Web build;
- сегодняшняя запускаемость emulator APK;
- 34/34 Web matrix, 28/28 Android matrix, restart и soak как свежий прогон;
- полный skin × pose × bonus lifecycle;
- live GitHub Pages URL и соответствие опубликованного deployment локальному Pages HEAD;
- физическое устройство и release performance.

Эти пункты не объявляются проваленными: они имеют статус `stale_evidence_requires_reproduction`. В текущем planning-only задании сборка и runtime намеренно не запускались.

## Итог дрейфа

Важного положительного или отрицательного runtime-дрейфа после 14 июля не найдено. Главный дрейф — процессный: объём незакоммиченных документов/evidence вырос, а source anchor, release parity и signing/AAB решения всё ещё отсутствуют.
