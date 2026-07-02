# Cleanup Plan

Generated: 2026-06-12 after texture10 background rebuild and main menu background 10.1 integration.

The final cleanup keeps only current runtime assets, current build outputs, current release artifacts, current documentation, and current evidence for the `nessesary/9` object-texture pipeline plus the `nessesary/10/Levels` background pipeline.

## Rules

- Keep Android and Web on the same runtime data.
- Keep Russian UI text.
- Keep the final release APK and Web build.
- Keep texture9 object evidence only where it documents the active object-pool pipeline.
- Keep texture10 background evidence only where it documents the active background pipeline.
- Remove stale reports, stale logs, temporary workspaces, old release outputs, inactive source iterations, old background prompt seeds, and inactive generator scripts.
- Do not delete active Cocos build/cache folders unless a clean rebuild task explicitly asks for it.

## Verification

After cleanup:

1. Run config validation.
2. Run active old-value scan.
3. Run backend/runtime/dependency audit.
4. Verify APK signing/badging.
5. Verify Web release through a local HTTP server.
6. Verify GitHub remote commit.
