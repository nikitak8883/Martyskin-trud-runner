'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const uiAdapterPath = path.join(projectRoot, 'assets', 'scripts', 'gameplay', 'ui', 'GameplayUiIntentAdapter.ts');
const lifecyclePath = path.join(projectRoot, 'assets', 'scripts', 'gameplay', 'lifecycle', 'GameRuntimeLifecycleOwner.ts');
const statePath = path.join(projectRoot, 'assets', 'scripts', 'gameplay', 'state', 'GameSessionState.ts');
const typescriptPath = process.env.COCOS_TYPESCRIPT_JS
  || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js';

for (const requiredPath of [uiAdapterPath, lifecyclePath, statePath, typescriptPath]) {
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
const program = ts.createProgram([uiAdapterPath, lifecyclePath, statePath], compilerOptions);
const diagnostics = ts.getPreEmitDiagnostics(program)
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
  .map((diagnostic) => {
    const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
    if (!diagnostic.file || diagnostic.start === undefined) return `${diagnostic.code}: ${message}`;
    const position = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
    return `${diagnostic.file.fileName}:${position.line + 1}:${position.character + 1} ${diagnostic.code}: ${message}`;
  });
assert.deepStrictEqual(diagnostics, [], `Strict TypeScript diagnostics:\n${diagnostics.join('\n')}`);

function loadTypeScriptModule(filePath) {
  const transpiled = ts.transpileModule(fs.readFileSync(filePath, 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2015,
      strict: true,
    },
    fileName: filePath,
    reportDiagnostics: true,
  });
  const errors = (transpiled.diagnostics || [])
    .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
    .map((diagnostic) => `${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')}`);
  assert.deepStrictEqual(errors, [], `Transpile diagnostics for ${filePath}:\n${errors.join('\n')}`);
  const loadedModule = { exports: {} };
  const load = new Function('exports', 'require', 'module', '__filename', '__dirname', transpiled.outputText);
  load(
    loadedModule.exports,
    (request) => { throw new Error(`Unexpected runtime dependency in ${filePath}: ${request}`); },
    loadedModule,
    filePath,
    path.dirname(filePath),
  );
  return loadedModule.exports;
}

const { GameplayUiIntentAdapter } = loadTypeScriptModule(uiAdapterPath);
const { GameRuntimeLifecycleOwner } = loadTypeScriptModule(lifecyclePath);

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

function createUiHarness(initialState = 'menu') {
  const control = { state: initialState, levelCount: 15, skinCount: 8, navigateAccepted: true };
  const calls = [];
  const adapter = new GameplayUiIntentAdapter({
    getSessionState: () => control.state,
    getLevelCount: () => control.levelCount,
    getSkinCount: () => control.skinCount,
    onNavigate: (next, reason) => {
      calls.push({ action: 'navigate', next, reason });
      return control.navigateAccepted;
    },
    onStartLevel: (levelIndex) => calls.push({ action: 'start_level', levelIndex }),
    onPreviewSkin: (skinIndex) => calls.push({ action: 'preview_skin', skinIndex }),
    onConfirmSkin: () => calls.push({ action: 'confirm_skin' }),
    onOpenDeveloperGate: () => calls.push({ action: 'open_developer_gate' }),
    onSubmitDeveloperGate: () => calls.push({ action: 'submit_developer_gate' }),
  });
  return { adapter, calls, control };
}

function createLifecycleHarness() {
  const control = { epoch: 1, scheduleThrows: false };
  const scheduled = new Map();
  const unscheduled = [];
  const events = [];
  const owner = new GameRuntimeLifecycleOwner({
    getEpoch: () => control.epoch,
    scheduleOnce: (callback, delaySeconds) => {
      if (control.scheduleThrows) throw new Error('schedule failed');
      scheduled.set(callback, delaySeconds);
    },
    unschedule: (callback) => {
      unscheduled.push(callback);
      scheduled.delete(callback);
    },
    onEvent: (event) => events.push(event),
  });
  const run = (callback) => {
    assert.ok(scheduled.has(callback), 'callback is not scheduled');
    scheduled.delete(callback);
    callback();
  };
  return { control, events, owner, run, scheduled, unscheduled };
}

