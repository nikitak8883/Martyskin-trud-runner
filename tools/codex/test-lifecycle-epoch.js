'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const sourcePath = path.join(projectRoot, 'assets', 'scripts', 'qa', 'LifecycleEpoch.ts');
const gameRootPath = path.join(projectRoot, 'assets', 'scripts', 'GameRoot.ts');
const typescriptPath = process.env.COCOS_TYPESCRIPT_JS
  || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js';

for (const requiredPath of [sourcePath, gameRootPath, typescriptPath]) {
  if (!fs.existsSync(requiredPath)) throw new Error(`Required file not found: ${requiredPath}`);
}

const ts = require(typescriptPath);
const compilerOptions = {
  module: ts.ModuleKind.CommonJS,
  moduleResolution: ts.ModuleResolutionKind.Node10,
  target: ts.ScriptTarget.ES2015,
  strict: true,
  noEmit: true,
  skipLibCheck: true,
};
const program = ts.createProgram([sourcePath], compilerOptions);
const diagnostics = ts.getPreEmitDiagnostics(program)
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error);
const diagnosticText = diagnostics.map((diagnostic) => {
  const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
  if (!diagnostic.file || diagnostic.start === undefined) return `${diagnostic.code}: ${message}`;
  const position = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
  return `${diagnostic.file.fileName}:${position.line + 1}:${position.character + 1} ${diagnostic.code}: ${message}`;
});
assert.deepStrictEqual(diagnosticText, [], `Strict TypeScript diagnostics:\n${diagnosticText.join('\n')}`);

const transpiled = ts.transpileModule(fs.readFileSync(sourcePath, 'utf8'), {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2015,
    strict: true,
  },
  fileName: sourcePath,
  reportDiagnostics: true,
});
const transpileErrors = (transpiled.diagnostics || [])
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
  .map((diagnostic) => `${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')}`);
assert.deepStrictEqual(transpileErrors, [], `Transpile diagnostics:\n${transpileErrors.join('\n')}`);

const loadedModule = { exports: {} };
const load = new Function(
  'exports',
  'require',
  'module',
  '__filename',
  '__dirname',
  transpiled.outputText,
);
load(
  loadedModule.exports,
  (request) => { throw new Error(`Unexpected dependency: ${request}`); },
  loadedModule,
  sourcePath,
  path.dirname(sourcePath),
);
const { LifecycleEpoch } = loadedModule.exports;

let passedGroups = 0;
function testGroup(name, callback) {
  try {
    callback();
    passedGroups += 1;
  } catch (error) {
    error.message = `${name}: ${error.message}`;
    throw error;
  }
}

async function testGroupAsync(name, callback) {
  try {
    await callback();
    passedGroups += 1;
  } catch (error) {
    error.message = `${name}: ${error.message}`;
    throw error;
  }
}

testGroup('default_and_initial_values', () => {
  const zero = new LifecycleEpoch();
  assert.strictEqual(zero.current(), 0);
  assert.strictEqual(Object.is(zero.current(), -0), false);
  assert.strictEqual(new LifecycleEpoch(-0).current(), 0);
  assert.strictEqual(new LifecycleEpoch(42).current(), 42);
  assert.strictEqual(new LifecycleEpoch(Number.MAX_SAFE_INTEGER).current(), Number.MAX_SAFE_INTEGER);
});

testGroup('invalid_initial_values', () => {
  for (const value of [
    -1,
    0.5,
    NaN,
    Infinity,
    -Infinity,
    Number.MAX_SAFE_INTEGER + 1,
    '0',
    null,
    Symbol('epoch'),
  ]) {
    assert.throws(() => new LifecycleEpoch(value), /non-negative safe integer/);
  }
});

testGroup('capture_and_current_are_stable', () => {
  const epoch = new LifecycleEpoch(7);
  assert.strictEqual(epoch.capture(), 7);
  assert.strictEqual(epoch.current(), 7);
  assert.strictEqual(epoch.capture(), epoch.current());
});

testGroup('advance_is_monotonic', () => {
  const epoch = new LifecycleEpoch();
  assert.strictEqual(epoch.advance(), 1);
  assert.strictEqual(epoch.advance(), 2);
  assert.strictEqual(epoch.current(), 2);
});

testGroup('is_current_rejects_invalid_stale_and_future_values', () => {
  const epoch = new LifecycleEpoch(3);
  assert.strictEqual(epoch.isCurrent(3), true);
  for (const value of [2, 4, -1, 3.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1, '3']) {
    assert.strictEqual(epoch.isCurrent(value), false);
  }
});

testGroup('guard_executes_and_forwards_arguments', () => {
  const epoch = new LifecycleEpoch(5);
  const calls = [];
  const guarded = epoch.guard((...args) => calls.push(args));
  assert.strictEqual(guarded('alpha', 2), true);
  assert.deepStrictEqual(calls, [['alpha', 2]]);
});

