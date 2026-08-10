'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const adapterPath = path.join(projectRoot, 'assets', 'scripts', 'gameplay', 'input', 'GameplayInputAdapter.ts');
const statePath = path.join(projectRoot, 'assets', 'scripts', 'gameplay', 'state', 'GameSessionState.ts');
const gameRootPath = path.join(projectRoot, 'assets', 'scripts', 'GameRoot.ts');
const typescriptPath = process.env.COCOS_TYPESCRIPT_JS
  || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js';

for (const requiredPath of [adapterPath, statePath, gameRootPath, typescriptPath]) {
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
const program = ts.createProgram([adapterPath, statePath], compilerOptions);
const diagnostics = ts.getPreEmitDiagnostics(program)
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
  .map((diagnostic) => {
    const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
    if (!diagnostic.file || diagnostic.start === undefined) return `${diagnostic.code}: ${message}`;
    const position = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
    return `${diagnostic.file.fileName}:${position.line + 1}:${position.character + 1} ${diagnostic.code}: ${message}`;
  });
assert.deepStrictEqual(diagnostics, [], `Strict TypeScript diagnostics:\n${diagnostics.join('\n')}`);

const transpiled = ts.transpileModule(fs.readFileSync(adapterPath, 'utf8'), {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2015,
    strict: true,
  },
  fileName: adapterPath,
  reportDiagnostics: true,
});
const transpileErrors = (transpiled.diagnostics || [])
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
  .map((diagnostic) => `${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')}`);
assert.deepStrictEqual(transpileErrors, [], `Transpile diagnostics:\n${transpileErrors.join('\n')}`);

const loadedModule = { exports: {} };
const load = new Function('exports', 'require', 'module', '__filename', '__dirname', transpiled.outputText);
load(
  loadedModule.exports,
  (request) => { throw new Error(`Unexpected runtime dependency: ${request}`); },
  loadedModule,
  adapterPath,
  path.dirname(adapterPath),
);

const {
  GAMEPLAY_INPUT_PAUSE_DEBOUNCE_MS,
  GameplayInputAdapter,
} = loadedModule.exports;
assert.strictEqual(GAMEPLAY_INPUT_PAUSE_DEBOUNCE_MS, 220);

function createHarness(initialState = 'menu', initialNowMs = 1000) {
  const control = { state: initialState, nowMs: initialNowMs };
  const calls = [];
  const adapter = new GameplayInputAdapter({
    getSessionState: () => control.state,
    nowMs: () => control.nowMs,
    onJump: (context) => calls.push({ kind: 'jump', context }),
    onGlideChanged: (active, context) => calls.push({ kind: 'glide', active, context }),
    onDash: (context) => calls.push({ kind: 'dash', context }),
    onPause: (context) => calls.push({ kind: 'pause', context }),
  });
  return { adapter, calls, control };
}

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

testGroup('jump_and_dash_require_playing_session', () => {
  const h = createHarness('menu');
  const jump = { action: 'jump', phase: 'trigger', source: 'keyboard' };
  const dash = { action: 'dash', phase: 'trigger', source: 'hud_button' };
  assert.strictEqual(h.adapter.dispatch(jump).reason, 'session_not_playing');
  assert.strictEqual(h.adapter.dispatch(dash).reason, 'session_not_playing');
  assert.deepStrictEqual(h.calls, []);
  h.control.state = 'playing';
  assert.strictEqual(h.adapter.dispatch(jump).accepted, true);
  assert.strictEqual(h.adapter.dispatch(dash).accepted, true);
  assert.deepStrictEqual(h.calls.map((call) => call.kind), ['jump', 'dash']);
});

testGroup('glide_start_is_gated_but_stop_always_releases', () => {
  const h = createHarness('paused');
  const blocked = h.adapter.dispatch({ action: 'glide', phase: 'start', source: 'global_touch' });
  assert.strictEqual(blocked.reason, 'session_not_playing');
  assert.deepStrictEqual(h.calls, []);
  const release = h.adapter.releaseGlide('global_touch');
  assert.strictEqual(release.accepted, true);
  assert.deepStrictEqual(h.calls.map((call) => [call.kind, call.active]), [['glide', false]]);
  h.control.state = 'playing';
  h.adapter.dispatch({ action: 'glide', phase: 'start', source: 'keyboard' });
  assert.deepStrictEqual(h.calls.map((call) => [call.kind, call.active]), [['glide', false], ['glide', true]]);
});

