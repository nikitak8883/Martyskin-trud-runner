'use strict';

const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const guard = require('./load_test_typescript');
const root = path.join(__dirname, 'node-test-toolchain');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const lock = JSON.parse(fs.readFileSync(path.join(root, 'package-lock.json'), 'utf8'));
const results = [];
function test(name, body) { body(); results.push(name); }
function clone(value) { return JSON.parse(JSON.stringify(value)); }

test('isolated-version-integrity-lock-is-exact', () => {
  assert.equal(guard.validateTestToolchainManifest(manifest, lock), true);
});
for (const [name, mutate] of [
  ['version-range', (m) => { m.dependencies.typescript = '^5.8.2'; }],
  ['extra-dependency', (m) => { m.dependencies.other = '1.0.0'; }],
  ['lifecycle-script', (m) => { m.scripts = { postinstall: 'echo unsafe' }; }],
  ['publishable-package', (m) => { m.private = false; }],
  ['lock-version', (m, l) => { l.packages['node_modules/typescript'].version = '5.8.3'; }],
  ['lock-registry', (m, l) => { l.packages['node_modules/typescript'].resolved = 'https://example.invalid/compiler.tgz'; }],
  ['lock-integrity', (m, l) => { l.packages['node_modules/typescript'].integrity = 'sha512-invalid'; }],
  ['extra-package', (m, l) => { l.packages['node_modules/other'] = { version: '1.0.0' }; }],
  ['lock-install-script', (m, l) => { l.packages['node_modules/typescript'].hasInstallScript = true; }],
]) {
  test(`reject-${name}`, () => {
    const m = clone(manifest), l = clone(lock);
    mutate(m, l);
    assert.throws(() => guard.validateTestToolchainManifest(m, l), /Invalid isolated/);
  });
}
const live = guard.loadTestTypeScript({ override: undefined });
test('default-is-locked-local-compiler', () => {
  assert.equal(live.source, 'isolated-lock');
  assert.equal(live.compiler.version, '5.8.2');
  assert.ok(live.compilerPath.startsWith(fs.realpathSync(root) + path.sep));
});
test('explicit-identical-compiler-override-accepted', () => {
  const observed = guard.loadTestTypeScript({ override: live.compilerPath });
  assert.equal(observed.source, 'explicit-verified-override');
  assert.equal(observed.compiler, live.compiler);
});
test('relative-override-fails-before-require', () => {
  assert.throws(() => guard.loadTestTypeScript({ override: 'compiler.js' }), /must be absolute/);
});
test('missing-override-fails-no-fallback', () => {
  assert.throws(() => guard.loadTestTypeScript({ override: path.join(root, 'missing-compiler.js') }), /Pinned test compiler unavailable/);
});

const tempRoot = path.resolve(__dirname, '..', '..', 'temp');
fs.mkdirSync(tempRoot, { recursive: true });
const fixture = fs.mkdtempSync(path.join(tempRoot, 'node-toolchain-negative-'));
try {
  fs.writeFileSync(path.join(fixture, 'package.json'), JSON.stringify(manifest));
  fs.writeFileSync(path.join(fixture, 'package-lock.json'), JSON.stringify(lock));
  test('missing-installed-package-fails-with-install-command', () => {
    assert.throws(() => guard.loadTestTypeScript({ toolchainRoot: fixture, override: undefined }), /Install with: npm ci --prefix/);
  });
  const packageRoot = path.join(fixture, 'node_modules', 'typescript');
  fs.mkdirSync(path.join(packageRoot, 'lib'), { recursive: true });
  const compiler = path.join(packageRoot, 'lib', 'typescript.js');
  fs.writeFileSync(path.join(packageRoot, 'package.json'), JSON.stringify({ name: 'typescript', version: '5.8.3' }));
  fs.writeFileSync(compiler, 'global.__mtrBadCompilerExecuted = true;');
  test('wrong-version-fails-before-code-execution', () => {
    assert.throws(() => guard.loadTestTypeScript({ toolchainRoot: fixture, override: undefined }), /version mismatch/);
    assert.equal(global.__mtrBadCompilerExecuted, undefined);
  });
  fs.writeFileSync(path.join(packageRoot, 'package.json'), JSON.stringify({ name: 'typescript', version: '5.8.2' }));
  test('wrong-bytes-fail-before-code-execution', () => {
    assert.throws(() => guard.loadTestTypeScript({ toolchainRoot: fixture, override: undefined }), /SHA-256 mismatch/);
    assert.equal(global.__mtrBadCompilerExecuted, undefined);
  });
} finally {
  // Only this test-owned mkdtemp tree, never an external symlink or user path.
  if (fs.lstatSync(fixture).isSymbolicLink() || path.dirname(fs.realpathSync(fixture)) !== fs.realpathSync(tempRoot)
      || path.dirname(fixture) !== tempRoot || !path.basename(fixture).startsWith('node-toolchain-negative-')) {
    throw new Error('Fixture cleanup path escaped its owner');
  }
  fs.rmSync(fixture, { recursive: true, force: true });
}
test('all-nine-behavior-tests-use-shared-loader', () => {
  for (const stem of ['game-session-state', 'gameplay-input-adapter', 'gameplay-collision-router', 'powerup-lifecycle',
    'game-runtime-ownership', 'dev-event-log', 'game-root-dev-event-adapter', 'lifecycle-epoch', 'atlas-pilot-metrics']) {
    const source = fs.readFileSync(path.join(__dirname, `test-${stem}.js`), 'utf8');
    assert.ok(source.includes("require('./load_test_typescript').loadTestTypeScript()"), stem);
    assert.ok(!source.includes('C:/ProgramData/cocos/'), stem);
  }
});
test('hosted-matrix-installs-lock-without-lifecycle-scripts', () => {
  const workflow = fs.readFileSync(path.join(__dirname, '..', '..', '.github', 'workflows', 'mtr-static-gates.yml'), 'utf8');
  assert.ok(workflow.includes(guard.installCommand));
  assert.ok(workflow.indexOf(guard.installCommand) < workflow.indexOf('name: Run the canonical static gate'));
});
console.log(JSON.stringify({ status: 'PASS', passed: results.length, total: results.length, tests: results,
  typescriptVersion: live.compilerVersion, compilerSha256: live.compilerSha256, networkDuringTests: false }));
