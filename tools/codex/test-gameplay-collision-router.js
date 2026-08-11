'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const routerPath = path.join(projectRoot, 'assets', 'scripts', 'gameplay', 'collision', 'GameplayCollisionRouter.ts');
const gameRootPath = path.join(projectRoot, 'assets', 'scripts', 'GameRoot.ts');
const typescriptPath = process.env.COCOS_TYPESCRIPT_JS
  || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js';

for (const requiredPath of [routerPath, gameRootPath, typescriptPath]) {
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
const program = ts.createProgram([routerPath], compilerOptions);
const diagnostics = ts.getPreEmitDiagnostics(program)
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
  .map((diagnostic) => {
    const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
    if (!diagnostic.file || diagnostic.start === undefined) return `${diagnostic.code}: ${message}`;
    const position = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
    return `${diagnostic.file.fileName}:${position.line + 1}:${position.character + 1} ${diagnostic.code}: ${message}`;
  });
assert.deepStrictEqual(diagnostics, [], `Strict TypeScript diagnostics:\n${diagnostics.join('\n')}`);

const transpiled = ts.transpileModule(fs.readFileSync(routerPath, 'utf8'), {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2015,
    strict: true,
  },
  fileName: routerPath,
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
  routerPath,
  path.dirname(routerPath),
);

const {
  GAMEPLAY_COLLISION_KINDS,
  GameplayCollisionRouter,
} = loadedModule.exports;

const orderedIntents = [
  { kind: 'platform_land', entityId: 'platform:0', otherId: 'player', payload: { platformIndex: 0, targetY: 420 } },
  { kind: 'ground_clamp', entityId: 'ground:main', otherId: 'player', payload: { targetY: 560 } },
  { kind: 'collectible_pickup', entityId: 'collectible:0', otherId: 'player', payload: { collectibleIndex: 0, collectibleKind: 'banana', screenX: 250, worldY: 480 } },
  { kind: 'bonus_pickup', entityId: 'bonus:0', otherId: 'player', payload: { bonusIndex: 0, bonusType: 2, screenX: 260, worldY: 470 } },
  { kind: 'obstacle_hit', entityId: 'obstacle:0', otherId: 'player', payload: { obstacleIndex: 0, obstacleType: 3, screenX: 280, worldY: 520 } },
  { kind: 'npc_stomp', entityId: 'npc:0', otherId: 'player', payload: { npcIndex: 0, screenX: 300 } },
  { kind: 'npc_hit', entityId: 'npc:1', otherId: 'player', payload: { npcIndex: 1, screenX: 320, worldY: 514 } },
  { kind: 'level_finish', entityId: 'level:0', otherId: 'player', payload: { levelIndex: 0, nextState: 'clear' } },
];

function createHarness(initialEpoch = 3, initialTick = 42, onEvent) {
  const control = { epoch: initialEpoch, tick: initialTick };
  const events = [];
  const router = new GameplayCollisionRouter({
    getEpoch: () => control.epoch,
    getTick: () => control.tick,
    onEvent: onEvent || ((event) => events.push(event)),
  });
  return { control, events, router };
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

testGroup('canonical_collision_kind_order_is_frozen', () => {
  assert.deepStrictEqual([...GAMEPLAY_COLLISION_KINDS], orderedIntents.map((intent) => intent.kind));
  assert.strictEqual(Object.isFrozen(GAMEPLAY_COLLISION_KINDS), true);
});

testGroup('recorded_order_is_synchronous_and_monotonic', () => {
  const h = createHarness();
  const returned = orderedIntents.map((intent) => h.router.route(intent));
  assert.deepStrictEqual(h.events.map((event) => event.kind), orderedIntents.map((intent) => intent.kind));
  assert.deepStrictEqual(h.events.map((event) => event.sequence), [1, 2, 3, 4, 5, 6, 7, 8]);
  assert.ok(returned.every((event, index) => event === h.events[index]));
  assert.ok(h.events.every((event) => event.epoch === 3 && event.tick === 42));
});

testGroup('event_and_payload_are_immutable_snapshots', () => {
  const h = createHarness();
  const intent = orderedIntents[2];
  const event = h.router.route(intent);
  assert.strictEqual(Object.isFrozen(event), true);
  assert.strictEqual(Object.isFrozen(event.payload), true);
  assert.notStrictEqual(event.payload, intent.payload);
  assert.deepStrictEqual(event.payload, intent.payload);
});

testGroup('epoch_and_tick_are_sampled_per_route', () => {
  const h = createHarness(1, 10);
  h.router.route(orderedIntents[0]);
  h.control.epoch = 2;
  h.control.tick = 11;
  h.router.route(orderedIntents[1]);
  assert.deepStrictEqual(h.events.map((event) => [event.epoch, event.tick]), [[1, 10], [2, 11]]);
});

testGroup('invalid_identity_kind_and_clock_fail_before_callback', () => {
  const h = createHarness();
  assert.throws(() => h.router.route({ ...orderedIntents[0], entityId: '  ' }), /entityId/);
  assert.throws(() => h.router.route({ ...orderedIntents[0], otherId: 'npc' }), /otherId/);
  assert.throws(() => h.router.route({ ...orderedIntents[0], kind: 'unknown' }), /Unknown/);
  h.control.epoch = -1;
  assert.throws(() => h.router.route(orderedIntents[0]), /epoch/);
  h.control.epoch = 1;
  h.control.tick = Number.NaN;
  assert.throws(() => h.router.route(orderedIntents[0]), /tick/);
  assert.deepStrictEqual(h.events, []);
});

testGroup('reentrant_routing_is_rejected_and_guard_recovers', () => {
  let first = true;
  let router;
  const events = [];
  router = new GameplayCollisionRouter({
    getEpoch: () => 1,
    getTick: () => 1,
    onEvent: (event) => {
      events.push(event.kind);
      if (first) {
        first = false;
        router.route(orderedIntents[1]);
      }
    },
  });
  assert.throws(() => router.route(orderedIntents[0]), /reentrant/);
  router.route(orderedIntents[1]);
  assert.deepStrictEqual(events, ['platform_land', 'ground_clamp']);
});

testGroup('callback_failure_propagates_without_poisoning_router', () => {
  let shouldThrow = true;
  const events = [];
  const router = new GameplayCollisionRouter({
    getEpoch: () => 1,
    getTick: () => 1,
    onEvent: (event) => {
      if (shouldThrow) {
        shouldThrow = false;
        throw new Error('fixture failure');
      }
      events.push(event);
    },
  });
  assert.throws(() => router.route(orderedIntents[0]), /fixture failure/);
  const recovered = router.route(orderedIntents[1]);
  assert.strictEqual(recovered.sequence, 2);
  assert.strictEqual(events.length, 1);
});

testGroup('router_has_no_cocos_queue_or_subscriber_ownership', () => {
  const source = fs.readFileSync(routerPath, 'utf8');
  for (const marker of ["from 'cc'", 'console.', 'setTimeout', 'setInterval', 'queue', 'handlers', 'subscribe']) {
    assert.ok(!source.includes(marker), `forbidden router ownership: ${marker}`);
  }
  assert.strictEqual((source.match(/readonly onEvent:/g) || []).length, 1);
});

testGroup('game_root_routes_detection_in_legacy_order', () => {
  const source = fs.readFileSync(gameRootPath, 'utf8');
  assert.strictEqual((source.match(/new\s+GameplayCollisionRouter\s*\(/g) || []).length, 1);
  assert.strictEqual((source.match(/this\.applyCollisionEvent\(event\)/g) || []).length, 1);

  const update = source.slice(source.indexOf('private updateGame'), source.indexOf('private applyCollisionEvent'));
  const qaMatrix = source.slice(
    source.indexOf('private runCollisionRouterMatrixForQa'),
    source.indexOf('private schedulePowerUpLifecycleMatrixForQa'),
  );
  const powerUpQaMatrix = source.slice(
    source.indexOf('private runPowerUpLifecycleMatrixForQa'),
    source.indexOf('private enableDeveloperMode'),
  );
  assert.strictEqual((update.match(/this\.gameplayCollisions\.route\s*\(/g) || []).length, 8);
  assert.strictEqual((qaMatrix.match(/this\.gameplayCollisions\.route\s*\(/g) || []).length, 8);
  assert.strictEqual((powerUpQaMatrix.match(/this\.gameplayCollisions\.route\s*\(/g) || []).length, 2);
  assert.strictEqual((source.match(/this\.gameplayCollisions\.route\s*\(/g) || []).length, 18);
  assert.ok(qaMatrix.includes("if (!DEBUG || !this.developerMode || this.state !== 'playing')"));
  assert.ok(qaMatrix.includes('MTR_COLLISION_QA_'));
  const markers = [
    "kind: 'platform_land'",
    "kind: 'ground_clamp'",
    "kind: 'collectible_pickup'",
    "kind: 'bonus_pickup'",
    "kind: 'obstacle_hit'",
    "kind: 'npc_stomp'",
    "kind: 'npc_hit'",
    "kind: 'level_finish'",
    'this.updateParticles(dt)',
  ];
  let previous = -1;
  for (const marker of markers) {
    const current = update.indexOf(marker);
    assert.ok(current > previous, `legacy order drift at ${marker}`);
    previous = current;
  }
});

testGroup('side_effects_live_only_in_exhaustive_game_root_callback', () => {
  const source = fs.readFileSync(gameRootPath, 'utf8');
  const update = source.slice(source.indexOf('private updateGame'), source.indexOf('private applyCollisionEvent'));
  const apply = source.slice(source.indexOf('private applyCollisionEvent'), source.indexOf('private applyJumpInput'));
  for (const marker of [
    'collectible.taken = true',
    'bonus.taken = true',
    'obstacle.dead = true',
    'npc.dead = true',
    "this.transitionTo(event.payload.nextState, 'level_end')",
  ]) assert.ok(apply.includes(marker), `missing callback side effect: ${marker}`);
  for (const marker of ['b.taken = true', 'bonus.taken = true', 'o.dead = true', 'npc.dead = true']) {
    assert.ok(!update.includes(marker), `legacy direct side effect remains: ${marker}`);
  }
  for (const kind of GAMEPLAY_COLLISION_KINDS) {
    assert.strictEqual((apply.match(new RegExp(`case '${kind}'`, 'g')) || []).length, 1);
  }
  assert.ok(!apply.includes('this.gameplayCollisions.route('));
  assert.ok(apply.includes('const unhandledEvent: never = event'));
});

console.log(JSON.stringify({
  collision_kinds: GAMEPLAY_COLLISION_KINDS.length,
  passed_groups: passedGroups,
  status: 'PASS',
}));