testGroup('pause_debounce_accepts_first_and_exact_boundary', () => {
  const h = createHarness('menu', 5000);
  const intent = { action: 'pause', phase: 'trigger', source: 'keyboard' };
  const first = h.adapter.dispatch(intent);
  assert.strictEqual(first.accepted, true);
  assert.strictEqual(first.pauseAcceptedCount, 1);
  assert.strictEqual(h.calls[0].context.acceptedCount, 1);
  h.control.nowMs = 5219;
  assert.strictEqual(h.adapter.dispatch(intent).reason, 'pause_debounced');
  assert.strictEqual(h.adapter.pauseAcceptedCount, 1);
  h.control.nowMs = 5220;
  const boundary = h.adapter.dispatch(intent);
  assert.strictEqual(boundary.accepted, true);
  assert.strictEqual(boundary.pauseAcceptedCount, 2);
  assert.deepStrictEqual(h.calls.map((call) => call.kind), ['pause', 'pause']);
});

testGroup('overlapping_pause_routes_share_one_debounce_owner', () => {
  const h = createHarness('playing', 8000);
  const nodeRoute = h.adapter.dispatch({ action: 'pause', phase: 'trigger', source: 'pause_zone' });
  const globalRoute = h.adapter.dispatch({ action: 'pause', phase: 'trigger', source: 'global_touch' });
  assert.strictEqual(nodeRoute.accepted, true);
  assert.strictEqual(globalRoute.reason, 'pause_debounced');
  assert.strictEqual(h.calls.length, 1);
  assert.strictEqual(h.calls[0].context.source, 'pause_zone');
});

testGroup('clock_rollback_fails_closed_until_boundary_recovers', () => {
  const h = createHarness('playing', 1000);
  const pause = { action: 'pause', phase: 'trigger', source: 'qa' };
  assert.strictEqual(h.adapter.dispatch(pause).accepted, true);
  h.control.nowMs = 900;
  assert.strictEqual(h.adapter.dispatch(pause).reason, 'pause_debounced');
  h.control.nowMs = 1220;
  assert.strictEqual(h.adapter.dispatch(pause).accepted, true);
  assert.strictEqual(h.adapter.pauseAcceptedCount, 2);
});

testGroup('invalid_clock_does_not_poison_pause_state', () => {
  const h = createHarness('playing', Number.NaN);
  const pause = { action: 'pause', phase: 'trigger', source: 'qa' };
  assert.strictEqual(h.adapter.dispatch(pause).reason, 'invalid_clock');
  assert.strictEqual(h.adapter.pauseAcceptedCount, 0);
  assert.deepStrictEqual(h.calls, []);
  h.control.nowMs = 3000;
  assert.strictEqual(h.adapter.dispatch(pause).accepted, true);
  assert.strictEqual(h.adapter.pauseAcceptedCount, 1);
});

testGroup('invalid_action_phases_have_no_side_effects', () => {
  const h = createHarness('playing');
  const invalid = [
    { action: 'jump', phase: 'start', source: 'keyboard' },
    { action: 'dash', phase: 'stop', source: 'global_touch' },
    { action: 'pause', phase: 'start', source: 'hud_button' },
    { action: 'glide', phase: 'trigger', source: 'keyboard' },
  ];
  for (const intent of invalid) assert.strictEqual(h.adapter.dispatch(intent).reason, 'invalid_phase');
  assert.deepStrictEqual(h.calls, []);
});

