# M02.2 Web/Android content parity contract

Date: 2026-07-22  
Status: `IMPLEMENTED / RELEASE STILL BLOCKED`

## Purpose

Every Web or Android build report must carry one identical logical content identity. Platform artifacts remain separate records because a Web directory, an emulator APK and an arm64 APK have different files, hashes, packaging and acceptance gates.

The shared identity is a provenance key, not an artifact hash and not a release approval.

## Canonical identity

Source asset: `assets/resources/config/content_identity.json`  
Cocos metadata: `assets/resources/config/content_identity.json.meta`

| Field | Accepted value |
| --- | --- |
| Contract | `mtr.content_identity` v1 |
| Logical content version | `mtr-v3-source-a5c4bdbb2fca` |
| Repository | `https://github.com/nikitak8883/Martyskin-trud-runner.git` |
| Source branch | `mtr-source-v3` |
| Public baseline commit | `a5c4bdbb2fca479ad918ea7f3fa4fdd40bdffce2` |
| Baseline kind | `published_source_before_identity_metadata` |
| Original M00 freeze | `mtr-v3-freeze-12670452ae45` at parent commit `12670452ae4580ef5c685ff986476daf91522978` |
| M00 aggregate SHA-256 | `E3C72CE3D41BAA9EA54D9941A6A91312DFD38A94112C99ADC02D935915A8EDFD` |

The public baseline is deliberately the last published source commit before this identity file was added. A metadata file cannot contain the SHA of the commit that contains itself; using the immediately preceding immutable commit avoids a circular/self-invalidating identity. The nested M00 provenance preserves the earlier full-source fingerprint independently.

## Build-report contract

`tools/Run-MtrCocosBuild.ps1` validates the identity before starting Cocos Creator. Both preflight and real build reports expose:

```text
contract: mtr.cocos_build_report (real build)
targetPlatform: web-mobile | android
contentIdentity: identical shared object
platformArtifactManifest: target-specific object
```

The `contentIdentity` object contains the logical version, public source baseline, immutable identity-file SHA-256 and M00 freeze aggregate. It must compare equal in Web, emulator-Android and arm-Android reports.

The `platformArtifactManifest` object is never shared:

- `platform=web-mobile`, `outputName=web-mobile` for the Web tree;
- `platform=android`, `outputName=android-emulator` for the x86_64 emulator line;
- `platform=android`, `outputName=android` for the arm line.

M02.2 establishes the envelope and separation. M02.3–M02.5 must populate and verify the concrete per-platform files, counts, hashes, ABIs, package/signature fields and runtime evidence. They must not copy an Android artifact hash into Web evidence or vice versa.

The legacy `webPostProcess` and `androidPostPackage` fields remain for backward compatibility. Their relevant value is also nested under the matching `platformArtifactManifest`; the opposite platform value remains absent/null.

## Fail-closed rules

The build wrapper exits before Cocos starts when any of these is true:

- the canonical identity or Cocos `.meta` input is missing or malformed;
- the identity path escapes the project or is replaced by an alternate file;
- repository, branch, source commit, logical version or platform fields drift;
- M00 freeze provenance no longer matches the protected source manifest;
- the selected build config is not `web-mobile` or `android`;
- the selected platform is absent from the shared identity.

`tools/validate-content-identity.py` additionally requires:

- exact object fields and formats;
- a reachable public baseline commit on the current/canonical source refs;
- valid Cocos JSON metadata;
- one Web and two Android build configs;
- successful no-build PowerShell preflight for all three configs;
- byte-identical `contentIdentity` output across all preflights;
- separate `per-platform` artifact envelopes;
- contained atomic report writes.

The validator is the eighth mandatory step in `tools/codex/quality-gate/static-gates.json`; failure blocks both local and hosted matrices.

## Bump policy

Create and publish a new pre-metadata baseline, then update the identity and logical version when changing runtime code, runtime assets, content configuration, a scene, or shared build behavior.

An identity bump is not required for audit-only documentation, rotating QA evidence, or CI-only tooling that cannot affect packaged/runtime content. Any uncertainty is resolved fail-closed: treat the change as content-affecting and bump after a reviewed public baseline.

## Commands

No-build target preflight:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-web-mobile.json -ValidateContentIdentityOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-android-emulator.json -ValidateContentIdentityOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-MtrCocosBuild.ps1 -ConfigPath .\build-android.json -ValidateContentIdentityOnly
```

Cross-platform contract validation:

```text
python tools/validate-content-identity.py --project-root .
```

M02.2 runs only these preflight/static checks. Cocos builds, browser runtime, emulator install/launch, physical device, signing and Pages deployment belong to later packages and are not implied.

## Rollback

Revert the M02.2 identity asset/meta, validator/tests, wrapper report fields, static-gate step and this contract together. Do not revert only the validator while leaving unverified identity output in build reports.