testGroup('ui_navigation_delegates_without_state_writer', () => {
  const h = createUiHarness('menu');
  const result = h.adapter.dispatch({ action: 'navigate', next: 'levels', reason: 'ui_levels' });
  assert.deepStrictEqual(h.calls, [{ action: 'navigate', next: 'levels', reason: 'ui_levels' }]);
  assert.deepStrictEqual(result, { accepted: true, action: 'navigate', sourceState: 'menu', reason: 'handled' });
  assert.strictEqual(Object.isFrozen(result), true);
  h.control.navigateAccepted = false;
  const rejected = h.adapter.dispatch({ action: 'navigate', next: 'playing', reason: 'invalid_fixture' });
  assert.deepStrictEqual(rejected, { accepted: false, action: 'navigate', sourceState: 'menu', reason: 'transition_rejected' });
});

testGroup('ui_level_indices_fail_closed', () => {
  const h = createUiHarness('levels');
  assert.strictEqual(h.adapter.dispatch({ action: 'start_level', levelIndex: -1 }).reason, 'invalid_level_index');
  assert.strictEqual(h.adapter.dispatch({ action: 'start_level', levelIndex: 15 }).reason, 'invalid_level_index');
  assert.strictEqual(h.adapter.dispatch({ action: 'start_level', levelIndex: 1.5 }).reason, 'invalid_level_index');
  assert.strictEqual(h.adapter.dispatch({ action: 'start_level', levelIndex: 14 }).accepted, true);
  assert.deepStrictEqual(h.calls, [{ action: 'start_level', levelIndex: 14 }]);
});

testGroup('ui_skin_intents_require_skin_screen_and_valid_index', () => {
  const h = createUiHarness('menu');
  assert.strictEqual(h.adapter.dispatch({ action: 'preview_skin', skinIndex: 0 }).reason, 'invalid_source_state');
  assert.strictEqual(h.adapter.dispatch({ action: 'confirm_skin' }).reason, 'invalid_source_state');
  h.control.state = 'skins';
  assert.strictEqual(h.adapter.dispatch({ action: 'preview_skin', skinIndex: 8 }).reason, 'invalid_skin_index');
  assert.strictEqual(h.adapter.dispatch({ action: 'preview_skin', skinIndex: 7 }).accepted, true);
  assert.strictEqual(h.adapter.dispatch({ action: 'confirm_skin' }).accepted, true);
  assert.deepStrictEqual(h.calls, [{ action: 'preview_skin', skinIndex: 7 }, { action: 'confirm_skin' }]);
});

testGroup('ui_developer_gate_intents_are_state_bounded', () => {
  const h = createUiHarness('menu');
  assert.strictEqual(h.adapter.dispatch({ action: 'open_developer_gate' }).accepted, true);
  assert.strictEqual(h.adapter.dispatch({ action: 'submit_developer_gate' }).reason, 'invalid_source_state');
  h.control.state = 'devgate';
  assert.strictEqual(h.adapter.dispatch({ action: 'submit_developer_gate' }).accepted, true);
  assert.deepStrictEqual(h.calls, [{ action: 'open_developer_gate' }, { action: 'submit_developer_gate' }]);
});

testGroup('component_callback_executes_after_epoch_change', () => {
  const h = createLifecycleHarness();
  let calls = 0;
  h.owner.scheduleOnce('component.preload', 'component', () => { calls += 1; }, 0.5);
  const callback = Array.from(h.scheduled.keys())[0];
  h.control.epoch = 2;
  h.run(callback);
  assert.strictEqual(calls, 1);
  assert.deepStrictEqual(h.owner.snapshot(), { destroyed: false, epoch: 2, componentCallbacks: 0, sessionCallbacks: 0, listeners: 0 });
});

testGroup('session_callback_executes_only_in_same_epoch', () => {
  const h = createLifecycleHarness();
  let calls = 0;
  h.owner.scheduleOnce('session.qa', 'session', () => { calls += 1; }, 0);
  h.run(Array.from(h.scheduled.keys())[0]);
  assert.strictEqual(calls, 1);
  assert.ok(h.events.some((event) => event.code === 'callback.executed'));
});