testGroup('callback_context_is_deterministic_and_source_complete', () => {
  const h = createHarness('playing', 4242);
  h.adapter.dispatch({ action: 'jump', phase: 'trigger', source: 'global_touch' });
  assert.deepStrictEqual(h.calls[0], {
    kind: 'jump',
    context: {
      action: 'jump',
      phase: 'trigger',
      source: 'global_touch',
      sessionState: 'playing',
      nowMs: 4242,
    },
  });
});

testGroup('session_reset_uses_the_same_glide_adapter', () => {
  const h = createHarness('over', 6000);
  const result = h.adapter.releaseGlide('session_reset');
  assert.strictEqual(result.accepted, true);
  assert.strictEqual(h.calls.length, 1);
  assert.strictEqual(h.calls[0].kind, 'glide');
  assert.strictEqual(h.calls[0].active, false);
  assert.strictEqual(h.calls[0].context.source, 'session_reset');
});

testGroup('game_root_listener_and_routing_parity', () => {
  const source = fs.readFileSync(gameRootPath, 'utf8');
  const adapterSource = fs.readFileSync(adapterPath, 'utf8');
  const count = (text, pattern) => (text.match(pattern) || []).length;
  assert.strictEqual(count(source, /new\s+GameplayInputAdapter\s*\(/g), 1);
  assert.strictEqual(count(source, /this\.gliding\s*=/g), 1);
  assert.strictEqual(count(source, /this\.applyJumpInput\(\)/g), 1);
  assert.strictEqual(count(source, /this\.applyDashInput\(\)/g), 1);
  assert.strictEqual(count(source, /this\.applyPauseInput\(context\)/g), 1);
  assert.ok(!source.includes('togglePauseFromInput'));
  assert.ok(!source.includes('lastPauseToggleMs'));
  assert.ok(!source.includes('pauseTapAccepted'));
  assert.ok(!/private\s+(?:jump|dash)\s*\(/.test(source));

  const listeners = [
    ['TOUCH_START', 'onTouchStart'],
    ['TOUCH_MOVE', 'onTouchMove'],
    ['TOUCH_END', 'onTouchEnd'],
    ['TOUCH_CANCEL', 'onTouchEnd'],
    ['KEY_DOWN', 'onKeyDown'],
    ['KEY_UP', 'onKeyUp'],
  ];
  for (const [event, handler] of listeners) {
    const on = new RegExp(`input\\.on\\(Input\\.EventType\\.${event}, this\\.${handler}, this\\);`, 'g');
    const off = new RegExp(`input\\.off\\(Input\\.EventType\\.${event}, this\\.${handler}, this\\);`, 'g');
    assert.strictEqual(count(source, on), 1, `listener registration drift: ${event}/${handler}`);
    assert.strictEqual(count(source, off), 1, `listener cleanup drift: ${event}/${handler}`);
  }
  assert.strictEqual(count(source, /this\.pauseTouchZone\.on\(Input\.EventType\.TOUCH_END, this\.onPauseTouchZoneTap, this\);/g), 1);
  assert.strictEqual(count(source, /this\.pauseTouchZone\.off\(Input\.EventType\.TOUCH_END, this\.onPauseTouchZoneTap, this\);/g), 1);
  assert.ok(!adapterSource.includes("from 'cc'"));
  assert.ok(!adapterSource.includes('input.on('));

  for (const sourceName of ['keyboard', 'global_touch', 'hud_button', 'pause_zone', 'qa', 'session_reset']) {
    assert.ok(source.includes(`'${sourceName}'`), `missing GameRoot route: ${sourceName}`);
  }
  const touchStart = source.slice(source.indexOf('private onTouchStart'), source.indexOf('private onTouchMove'));
  assert.ok(touchStart.indexOf('this.handleTouch') < touchStart.indexOf("action: 'glide'"));
  const keyDown = source.slice(source.indexOf('private onKeyDown'), source.indexOf('private onKeyUp'));
  assert.ok(keyDown.indexOf("action: 'glide'") < keyDown.indexOf("action: 'jump'"));
});

console.log(JSON.stringify({
  debounce_ms: GAMEPLAY_INPUT_PAUSE_DEBOUNCE_MS,
  passed_groups: passedGroups,
  status: 'PASS',
}));
