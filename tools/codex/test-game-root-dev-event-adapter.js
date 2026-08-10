'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const qaRoot = path.join(projectRoot, 'assets', 'scripts', 'qa');
const adapterPath = path.join(qaRoot, 'GameRootDevEventAdapter.ts');
const devEventLogPath = path.join(qaRoot, 'DevEventLog.ts');
const devEventTypesPath = path.join(qaRoot, 'DevEventTypes.ts');
const lifecyclePath = path.join(qaRoot, 'LifecycleEpoch.ts');
const statePath = path.join(projectRoot, 'assets', 'scripts', 'gameplay', 'state', 'GameSessionState.ts');
const gameRootPath = path.join(projectRoot, 'assets', 'scripts', 'GameRoot.ts');
const appActivityPath = path.join(projectRoot, 'native', 'engine', 'android', 'app', 'src', 'com', 'cocos', 'game', 'AppActivity.java');
const webBuildConfigPath = path.join(projectRoot, 'build-web-mobile.json');
const emulatorBuildConfigPath = path.join(projectRoot, 'build-android-emulator.json');
const typescriptPath = process.env.COCOS_TYPESCRIPT_JS
  || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js';

const requiredPaths = [
  adapterPath,
  devEventLogPath,
  devEventTypesPath,
  lifecyclePath,
  statePath,
  gameRootPath,
  appActivityPath,
  webBuildConfigPath,
  emulatorBuildConfigPath,
  typescriptPath,
];
for (const requiredPath of requiredPaths) {
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
const program = ts.createProgram([
  adapterPath,
  devEventLogPath,
  devEventTypesPath,
  lifecyclePath,
  statePath,
], compilerOptions);
const diagnostics = ts.getPreEmitDiagnostics(program)
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error);
const diagnosticText = diagnostics.map((diagnostic) => {
  const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
  if (!diagnostic.file || diagnostic.start === undefined) return `${diagnostic.code}: ${message}`;
  const position = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
  return `${diagnostic.file.fileName}:${position.line + 1}:${position.character + 1} ${diagnostic.code}: ${message}`;
});
assert.deepStrictEqual(diagnosticText, [], `Strict TypeScript diagnostics:\n${diagnosticText.join('\n')}`);

const moduleCache = new Map();
function loadTypeScriptModule(filePath) {
  const resolved = path.resolve(filePath);
  if (moduleCache.has(resolved)) return moduleCache.get(resolved).exports;
  const loadedModule = { exports: {} };
  moduleCache.set(resolved, loadedModule);
  const transpiled = ts.transpileModule(fs.readFileSync(resolved, 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2015,
      strict: true,
    },
    fileName: resolved,
    reportDiagnostics: true,
  });
  const transpileErrors = (transpiled.diagnostics || [])
    .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
    .map((diagnostic) => `${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')}`);
  assert.deepStrictEqual(transpileErrors, [], `Transpile diagnostics:\n${transpileErrors.join('\n')}`);
  const load = new Function('exports', 'require', 'module', '__filename', '__dirname', transpiled.outputText);
  load(
    loadedModule.exports,
    (request) => {
      if (!request.startsWith('.')) throw new Error(`Unexpected dependency: ${request}`);
      const candidate = path.resolve(path.dirname(resolved), request.endsWith('.ts') ? request : `${request}.ts`);
      return loadTypeScriptModule(candidate);
    },
    loadedModule,
    resolved,
    path.dirname(resolved),
  );
  return loadedModule.exports;
}

const {
  GAME_ROOT_DEV_EVENT_CAPACITY,
  GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES,
  GameRootDevEventAdapter,
} = loadTypeScriptModule(adapterPath);
const { evaluateGameSessionTransition } = loadTypeScriptModule(statePath);

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

function completeReset(adapter, state, reason, tick = 0) {
  const epoch = adapter.beginReset(state, reason, tick);
  adapter.endReset(epoch, state, reason, 0);
  return epoch;
}

testGroup('release_disabled_log_still_advances_epoch', () => {
  const sink = [];
  const adapter = new GameRootDevEventAdapter({ eventsEnabled: false, onEvent: (event) => sink.push(event) });
  assert.strictEqual(adapter.eventsEnabled, false);
  assert.strictEqual(completeReset(adapter, 'menu', 'boot'), 1);
  assert.strictEqual(adapter.currentEpoch(), 1);
  assert.deepStrictEqual(adapter.snapshot(), []);
  assert.deepStrictEqual(sink, []);
  assert.strictEqual(adapter.exportJson(), '[]');
});

