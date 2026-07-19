# Quality evidence adapters

Эта папка содержит reference implementation M01.2, а не активный quality runner.

- `quality_adapter_registry.json` — allowlist current/historical/data source schemas.
- `quality_evidence_adapter.py` — dependency-free normalization и fail-closed runtime guard.

Adapter принимает native JSON report и отдельный trusted context. Контекст обязан содержать source/content identity, target, report/tool hashes, strict flags и timing. Он не должен собираться из непроверенных полей самого отчёта.

CLI печатает envelope только в stdout. Atomic file writes, process execution, timeout, environment isolation и generic JSON Schema engine принадлежат M01.3 runner.

Self-test:

```powershell
python .\docs\global_modernization\v3\library\tests\validate_m01_2_contracts.py
```

Код под `docs/global_modernization/v3/library/` нельзя импортировать из Cocos runtime.

