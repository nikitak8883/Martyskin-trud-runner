'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const sourcePath = path.join(projectRoot, 'assets', 'scripts', 'gameplay', 'powerups', 'PowerUpLifecycle.ts');
const typescriptPath = process.env.COCOS_TYPESCRIPT_JS
  || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js';

for (const requiredPath of [sourcePath, typescriptPath]) {
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
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
  .map((diagnostic) => {
    const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
    if (!diagnostic.file || diagnostic.start === undefined) return `${diagnostic.code}: ${message}`;
    const position = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
    return `${diagnostic.file.fileName}:${position.line + 1}:${position.character + 1} ${diagnostic.code}: ${message}`;
  });
assert.deepStrictEqual(diagnostics, [], `Strict TypeScript diagnostics:\n${diagnostics.join('\n')}`);

const transpiled = ts.transpileModule(fs.readFileSync(sourcePath, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2015, strict: true },
  fileName: sourcePath,
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
  sourcePath,
  path.dirname(sourcePath),
);

const { POWER_UP_EFFECT_KEYS, POWER_UP_KIND_COUNT, PowerUpLifecycle } = loadedModule.exports;
assert.strictEqual(POWER_UP_KIND_COUNT, 9);
assert.deepStrictEqual([...POWER_UP_EFFECT_KEYS], [
  'jumpBoost', 'dashBoost', 'armor', 'magnet', 'vestBonus',
  'shieldBonus', 'coffeeBoost', 'blueprintBonus', 'passBonus', 'extraLifeAura',
]);

let epoch = 1;
let tick = 10;
const events = [];
const lifecycle = new PowerUpLifecycle({
  getEpoch: () => epoch,
  getTick: () => tick,
  allowQaMutation: true,
  onEvent: (event) => events.push(event),
});

let snapshot = lifecycle.beginEpoch(epoch, 'unit');
assert.strictEqual(snapshot.sessionOpen, true);
assert.strictEqual(snapshot.runBonusCount, 0);
assert.strictEqual(snapshot.instanceCount, 0);
assert.ok(POWER_UP_EFFECT_KEYS.every((key) => snapshot.effects[key] === 0));

const spawned = lifecycle.spawn('unit:coffee', 5);
assert.strictEqual(spawned.accepted, true);
assert.strictEqual(lifecycle.spawn('unit:coffee', 5).reason, 'duplicate_instance');
assert.strictEqual(lifecycle.collect('unit:coffee', epoch - 1).reason, 'stale_epoch');
assert.strictEqual(lifecycle.instance('unit:coffee').phase, 'spawned');

tick += 1;
assert.strictEqual(lifecycle.collect('unit:coffee', epoch).accepted, true);
const activated = lifecycle.activate('unit:coffee', 5, epoch);
assert.strictEqual(activated.accepted, true);
assert.deepStrictEqual(activated.oneShot, {
  resetDashCooldown: true,
  scoreDelta: 0,
  healAmount: 0,
  invincibilityFloor: 0,
});
snapshot = lifecycle.snapshot();
assert.strictEqual(snapshot.effects.coffeeBoost, 10);
assert.strictEqual(snapshot.effects.jumpBoost, 8);
assert.strictEqual(snapshot.effects.dashBoost, 6);
assert.strictEqual(snapshot.runBonusCount, 1);
assert.strictEqual(snapshot.runBonusSeen[5], true);
assert.strictEqual(snapshot.activeInstanceCount, 1);
assert.throws(() => { snapshot.effects.coffeeBoost = 999; }, TypeError);
assert.throws(() => { snapshot.runBonusSeen[5] = false; }, TypeError);

tick += 1;
snapshot = lifecycle.tick(0.5);
assert.strictEqual(snapshot.effects.coffeeBoost, 9.5);
assert.strictEqual(snapshot.effects.jumpBoost, 7.5);
assert.strictEqual(snapshot.effects.dashBoost, 5.5);
assert.strictEqual(snapshot.effects.armor, -0.5);
snapshot = lifecycle.tick(9.5);
assert.strictEqual(snapshot.effects.coffeeBoost, 0);
assert.strictEqual(snapshot.effects.jumpBoost, -2);
assert.strictEqual(snapshot.effects.dashBoost, -4);
assert.strictEqual(lifecycle.instance('unit:coffee'), null);
assert.ok(events.some((event) => event.action === 'expired' && event.instance.id === 'unit:coffee'));
assert.ok(events.some((event) => event.action === 'cleaned' && event.instance.id === 'unit:coffee'));

const expectedPolicies = [
  { key: 'jumpBoost', seconds: 14, score: 0, heal: 0, invincible: 0, dashReset: false },
  { key: 'dashBoost', seconds: 12, score: 0, heal: 0, invincible: 0, dashReset: true },
  { key: 'shieldBonus', seconds: 18, score: 0, heal: 0, invincible: 0, dashReset: false },
  { key: 'magnet', seconds: 14, score: 0, heal: 0, invincible: 0, dashReset: false },
  { key: 'vestBonus', seconds: 16, score: 0, heal: 0, invincible: 0, dashReset: false },
  { key: 'coffeeBoost', seconds: 10, score: 0, heal: 0, invincible: 0, dashReset: true },
  { key: 'blueprintBonus', seconds: 16, score: 50, heal: 0, invincible: 0, dashReset: false },
  { key: 'passBonus', seconds: 16, score: 0, heal: 0, invincible: 0.75, dashReset: false },
  { key: 'extraLifeAura', seconds: 10, score: 100, heal: 1, invincible: 0, dashReset: false },
];

for (let kind = 0; kind < POWER_UP_KIND_COUNT; kind += 1) {
  epoch += 1;
  tick += 1;
  lifecycle.beginEpoch(epoch, `policy-${kind}`);
  const id = `policy:${kind}`;
  assert.strictEqual(lifecycle.spawn(id, kind).accepted, true);
  assert.strictEqual(lifecycle.collect(id, epoch).accepted, true);
  const result = lifecycle.activate(id, kind, epoch);
  assert.strictEqual(result.accepted, true);
  const expected = expectedPolicies[kind];
  assert.strictEqual(lifecycle.effectSeconds(expected.key), expected.seconds);
  assert.strictEqual(result.oneShot.scoreDelta, expected.score);
  assert.strictEqual(result.oneShot.healAmount, expected.heal);
  assert.strictEqual(result.oneShot.invincibilityFloor, expected.invincible);
  assert.strictEqual(result.oneShot.resetDashCooldown, expected.dashReset);
}

snapshot = lifecycle.cleanupSession('terminal');
assert.strictEqual(snapshot.sessionOpen, false);
assert.strictEqual(snapshot.instanceCount, 0);
assert.ok(POWER_UP_EFFECT_KEYS.every((key) => snapshot.effects[key] === 0));
assert.strictEqual(snapshot.runBonusCount, 1);
assert.strictEqual(snapshot.runBonusSeen[8], true);
assert.strictEqual(lifecycle.collect('policy:8', epoch).reason, 'session_closed');
assert.throws(() => lifecycle.tick(0.1), /session is closed/);

epoch += 1;
snapshot = lifecycle.beginEpoch(epoch, 'retry');
assert.strictEqual(snapshot.runBonusCount, 0);
assert.ok(snapshot.runBonusSeen.every((seen) => seen === false));
assert.strictEqual(lifecycle.collect('policy:8', epoch - 1).reason, 'stale_epoch');

snapshot = lifecycle.seedAllEffectsForQa(24, epoch);
assert.ok(POWER_UP_EFFECT_KEYS.every((key) => snapshot.effects[key] === 24));
assert.strictEqual(lifecycle.consumeArmor(epoch), true);
assert.strictEqual(lifecycle.effectSeconds('armor'), 0);
assert.strictEqual(lifecycle.consumeArmor(epoch), false);

const closedQa = new PowerUpLifecycle({ getEpoch: () => 0, getTick: () => 0 });
closedQa.beginEpoch(0, 'qa-gate');
assert.throws(() => closedQa.seedAllEffectsForQa(24, 0), /disabled/);
assert.throws(() => closedQa.spawn('invalid id', 0), /Invalid power-up instance id/);
assert.throws(() => closedQa.spawn('invalid:type', 9), /integer in 0\.\.8/);
assert.throws(() => closedQa.tick(-0.1), /finite non-negative/);

let atomicTick = 40;
const atomicActivation = new PowerUpLifecycle({
  getEpoch: () => 4,
  getTick: () => atomicTick,
});
atomicActivation.beginEpoch(4, 'atomic-activation');
assert.strictEqual(atomicActivation.spawn('atomic:coffee', 5).accepted, true);
assert.strictEqual(atomicActivation.collect('atomic:coffee', 4).accepted, true);
atomicTick = -1;
assert.throws(() => atomicActivation.activate('atomic:coffee', 5, 4), /non-negative safe integer/);
snapshot = atomicActivation.snapshot();
assert.strictEqual(snapshot.runBonusCount, 0);
assert.ok(POWER_UP_EFFECT_KEYS.every((key) => snapshot.effects[key] === 0));
assert.strictEqual(atomicActivation.instance('atomic:coffee').phase, 'collected');
atomicTick = 41;
assert.strictEqual(atomicActivation.activate('atomic:coffee', 5, 4).accepted, true);

let atomicQaTick = 50;
const atomicQaSeed = new PowerUpLifecycle({
  getEpoch: () => 5,
  getTick: () => atomicQaTick,
  allowQaMutation: true,
});
atomicQaSeed.beginEpoch(5, 'atomic-qa-seed');
atomicQaTick = -1;
assert.throws(() => atomicQaSeed.seedAllEffectsForQa(24, 5), /non-negative safe integer/);
snapshot = atomicQaSeed.snapshot();
assert.ok(POWER_UP_EFFECT_KEYS.every((key) => snapshot.effects[key] === 0));

epoch += 1;
snapshot = lifecycle.invalidate(epoch, 'destroy');
assert.strictEqual(snapshot.sessionOpen, false);
assert.strictEqual(snapshot.instanceCount, 0);
assert.ok(POWER_UP_EFFECT_KEYS.every((key) => snapshot.effects[key] === 0));

const phases = events
  .filter((event) => event.instance && event.instance.id === 'unit:coffee')
  .map((event) => event.action);
assert.deepStrictEqual(phases, ['spawned', 'collected', 'activated', 'expired', 'cleaned']);
for (let index = 1; index < events.length; index += 1) {
  assert.strictEqual(events[index].sequence, events[index - 1].sequence + 1);
}

process.stdout.write(`${JSON.stringify({
  status: 'PASS',
  groups: 14,
  kinds: POWER_UP_KIND_COUNT,
  effects: POWER_UP_EFFECT_KEYS.length,
  phaseOrder: phases,
  events: events.length,
})}\n`);