testGroup('one_reset_emits_exact_order_and_epoch', () => {
  const adapter = new GameRootDevEventAdapter({ eventsEnabled: true });
  assert.strictEqual(completeReset(adapter, 'menu', 'boot', 7), 1);
  const events = adapter.snapshot();
  assert.deepStrictEqual(events.map((event) => event.code), [
    'session.epoch.changed',
    'session.reset.begin',
    'session.reset.end',
  ]);
  assert.deepStrictEqual(events.map((event) => event.epoch), [1, 1, 1]);
  assert.deepStrictEqual(events.map((event) => event.sequence), [1, 2, 3]);
  assert.strictEqual(events[0].payload.previousEpoch, 0);
  assert.strictEqual(events[0].payload.currentEpoch, 1);
  assert.strictEqual(events[2].payload.currentEpoch, 1);
});

testGroup('transition_events_are_unique_and_do_not_write_state', () => {
  const adapter = new GameRootDevEventAdapter({ eventsEnabled: true });
  const accepted = evaluateGameSessionTransition('menu', 'name', 'ui_start_menu');
  const idempotent = evaluateGameSessionTransition('name', 'name', 'repeat');
  const rejected = evaluateGameSessionTransition('playing', 'menu', 'invalid_test');
  adapter.recordTransition(accepted, 1);
  adapter.recordTransition(idempotent, 2);
  adapter.recordTransition(rejected, 3);
  const events = adapter.snapshot();
  assert.deepStrictEqual(events.map((event) => event.code), [
    'session.transition.accepted',
    'session.transition.accepted',
    'session.transition.rejected',
  ]);
  assert.deepStrictEqual(events.map((event) => event.state), ['name', 'name', 'playing']);
  assert.deepStrictEqual(events.map((event) => event.payload.changed), [true, false, false]);
  assert.deepStrictEqual(events.map((event) => event.payload.result), ['accepted', 'accepted', 'invalid_transition']);
});

testGroup('reset_pairing_rejects_nested_and_stale_end', () => {
  const adapter = new GameRootDevEventAdapter({ eventsEnabled: true });
  const epoch = adapter.beginReset('menu', 'boot', 0);
  assert.throws(() => adapter.beginReset('menu', 'qa_reset_loop', 0), /cannot be nested/);
  assert.throws(() => adapter.endReset(epoch + 1, 'menu', 'boot', 0), /stale epoch/);
  adapter.endReset(epoch, 'menu', 'boot', 0);
  assert.throws(() => adapter.endReset(epoch, 'menu', 'boot', 0), /stale epoch/);
});

testGroup('guard_suppresses_work_after_next_reset', () => {
  const adapter = new GameRootDevEventAdapter({ eventsEnabled: true });
  completeReset(adapter, 'playing', 'start_level');
  let calls = 0;
  const guarded = adapter.guardSessionCallback(() => { calls += 1; });
  assert.strictEqual(guarded(), true);
  completeReset(adapter, 'playing', 'qa_reset_loop');
  assert.strictEqual(guarded(), false);
  assert.strictEqual(calls, 1);
});

testGroup('destroy_invalidation_advances_once_and_suppresses_guard', () => {
  const adapter = new GameRootDevEventAdapter({ eventsEnabled: true });
  completeReset(adapter, 'menu', 'boot');
  const guarded = adapter.guardSessionCallback(() => {});
  assert.strictEqual(adapter.invalidate('menu', 'component_destroy', 0), 2);
  assert.strictEqual(guarded(), false);
  const last = adapter.snapshot().slice(-1)[0];
  assert.strictEqual(last.code, 'session.epoch.changed');
  assert.strictEqual(last.reason, 'component_destroy');
  assert.strictEqual(last.payload.previousEpoch, 1);
  assert.strictEqual(last.payload.currentEpoch, 2);
});

testGroup('event_sink_is_observational_and_cannot_fail_gameplay', () => {
  const adapter = new GameRootDevEventAdapter({
    eventsEnabled: true,
    onEvent: () => { throw new Error('sink failure'); },
  });
  assert.doesNotThrow(() => completeReset(adapter, 'menu', 'boot'));
  assert.strictEqual(adapter.snapshot().length, 3);
});