testGroup('guard_becomes_stale_after_advance', () => {
  const epoch = new LifecycleEpoch();
  let calls = 0;
  const guarded = epoch.guard(() => { calls += 1; });
  epoch.advance();
  assert.strictEqual(guarded(), false);
  assert.strictEqual(guarded(), false);
  assert.strictEqual(calls, 0);
});

testGroup('guard_captures_internally_and_cannot_future_activate', () => {
  const epoch = new LifecycleEpoch();
  assert.throws(() => epoch.guard(1, () => {}), /callback must be a function/);
  const currentGuard = epoch.guard(() => {});
  epoch.advance();
  assert.strictEqual(currentGuard(), false);
  epoch.advance();
  assert.strictEqual(currentGuard(), false);
});

testGroup('numeric_tokens_are_captured_snapshots_not_future_guards', () => {
  const epoch = new LifecycleEpoch();
  const captured = epoch.capture();
  const synthesizedFuture = captured + 1;
  assert.strictEqual(epoch.isCurrent(captured), true);
  assert.strictEqual(epoch.isCurrent(synthesizedFuture), false);
  epoch.advance();
  assert.strictEqual(epoch.isCurrent(captured), false);
  assert.strictEqual(epoch.isCurrent(synthesizedFuture), true);
  const guardCapturedBeforeAdvance = new LifecycleEpoch().guard(() => {});
  assert.strictEqual(guardCapturedBeforeAdvance(), true);
});

testGroup('guard_validates_callback', () => {
  const epoch = new LifecycleEpoch();
  for (const value of [undefined, null, 0, {}, 'callback']) {
    assert.throws(() => epoch.guard(value), /callback must be a function/);
  }
});

testGroup('callback_exception_propagates', () => {
  const epoch = new LifecycleEpoch();
  const expected = new Error('callback-failure');
  const guarded = epoch.guard(() => { throw expected; });
  assert.throws(() => guarded(), (error) => error === expected);
  assert.strictEqual(epoch.current(), 0);
});

testGroup('callback_advance_invalidates_later_invocations', () => {
  const epoch = new LifecycleEpoch();
  let calls = 0;
  const guarded = epoch.guard(() => {
    calls += 1;
    epoch.advance();
  });
  assert.strictEqual(guarded(), true);
  assert.strictEqual(guarded(), false);
  assert.strictEqual(calls, 1);
});

testGroup('instances_are_independent', () => {
  const first = new LifecycleEpoch();
  const second = new LifecycleEpoch();
  const firstGuard = first.guard(() => {});
  const secondGuard = second.guard(() => {});
  first.advance();
  assert.strictEqual(firstGuard(), false);
  assert.strictEqual(secondGuard(), true);
  assert.strictEqual(second.current(), 0);
});

testGroup('overflow_fails_before_mutation', () => {
  const epoch = new LifecycleEpoch(Number.MAX_SAFE_INTEGER - 1);
  assert.strictEqual(epoch.advance(), Number.MAX_SAFE_INTEGER);
  assert.throws(() => epoch.advance(), /exhausted/);
  assert.strictEqual(epoch.current(), Number.MAX_SAFE_INTEGER);
  assert.throws(() => epoch.advance(), /exhausted/);
  assert.strictEqual(epoch.current(), Number.MAX_SAFE_INTEGER);
});

testGroup('source_boundary_and_zero_wiring', () => {
  const source = fs.readFileSync(sourcePath, 'utf8');
  const gameRoot = fs.readFileSync(gameRootPath, 'utf8');
  assert.strictEqual(/^\s*import\s/m.test(source), false);
  for (const forbidden of ['Date.', 'Math.random', 'console.', 'localStorage', 'fetch(', 'scheduleOnce']) {
    assert.strictEqual(source.includes(forbidden), false, `Forbidden source marker: ${forbidden}`);
  }
  assert.strictEqual(gameRoot.includes('LifecycleEpoch'), false);
});

(async () => {
  await testGroupAsync('async_continuation_requires_its_own_ownership_check', async () => {
    const epoch = new LifecycleEpoch();
    let continuedAfterAwait = false;
    const guarded = epoch.guard(async () => {
      await Promise.resolve();
      continuedAfterAwait = true;
    });
    assert.strictEqual(guarded(), true);
    epoch.advance();
    await Promise.resolve();
    assert.strictEqual(continuedAfterAwait, true);
    assert.strictEqual(epoch.current(), 1);
  });

  process.stdout.write(`${JSON.stringify({
    status: 'PASS',
    testGroups: passedGroups,
    strictTypeScript: true,
    typescriptVersion: ts.version,
    compilerTarget: 'ES2015',
    compilerPath: typescriptPath,
    guardCapturesInternally: true,
    guardSemantics: 'SYNCHRONOUS_ENTRY_ONLY',
    numericTokenPolicy: 'CAPTURED_SNAPSHOTS_ONLY',
    gameRootWired: false,
  })}\n`);
})().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
});