testGroup('stale_session_callback_is_rejected', () => {
  const h = createLifecycleHarness();
  let calls = 0;
  h.owner.scheduleOnce('session.stale', 'session', () => { calls += 1; }, 0);
  const callback = Array.from(h.scheduled.keys())[0];
  h.control.epoch = 2;
  h.run(callback);
  assert.strictEqual(calls, 0);
  assert.ok(h.events.some((event) => event.code === 'callback.stale' && event.key === 'session.stale'));
});

testGroup('session_cancel_preserves_component_work', () => {
  const h = createLifecycleHarness();
  h.owner.scheduleOnce('component.asset', 'component', () => {}, 1);
  h.owner.scheduleOnce('session.retry', 'session', () => {}, 1);
  assert.strictEqual(h.owner.cancelSession('reset'), 1);
  assert.deepStrictEqual(h.owner.snapshot(), { destroyed: false, epoch: 1, componentCallbacks: 1, sessionCallbacks: 0, listeners: 0 });
  assert.strictEqual(h.unscheduled.length, 1);
});

testGroup('listener_keys_are_unique_and_cleanup_is_reverse_order', () => {
  const h = createLifecycleHarness();
  const calls = [];
  h.owner.registerListener('first', () => calls.push('on:first'), () => calls.push('off:first'));
  h.owner.registerListener('second', () => calls.push('on:second'), () => calls.push('off:second'));
  assert.throws(() => h.owner.registerListener('first', () => calls.push('duplicate'), () => {}), /already registered/);
  h.owner.destroy('component_destroy');
  assert.deepStrictEqual(calls, ['on:first', 'on:second', 'off:second', 'off:first']);
});

testGroup('destroy_cancels_all_callbacks_and_is_idempotent', () => {
  const h = createLifecycleHarness();
  h.owner.scheduleOnce('component.asset', 'component', () => {}, 1);
  h.owner.scheduleOnce('session.qa', 'session', () => {}, 1);
  const first = h.owner.destroy('component_destroy');
  const second = h.owner.destroy('component_destroy_again');
  assert.deepStrictEqual(first, { destroyed: true, epoch: 1, componentCallbacks: 0, sessionCallbacks: 0, listeners: 0 });
  assert.deepStrictEqual(second, first);
  assert.strictEqual(h.unscheduled.length, 2);
});

testGroup('destroyed_owner_rejects_new_work', () => {
  const h = createLifecycleHarness();
  h.owner.destroy('component_destroy');
  assert.throws(() => h.owner.scheduleOnce('late', 'component', () => {}, 0), /destroyed/);
  assert.throws(() => h.owner.registerListener('late', () => {}, () => {}), /destroyed/);
});

testGroup('invalid_schedule_contract_is_rejected', () => {
  const h = createLifecycleHarness();
  assert.throws(() => h.owner.scheduleOnce('', 'component', () => {}, 0), /key cannot be empty/);
  assert.throws(() => h.owner.scheduleOnce('negative', 'component', () => {}, -1), /finite and non-negative/);
  assert.throws(() => h.owner.scheduleOnce('nan', 'session', () => {}, Number.NaN), /finite and non-negative/);
  assert.deepStrictEqual(h.owner.snapshot(), { destroyed: false, epoch: 1, componentCallbacks: 0, sessionCallbacks: 0, listeners: 0 });
});

testGroup('schedule_failure_rolls_back_pending_entry', () => {
  const h = createLifecycleHarness();
  h.control.scheduleThrows = true;
  assert.throws(() => h.owner.scheduleOnce('failure', 'component', () => {}, 0), /schedule failed/);
  assert.deepStrictEqual(h.owner.snapshot(), { destroyed: false, epoch: 1, componentCallbacks: 0, sessionCallbacks: 0, listeners: 0 });
});

testGroup('event_payloads_and_snapshots_are_immutable', () => {
  const h = createLifecycleHarness();
  h.owner.scheduleOnce('immutable', 'component', () => {}, 0);
  assert.strictEqual(Object.isFrozen(h.events[0]), true);
  assert.strictEqual(Object.isFrozen(h.owner.snapshot()), true);
});

console.log(JSON.stringify({
  groups: passedGroups,
  status: 'PASS',
  uiActions: 6,
}));
