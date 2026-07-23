'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const sourcePath = path.join(projectRoot, 'assets', 'scripts', 'gameplay', 'state', 'GameSessionState.ts');
const gameRootPath = path.join(projectRoot, 'assets', 'scripts', 'GameRoot.ts');
const typescriptPath = process.env.COCOS_TYPESCRIPT_JS
  || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js';

for (const requiredPath of [sourcePath, gameRootPath, typescriptPath]) {
  if (!fs.existsSync(requiredPath)) throw new Error(`Required file not found: ${requiredPath}`);
}

const ts = require(typescriptPath);
const sourceText = fs.readFileSync(sourcePath, 'utf8');
const transpiled = ts.transpileModule(sourceText, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2019,
    strict: true,
  },
  fileName: sourcePath,
  reportDiagnostics: true,
});

const errors = (transpiled.diagnostics || [])
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
  .map((diagnostic) => `${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')}`);
assert.deepStrictEqual(errors, [], `TypeScript transpile diagnostics:\n${errors.join('\n')}`);

const loadedModule = { exports: {} };
const load = new Function('exports', 'require', 'module', '__filename', '__dirname', transpiled.outputText);
load(loadedModule.exports, require, loadedModule, sourcePath, path.dirname(sourcePath));
const contract = loadedModule.exports;

const expectedStates = [
  'menu',
  'playing',
  'paused',
  'clear',
  'over',
  'finished',
  'skins',
  'levels',
  'sound',
  'records',
  'achievements',
  'name',
  'devgate',
  'devpanel',
];

const expectedTargets = {
  menu: ['playing', 'clear', 'over', 'finished', 'skins', 'levels', 'sound', 'records', 'achievements', 'name', 'devgate', 'devpanel'],
  playing: ['paused', 'clear', 'over', 'finished'],
  paused: ['playing', 'sound', 'menu'],
  clear: ['playing', 'menu'],
  over: ['playing', 'menu'],
  finished: ['playing', 'records'],
  skins: ['playing', 'menu'],
  levels: ['playing', 'menu'],
  sound: ['playing', 'menu'],
  records: ['playing', 'achievements', 'menu'],
  achievements: ['playing', 'records', 'menu'],
  name: ['playing', 'menu'],
  devgate: ['playing', 'devpanel', 'menu'],
  devpanel: ['playing', 'menu'],
};

const expectedModes = {
  menu: 'MENU',
  playing: 'RUNNING',
  paused: 'PAUSED',
  clear: 'RUNNING',
  over: 'GAME_OVER',
  finished: 'RUNNING',
  skins: 'CHARACTER_SELECT',
  levels: 'LEVEL_SELECT',
  sound: 'PAUSED',
  records: 'ACHIEVEMENTS',
  achievements: 'ACHIEVEMENTS',
  name: 'CHARACTER_SELECT',
  devgate: 'DEV_MODE',
  devpanel: 'DEV_MODE',
};

assert.deepStrictEqual([...contract.GAME_SESSION_STATES], expectedStates);
assert.strictEqual(Object.isFrozen(contract.GAME_SESSION_STATES), true);
assert.strictEqual(Object.isFrozen(contract.GAME_SESSION_TRANSITION_TARGETS), true);

let acceptedTransitions = 0;
let rejectedTransitions = 0;
for (const from of expectedStates) {
  assert.deepStrictEqual([...contract.GAME_SESSION_TRANSITION_TARGETS[from]], expectedTargets[from], `targets:${from}`);
  assert.strictEqual(Object.isFrozen(contract.GAME_SESSION_TRANSITION_TARGETS[from]), true, `frozen:${from}`);
  assert.strictEqual(contract.gameSessionModeForState(from), expectedModes[from], `mode:${from}`);

  for (const to of expectedStates) {
    const expectedAllowed = from === to || expectedTargets[from].includes(to);
    assert.strictEqual(contract.isGameSessionTransitionAllowed(from, to), expectedAllowed, `allowed:${from}->${to}`);
    const reason = `test_${from}_${to}`;
    const result = contract.evaluateGameSessionTransition(from, to, reason);
    assert.strictEqual(result.from, from);
    assert.strictEqual(result.to, to);
    assert.strictEqual(result.reason, reason);
    assert.strictEqual(result.accepted, expectedAllowed, `accepted:${from}->${to}`);
    assert.strictEqual(result.changed, expectedAllowed && from !== to, `changed:${from}->${to}`);
    if (expectedAllowed) {
      acceptedTransitions += 1;
      assert.strictEqual(result.code, undefined, `accepted_code:${from}->${to}`);
    } else {
      rejectedTransitions += 1;
      assert.strictEqual(result.code, 'invalid_transition', `rejected_code:${from}->${to}`);
    }
  }
}

const gameRootSource = fs.readFileSync(gameRootPath, 'utf8');
assert.match(gameRootSource, /type State = GameSessionState;/);
assert.match(gameRootSource, /evaluateGameSessionTransition\(prev, next, reason\)/);
assert.match(gameRootSource, /private transitionTo\(next: State, reason = 'runtime'\): GameSessionTransitionResult/);
const stateWriterCount = (gameRootSource.match(/this\.state\s*=(?!=)/g) || []).length;
assert.strictEqual(stateWriterCount, 1, 'GameRoot must keep transitionTo as the sole this.state writer');

console.log(JSON.stringify({
  status: 'PASS',
  stateCount: expectedStates.length,
  acceptedTransitions,
  rejectedTransitions,
  idempotentTransitions: expectedStates.length,
  stateWriterCount,
}));
