# M02.2 code-review report

Date: 2026-07-22  
Verdict: `PASS FOR BOUNDED M02.2`

## Diff boundary

- one Cocos JSON identity asset and its importer metadata;
- one standard-library Python validator;
- five pure negative/positive unit tests;
- one no-build preflight and report extension in the existing Cocos wrapper;
- one new mandatory static-gate step;
- checkout-stable line-ending rules for hashed identity inputs;
- this parity contract and review record.

No gameplay source, scene, texture, UI, save data, build config, generated build, APK, browser runtime, emulator, physical device, signing material or Pages tree changed.

## Review findings

| Concern | Result |
| --- | --- |
| Identity metadata could reference its own enclosing commit | Prevented by the documented immutable pre-metadata public baseline. |
| Web and Android could report different logical versions | Prevented by one canonical asset and three actual wrapper preflights compared by the validator. |
| A shared logical identity could accidentally become a shared artifact manifest | Prevented by separate `platformArtifactManifest` objects with `per-platform` scope and target/output ownership. |
| An alternate identity file could be supplied to the wrapper | Prevented by canonical resolved-path equality plus project-root containment. |
| Source/freeze provenance could silently drift | Prevented by strict source fields, reachable baseline check and exact M00 manifest comparison. |
| Windows/Linux checkout could produce different identity hashes | Prevented by exact LF rules for identity JSON/meta and the validator source. |
| Validator output could overwrite an arbitrary path | Prevented by project containment and atomic temporary-file replacement. |
| Preflight could invoke Cocos or mutate builds | Prevented: `-ValidateContentIdentityOnly` returns before the build entrypoint; all artifact states are `NOT_BUILT`. |
| Legacy consumers could break | Prevented: existing `webPostProcess` and `androidPostPackage` output fields are retained. |
| Hosted shallow checkout could not prove baseline ancestry | Observed fail-closed on both OS in run `29896755871`; corrected to full source history instead of weakening the validator. |

## Local evidence before commit

- Python and JSON syntax: `PASS`.
- PowerShell parser: `PASS`.
- Content identity unit tests: `5/5 PASS`.
- Repository validator: `PASS`, 3/3 build-config preflights, 0 findings.
- Shared identity file SHA-256: `F8362EC17295FD646E335C501B40A24871E3B40C1CBA22B6A4C0F36AD9313395`.
- Cocos metadata SHA-256: `135824A44562019CB1C2A1FA7783552303813A3C0882EF1A8BA90CD755E43C3C`.
- Development full static gate `qg.20260722062427.cb31e1f5e6da`: `8/8 PASS`, 0 findings, source stable; 52 tests ran with 3 expected platform/privilege skips. Dirty-source authorization was explicit and is not final acceptance.
- Development gate report SHA-256: `EDDC1D87C896050C8B7A7D36D9FFEC6D97A454D69B80B34C494E0FD1B07A5CEA`.

## Accepted clean and hosted evidence

- Clean local gate `qg.20260722063249.cb31e1f5e6da`: `8/8 PASS`, 0 findings, source clean and stable, report SHA-256 `0D9FC16002EE28A4846B052ECD669B18DEDBFEA2157DD940F6380E5E2D64C38A`.
- Hosted run `29897120642` on published source `707ab97ad30bbfe7014c421c96c52ecfec5feaf7`: Ubuntu and Windows both `8/8 PASS`, 0 findings.
- Both hosted validators produced the same identity SHA-256 and metadata SHA-256, and each executed 3/3 Web/Android no-build preflights.
- Both hosted suites ran 52 tests with 2 expected platform skips and no failures.

M02.2 establishes report identity only. M02.3–M02.5 still own actual Web, emulator and arm artifact/runtime evidence, and the overall release remains blocked.
