# Locked Node contract-test compiler

This private tool-only package replaces implicit reliance on a Windows Cocos
installation. It is not a dependency of the game, Web output or APK. It has one
exact dependency, official TypeScript5.8.2, the same compiler shipped with the
qualified Creator3.8.8 installation. The main compiler SHA-256 is verified equal
to that installation: `795E49E46D497CC16E4B02916B50CBCA257B4256D62CDDC4CC504103F7961027`.

From the project root on either Windows or Linux, with Node18+ and npm available:

```sh
npm ci --prefix tools/codex/node-test-toolchain --ignore-scripts --no-audit --no-fund
node tools/codex/test-node-test-toolchain.js
python tools/codex/quality-gate/bootstrap.py -- --project-root . --config tools/codex/quality-gate/static-gates.json --output temp/quality-gate-m01-6/report.json --content-version mtr-static-gates-v1
```

The hosted Windows/Linux matrix runs the same locked install before the same
canonical gate. `npm ci` checks the committed lock integrity; install scripts,
audit and funding requests are disabled. Tests themselves never download or
install anything. Missing compiler, wrong version, changed main compiler bytes,
altered registry/integrity, extra dependencies and lifecycle scripts fail closed.
`COCOS_TYPESCRIPT_JS` remains an explicit diagnostic override, but only an absolute
path to a compiler with the exact same version/main bytes is accepted. No implicit
Cocos/global/parent `node_modules` fallback exists. Existing strict diagnostics,
behavior assertions, gameplay groups and atlas comparison thresholds are retained.

`node_modules` is ignored, reproducible local cache; do not mirror it into Git,
assets, release bundles, project-library or another global skill/runtime root.
Updating this test compiler requires a separate reviewed pin/lock/test change.
This package does not prove runtime/emulator/Release acceptance.