testGroup('ten_loop_runtime_contract_is_exact', () => {
  const adapter = new GameRootDevEventAdapter({ eventsEnabled: true });
  completeReset(adapter, 'menu', 'boot');
  for (let index = 0; index < 10; index += 1) completeReset(adapter, 'menu', 'qa_reset_loop');
  const events = adapter.snapshot();
  const sequences = new Set(events.map((event) => event.sequence));
  assert.strictEqual(adapter.currentEpoch(), 11);
  assert.strictEqual(events.length, 33);
  assert.strictEqual(sequences.size, 33);
  assert.strictEqual(events.filter((event) => event.code === 'session.epoch.changed').length, 11);
  assert.strictEqual(events.filter((event) => event.code === 'session.reset.begin').length, 11);
  assert.strictEqual(events.filter((event) => event.code === 'session.reset.end').length, 11);
});

testGroup('ring_and_export_remain_bounded', () => {
  const adapter = new GameRootDevEventAdapter({ eventsEnabled: true });
  for (let index = 0; index < 60; index += 1) completeReset(adapter, 'menu', 'qa_reset_loop');
  const events = adapter.snapshot();
  assert.strictEqual(events.length, GAME_ROOT_DEV_EVENT_CAPACITY);
  assert.strictEqual(new Set(events.map((event) => event.sequence)).size, GAME_ROOT_DEV_EVENT_CAPACITY);
  const exported = adapter.exportJson();
  assert.ok(Buffer.byteLength(exported, 'utf8') <= GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES);
  const decoded = JSON.parse(exported);
  assert.ok(decoded.length <= GAME_ROOT_DEV_EVENT_CAPACITY);
  assert.strictEqual(
    JSON.stringify(decoded),
    JSON.stringify(events.slice(events.length - decoded.length)),
  );
});

testGroup('source_boundary_and_release_wiring', () => {
  const adapterSource = fs.readFileSync(adapterPath, 'utf8');
  const gameRootSource = fs.readFileSync(gameRootPath, 'utf8');
  const appActivitySource = fs.readFileSync(appActivityPath, 'utf8');
  const webBuildConfig = JSON.parse(fs.readFileSync(webBuildConfigPath, 'utf8'));
  const emulatorBuildConfig = JSON.parse(fs.readFileSync(emulatorBuildConfigPath, 'utf8'));
  for (const forbidden of ["from 'cc'", 'localStorage', 'fetch(', 'Date.', 'Math.random']) {
    assert.strictEqual(adapterSource.includes(forbidden), false, `Forbidden adapter marker: ${forbidden}`);
  }
  assert.strictEqual((gameRootSource.match(/this\.state\s*=\s*next/g) || []).length, 1);
  assert.ok(gameRootSource.includes("import { DEBUG } from 'cc/env';"));
  assert.ok(gameRootSource.includes('eventsEnabled: DEBUG'));
  assert.ok(gameRootSource.includes('onEvent: DEBUG ? logGameRootDevEvent : undefined'));
  assert.ok(gameRootSource.includes("this.reset('boot')"));
  assert.ok(gameRootSource.includes("this.reset('start_level')"));
  assert.ok(gameRootSource.includes("this.reset('qa_end_state')"));
  assert.ok(gameRootSource.includes("this.reset('qa_reset_loop')"));
  assert.ok(gameRootSource.includes("params.get('mtr_qa_reset_loops')"));
  assert.ok(gameRootSource.includes("if (!/^(?:[1-9]|10)$/.test(rawLoops))"));
  assert.ok(appActivitySource.includes('"mtr_qa_reset_loops"'));
  assert.strictEqual(webBuildConfig.debug, false);
  assert.strictEqual(emulatorBuildConfig.debug, true);
});

process.stdout.write(`${JSON.stringify({
  status: 'PASS',
  testGroups: passedGroups,
  strictTypeScript: true,
  typescriptVersion: ts.version,
  compilerTarget: 'ES2015',
  compilerPath: typescriptPath,
  capacity: GAME_ROOT_DEV_EVENT_CAPACITY,
  maxExportBytes: GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES,
  tenResetLoopEpoch: 11,
  tenResetLoopEvents: 33,
  releaseBuildEventsEnabled: false,
})}\n`);
