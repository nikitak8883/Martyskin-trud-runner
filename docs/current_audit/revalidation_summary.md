# M00 read-only revalidation summary

```yaml
revalidation_status: partial_pass_release_blocked
generated_at: 2026-07-19
mode: planning_and_read_only_inventory
confirmed_claims:
  - primary HEAD and absent remote
  - dirty source tree
  - invalid intermediate Pages gitlink topology
  - Web versus Pages content drift
  - current x86_64 emulator APK identity
  - stale arm APK identity and Cocos signing
  - no AAB
  - Cocos Creator 3.8.8
  - GameRoot.ts remains 5428 lines
  - QA evidence corpus exists and is hash-indexed
changed_claims:
  - Tasks/5 library and current audit outputs add untracked planning material
  - no runtime source change after the 2026-07-14 report was detected
unverified_claims:
  - current Web runtime matrix
  - current Android emulator runtime matrix
  - current restart and soak behavior
  - complete skin lifecycle matrix
  - live Pages deployment state
  - physical-device performance
release_blockers:
  - no reviewed immutable source commit/tag
  - primary source remote absent
  - Pages gitlink has no .gitmodules mapping
  - Web/Pages parity failure
  - no current device-valid arm64 artifact from accepted source
  - no production signing policy
  - no embedded content version
  - no AAB if Google Play becomes an approved target
proposed_checkpoint_contents:
  - reviewed runtime source and required assets/meta
  - canonical shared Android/Web configs
  - required native source
  - validated tools and QA harnesses
  - canonical docs plus compact evidence indexes
  - approved v2/v3 project contracts
proposed_exclusions:
  - build/library/temp/output/local indexes
  - raw evidence and loose logs
  - external task archives and extracted packages
  - release binaries outside an approved artifact store/index
  - secrets, keystores and local machine settings
  - nested Pages working tree from parent staging
next_safe_action: review and approve the M00 checkpoint classification and Git topology decision before any freeze commit or runtime modernization
```

## Что выполнено

- внешний архив и оба уровня manifest/checksum проверены;
- выполнена синтаксическая проверка JSON, YAML, Python, PowerShell и TypeScript reference code;
- встроенные Python tests повторены на Windows: 2/2 PASS;
- JSON Schema validation не повторена: опциональный пакет `jsonschema` отсутствует и не устанавливался молча;
- живые Git, Web, Android, Cocos и QA-evidence факты проиндексированы;
- runtime/build/publish/signing/cleanup не запускались.

## Зафиксированные сбои текущего аудита

1. Первый механический copy использовал `Copy-Item -LiteralPath` с wildcard и скопировал 0 файлов. Команда немедленно заменена на безопасный `Copy-Item -Path`; итог проверен: 9 schema, 8 TypeScript reference и 6 template файлов.
2. `local_worker.retrieve_context` не вернул результат за ограниченное ожидание и был остановлен. Анализ продолжен по прямым, ограниченным локальным файлам; тяжёлая модель не запускалась. Созданные неуспешным запросом два cache-файла `.local_ai_index/queries/f91d39b5ec7e815c.*` удалены hygiene gate как временный хвост.
3. Прямой bundled `tsc -p tsconfig.json --noEmit` воспроизвёл ошибки Cocos engine declarations и ES lib target. По принятому evidence найдена корректная project-only команда; повтор с `--skipLibCheck --lib es2020,dom --isolatedModules false` завершился PASS. Внешний `npx tsc` не принимается как gate без wrapper.
4. Первый финальный leftover scan был запущен из workspace root с project-relative путями и вернул path errors. Повтор из канонического project root проверил 40 файлов / 434 808 байт; временных, пустых или debug-хвостов не найдено.

Оба события не изменили runtime и включены в отчёт, чтобы следующая сессия не повторяла те же попытки.
