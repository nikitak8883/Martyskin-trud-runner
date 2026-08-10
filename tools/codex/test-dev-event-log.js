'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const typesPath = path.join(projectRoot, 'assets', 'scripts', 'qa', 'DevEventTypes.ts');
const logPath = path.join(projectRoot, 'assets', 'scripts', 'qa', 'DevEventLog.ts');
const gameRootPath = path.join(projectRoot, 'assets', 'scripts', 'GameRoot.ts');
const typescriptPath = process.env.COCOS_TYPESCRIPT_JS
  || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js';

for (const requiredPath of [typesPath, logPath, gameRootPath, typescriptPath]) {
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
const program = ts.createProgram([typesPath, logPath], compilerOptions);
const diagnostics = ts.getPreEmitDiagnostics(program)
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error);
const diagnosticText = diagnostics.map((diagnostic) => {
  const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
  if (!diagnostic.file || diagnostic.start === undefined) return `${diagnostic.code}: ${message}`;
  const position = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
  return `${diagnostic.file.fileName}:${position.line + 1}:${position.character + 1} ${diagnostic.code}: ${message}`;
});
assert.deepStrictEqual(diagnosticText, [], `Strict TypeScript diagnostics:\n${diagnosticText.join('\n')}`);

function transpile(sourcePath) {
  const result = ts.transpileModule(fs.readFileSync(sourcePath, 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2015,
      strict: true,
    },
    fileName: sourcePath,
    reportDiagnostics: true,
  });
  const errors = (result.diagnostics || [])
    .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
    .map((diagnostic) => `${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')}`);
  assert.deepStrictEqual(errors, [], `TypeScript transpile diagnostics:\n${errors.join('\n')}`);
  return result.outputText;
}

function executeCommonJs(outputText, sourcePath, dependencies = {}) {
  const loadedModule = { exports: {} };
  const localRequire = (request) => {
    if (Object.prototype.hasOwnProperty.call(dependencies, request)) return dependencies[request];
    throw new Error(`Unexpected test-module dependency: ${request}`);
  };
  const load = new Function('exports', 'require', 'module', '__filename', '__dirname', outputText);
  load(loadedModule.exports, localRequire, loadedModule, sourcePath, path.dirname(sourcePath));
  return loadedModule.exports;
}

const types = executeCommonJs(transpile(typesPath), typesPath);
const logModule = executeCommonJs(transpile(logPath), logPath, {
  './DevEventTypes': types,
});
const { DevEventLog } = logModule;

const expectedCodes = [
  'session.transition.accepted',
  'session.transition.rejected',
  'session.reset.begin',
  'session.reset.end',
  'session.epoch.changed',
  'input.action',
  'collision.event',
  'powerup.event',
  'asset.load.start',
  'asset.load.complete',
  'asset.load.error',
  'qa.marker',
];

function input(tick, payload, overrides = {}) {
  return {
    epoch: 0,
    tick,
    code: 'qa.marker',
    ...(payload === undefined ? {} : { payload }),
    ...overrides,
  };
}

function enabledLog(config = {}) {
  return new DevEventLog({ enabled: true, ...config });
}

function byteLength(value) {
  return Buffer.byteLength(value, 'utf8');
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

testGroup('registry_and_defaults', () => {
  assert.deepStrictEqual([...types.DEV_EVENT_CODES], expectedCodes);
  assert.strictEqual(Object.isFrozen(types.DEV_EVENT_CODES), true);
  assert.strictEqual(Object.isFrozen(types.DEFAULT_DEV_EVENT_LOG_CONFIG), true);
  assert.strictEqual(types.DEFAULT_DEV_EVENT_LOG_CONFIG.enabled, false);
  for (const code of expectedCodes) assert.strictEqual(types.isDevEventCode(code), true);
  for (const value of ['', 'unknown', null, 1, {}]) assert.strictEqual(types.isDevEventCode(value), false);
});

testGroup('disabled_and_zero_capacity', () => {
  const disabled = new DevEventLog();
  let inspected = false;
  const hostileInput = new Proxy({}, {
    get() {
      inspected = true;
      throw new Error('disabled append inspected input');
    },
  });
  assert.strictEqual(disabled.enabled, false);
  assert.strictEqual(disabled.capacity, 256);
  assert.strictEqual(disabled.append(hostileInput), undefined);
  assert.strictEqual(inspected, false);
  assert.strictEqual(disabled.size, 0);
  assert.deepStrictEqual(disabled.snapshot(), []);
  assert.strictEqual(Object.isFrozen(disabled.snapshot()), true);
  assert.strictEqual(disabled.exportJson(), '[]');

  const zero = enabledLog({ capacity: 0 });
  assert.strictEqual(zero.enabled, true);
  assert.strictEqual(zero.append(hostileInput), undefined);
  assert.strictEqual(inspected, false);
  assert.strictEqual(zero.size, 0);
  assert.strictEqual(zero.exportJson(), '[]');
});

testGroup('config_boundaries', () => {
  const bounds = {
    capacity: [0, 4096],
    maxStateLength: [0, 256],
    maxReasonLength: [0, 512],
    maxStringLength: [0, 4096],
    maxArrayLength: [0, 256],
    maxObjectKeys: [0, 256],
    maxDepth: [0, 16],
    maxPayloadNodes: [1, 4096],
    maxPayloadBytes: [2, 262144],
    maxExportBytes: [2, 1048576],
  };
  for (const [key, [minimum, maximum]] of Object.entries(bounds)) {
    assert.doesNotThrow(() => new DevEventLog({ [key]: minimum }), `minimum:${key}`);
    assert.doesNotThrow(() => new DevEventLog({ [key]: maximum }), `maximum:${key}`);
    for (const invalid of [minimum - 1, maximum + 1, 1.5, Number.NaN, Number.POSITIVE_INFINITY]) {
      assert.throws(() => new DevEventLog({ [key]: invalid }), /must be an integer/, `${key}:${invalid}`);
    }
  }
  assert.throws(() => new DevEventLog({ enabled: 'true' }), /enabled must be boolean/);
  assert.throws(() => new DevEventLog({ unknown: 1 }), /Unknown DevEventLog config key/);
  assert.throws(() => new DevEventLog(null), /plain object/);
  assert.throws(() => new DevEventLog([]), /plain object/);
  assert.throws(() => new DevEventLog(new Date(0)), /plain object/);
  assert.doesNotThrow(() => new DevEventLog(Object.create(null)));

  let getterCalls = 0;
  const accessorConfig = {};
  Object.defineProperty(accessorConfig, 'capacity', {
    enumerable: true,
    get() {
      getterCalls += 1;
      return 1;
    },
  });
  assert.throws(() => new DevEventLog(accessorConfig), /must be a data property/);
  assert.strictEqual(getterCalls, 0);

  const symbolConfig = {};
  symbolConfig[Symbol('hidden')] = true;
  assert.throws(() => new DevEventLog(symbolConfig), /symbol keys/);

  const { proxy, revoke } = Proxy.revocable({}, {});
  revoke();
  assert.throws(() => new DevEventLog(proxy), /inspectable plain object/);
});

testGroup('ring_order_and_eviction', () => {
  const log = enabledLog({ capacity: 3 });
  for (let tick = 1; tick <= 5; tick += 1) log.append(input(tick));
  assert.strictEqual(log.size, 3);
  assert.deepStrictEqual(log.snapshot().map((event) => event.tick), [3, 4, 5]);
  assert.deepStrictEqual(log.snapshot().map((event) => event.sequence), [3, 4, 5]);

  const one = enabledLog({ capacity: 1 });
  one.append(input(1));
  one.append(input(2));
  assert.deepStrictEqual(one.snapshot().map((event) => event.sequence), [2]);
});

testGroup('clear_and_sequence', () => {
  const log = enabledLog({ capacity: 2 });
  log.append(input(1));
  log.append(input(2));
  log.clear();
  assert.strictEqual(log.size, 0);
  assert.deepStrictEqual(log.snapshot(), []);
  assert.strictEqual(log.append(input(3)).sequence, 3);

  const exhausted = enabledLog({ capacity: 1 });
  exhausted.nextSequence = Number.MAX_SAFE_INTEGER;
  assert.strictEqual(exhausted.append(input(1)).sequence, Number.MAX_SAFE_INTEGER);
  assert.throws(() => exhausted.append(input(2)), /sequence exhausted/);
});

testGroup('input_validation', () => {
  const log = enabledLog();
  for (const value of [-1, 0.5, Number.NaN, Number.POSITIVE_INFINITY, Number.MAX_SAFE_INTEGER + 1]) {
    assert.throws(() => log.append(input(1, undefined, { epoch: value })), /epoch must be a non-negative safe integer/);
    assert.throws(() => log.append(input(1, undefined, { tick: value })), /tick must be a non-negative safe integer/);
  }
  assert.throws(() => log.append(input(1, undefined, { code: 'unknown' })), /Unknown DevEvent code/);
  const hostileCode = { toString() { throw new Error('must not stringify'); } };
  assert.throws(() => log.append(input(1, undefined, { code: hostileCode })), /Unknown DevEvent code: object/);
  assert.throws(() => log.append(input(1, undefined, { state: 7 })), /state must be a string/);
  assert.throws(() => log.append(input(1, undefined, { reason: false })), /reason must be a string/);
  assert.throws(() => log.append({ ...input(1), unknown: true }), /Unknown DevEvent input key/);
  const symbolInput = input(1);
  symbolInput[Symbol('hidden')] = true;
  assert.throws(() => log.append(symbolInput), /symbol keys/);

  let epochGetterCalls = 0;
  const accessorInput = { tick: 1, code: 'qa.marker' };
  Object.defineProperty(accessorInput, 'epoch', {
    enumerable: true,
    get() {
      epochGetterCalls += 1;
      return epochGetterCalls === 1 ? 0 : Number.NaN;
    },
  });
  assert.throws(() => log.append(accessorInput), /input epoch must be a data property/);
  assert.strictEqual(epochGetterCalls, 0, 'input accessors must never execute');

  const inherited = Object.create(input(1));
  assert.throws(() => log.append(inherited), /plain object/);
  assert.strictEqual(log.append(input(1)).sequence, 1, 'failed appends must not consume sequence numbers');
  const nullPrototypeInput = Object.assign(Object.create(null), input(2));
  assert.strictEqual(log.append(nullPrototypeInput).sequence, 2);
});

testGroup('bounded_strings', () => {
  const log = enabledLog({ maxStateLength: 1, maxReasonLength: 2, maxStringLength: 2 });
  const event = log.append(input(1, '😀😀x', { state: '😀x', reason: 'ёжик' }));
  assert.strictEqual(event.state, '😀');
  assert.strictEqual(event.reason, 'ёж');
  assert.strictEqual(event.payload, '😀😀');
  assert.strictEqual([...event.state].length, 1, 'a surrogate pair must count as one code point');
  assert.strictEqual(event.state.length, 2, 'a retained astral code point must keep both UTF-16 code units');
});

testGroup('immutable_snapshot_and_copy', () => {
  const source = { z: 1, nested: { value: 2 } };
  const log = enabledLog();
  const appended = log.append(input(1, source));
  source.z = 9;
  source.nested.value = 10;
  const snapshot = log.snapshot();
  assert.strictEqual(Object.isFrozen(snapshot), true);
  assert.strictEqual(Object.isFrozen(snapshot[0]), true);
  assert.strictEqual(Object.isFrozen(snapshot[0].payload), true);
  assert.strictEqual(Object.isFrozen(snapshot[0].payload.nested), true);
  assert.notStrictEqual(snapshot[0].payload, source);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(snapshot[0].payload)), { nested: { value: 2 }, z: 1 });
  assert.strictEqual(appended, snapshot[0]);
  assert.throws(() => { snapshot.push(appended); }, TypeError);
  assert.throws(() => { snapshot[0].tick = 99; }, TypeError);
  assert.throws(() => { snapshot[0].payload.z = 99; }, TypeError);
});

testGroup('scalar_and_plain_object_sanitation', () => {
  const payload = Object.create(null);
  payload.finite = 1.25;
  payload.nan = Number.NaN;
  payload.positiveInfinity = Number.POSITIVE_INFINITY;
  payload.big = 123n;
  payload.fn = () => true;
  payload.symbol = Symbol('x');
  payload.undefinedValue = undefined;
  payload.boolean = true;
  payload.nil = null;
  const log = enabledLog();
  const safe = log.append(input(1, payload)).payload;
  assert.strictEqual(Object.getPrototypeOf(safe), null);
  assert.strictEqual(safe.finite, 1.25);
  assert.strictEqual(safe.nan, null);
  assert.strictEqual(safe.positiveInfinity, null);
  assert.strictEqual(safe.big, '123');
  assert.strictEqual(safe.fn, null);
  assert.strictEqual(safe.symbol, null);
  assert.strictEqual(safe.undefinedValue, null);
  assert.strictEqual(safe.boolean, true);
  assert.strictEqual(safe.nil, null);
});

testGroup('accessors_and_enumerability', () => {
  let objectGetterCalls = 0;
  const objectPayload = { visible: 1 };
  Object.defineProperty(objectPayload, 'accessor', {
    enumerable: true,
    get() {
      objectGetterCalls += 1;
      return 'secret';
    },
  });
  Object.defineProperty(objectPayload, 'nonEnumerable', {
    enumerable: false,
    value: 'private',
  });
  const safeObject = enabledLog().append(input(1, objectPayload)).payload;
  assert.strictEqual(objectGetterCalls, 0);
  assert.strictEqual(safeObject.accessor, '[accessor]');
  assert.strictEqual(Object.prototype.hasOwnProperty.call(safeObject, 'nonEnumerable'), false);

  let arrayGetterCalls = 0;
  const arrayPayload = [1, 2, 3];
  Object.defineProperty(arrayPayload, '1', {
    enumerable: true,
    get() {
      arrayGetterCalls += 1;
      return 'secret';
    },
  });
  const safeArray = enabledLog().append(input(1, arrayPayload)).payload;
  assert.strictEqual(arrayGetterCalls, 0);
  assert.deepStrictEqual([...safeArray], [1, '[accessor]', 3]);
  assert.strictEqual(Object.isFrozen(safeArray), true);

  const sparse = [];
  sparse.length = 3;
  sparse[2] = 'tail';
  assert.deepStrictEqual([...enabledLog().append(input(1, sparse)).payload], [null, null, 'tail']);
});

testGroup('shape_and_identity_guards', () => {
  const circular = { value: 1 };
  circular.self = circular;
  const circularSafe = enabledLog().append(input(1, circular)).payload;
  assert.strictEqual(circularSafe.self, '[circular]');

  assert.strictEqual(enabledLog().append(input(1, new Date(0))).payload, '[unsupported-object]');
  assert.strictEqual(enabledLog().append(input(1, new Error('secret'))).payload, '[unsupported-object]');
  class CustomPayload { constructor() { this.value = 1; } }
  assert.strictEqual(enabledLog().append(input(1, new CustomPayload())).payload, '[unsupported-object]');

  const { proxy, revoke } = Proxy.revocable({ value: 1 }, {});
  revoke();
  assert.strictEqual(enabledLog().append(input(1, proxy)).payload, '[uninspectable-object]');

  const pollutionAttempt = JSON.parse('{"__proto__":{"polluted":true},"safe":1}');
  const pollutionSafe = enabledLog().append(input(1, pollutionAttempt)).payload;
  assert.strictEqual(Object.getPrototypeOf(pollutionSafe), null);
  assert.strictEqual(Object.prototype.polluted, undefined);
  assert.strictEqual(Object.prototype.hasOwnProperty.call(pollutionSafe, '__proto__'), true);
});

testGroup('shape_budgets', () => {
  const limited = enabledLog({
    maxArrayLength: 2,
    maxObjectKeys: 2,
    maxDepth: 1,
    maxPayloadNodes: 8,
    maxStringLength: 16,
  });
  assert.deepStrictEqual([...limited.append(input(1, [1, 2, 3])).payload], [1, 2]);
  assert.deepStrictEqual(
    Object.keys(limited.append(input(2, { c: 3, a: 1, b: 2 })).payload),
    ['a', 'b'],
  );
  assert.strictEqual(limited.append(input(3, { nested: { value: 1 } })).payload.nested, '[depth-limit]');

  const nodeLimited = enabledLog({ maxPayloadNodes: 2 });
  const nodeSafe = nodeLimited.append(input(1, { a: 1, b: 2 })).payload;
  assert.strictEqual(nodeSafe.a, 1);
  assert.strictEqual(nodeSafe.__mtr_truncated__, '[node-limit]');

  const collisions = enabledLog({ maxStringLength: 1 });
  const collisionSafe = collisions.append(input(1, { ab: 2, aa: 1 })).payload;
  assert.deepStrictEqual(Object.keys(collisionSafe), ['a']);
  assert.strictEqual(collisionSafe.a, 1);
});

testGroup('payload_utf8_byte_bound', () => {
  for (const maximum of [2, 3, 4, 8, 21, 22, 64]) {
    const event = enabledLog({ maxPayloadBytes: maximum }).append(input(1, '😀'.repeat(100)));
    assert.ok(byteLength(JSON.stringify(event.payload)) <= maximum, `payload limit ${maximum}`);
  }

  const accepted = enabledLog({ maxPayloadBytes: 8 }).append(input(1, 'éé'));
  assert.strictEqual(accepted.payload, 'éé');
  assert.strictEqual(byteLength(JSON.stringify(accepted.payload)), 6);

  const rejected = enabledLog({ maxPayloadBytes: 8 }).append(input(1, '😀😀'));
  assert.strictEqual(rejected.payload, '');
  assert.strictEqual(byteLength(JSON.stringify(rejected.payload)), 2);

  const minimum = enabledLog({ maxPayloadBytes: 2 }).append(input(1, 'x'));
  assert.strictEqual(minimum.payload, '');
  assert.strictEqual(byteLength(JSON.stringify(minimum.payload)), 2);
});

testGroup('stable_serialization', () => {
  const firstPayload = {};
  firstPayload.z = 3;
  firstPayload.a = 1;
  firstPayload.m = { y: 2, b: 1 };
  const secondPayload = {};
  secondPayload.m = { b: 1, y: 2 };
  secondPayload.a = 1;
  secondPayload.z = 3;

  const first = enabledLog();
  const second = enabledLog();
  first.append(input(1, firstPayload));
  second.append(input(1, secondPayload));
  assert.strictEqual(first.exportJson(), second.exportJson());
  assert.deepStrictEqual(Object.keys(first.snapshot()[0].payload), ['a', 'm', 'z']);
});

testGroup('export_event_and_byte_bounds', () => {
  const log = enabledLog({ capacity: 4, maxExportBytes: 4096 });
  for (let tick = 1; tick <= 4; tick += 1) log.append(input(tick, `payload-${tick}-😀`));

  assert.deepStrictEqual(JSON.parse(log.exportJson(2)).map((event) => event.sequence), [3, 4]);
  assert.strictEqual(log.exportJson(0), '[]');
  assert.deepStrictEqual(JSON.parse(log.exportJson(Number.MAX_SAFE_INTEGER)).map((event) => event.sequence), [1, 2, 3, 4]);

  const oneEvent = log.exportJson(1);
  const exactBytes = byteLength(oneEvent);
  assert.strictEqual(log.exportJson(1, exactBytes), oneEvent);
  assert.strictEqual(log.exportJson(1, exactBytes - 1), '[]');
  assert.strictEqual(byteLength(log.exportJson(4, exactBytes)), exactBytes);

  for (const invalid of [-1, 0.5, Number.NaN, Number.POSITIVE_INFINITY, Number.MAX_SAFE_INTEGER + 1]) {
    assert.throws(() => log.exportJson(invalid), /maxEvents must be a non-negative safe integer/);
  }
  for (const invalid of [1, 1.5, Number.NaN, Number.POSITIVE_INFINITY, 4097]) {
    assert.throws(() => log.exportJson(1, invalid), /maxBytes must be in/);
  }
});

testGroup('source_boundary', () => {
  const typesSource = fs.readFileSync(typesPath, 'utf8');
  const logSource = fs.readFileSync(logPath, 'utf8');
  const gameRootSource = fs.readFileSync(gameRootPath, 'utf8');
  for (const source of [typesSource, logSource]) {
    assert.doesNotMatch(source, /from\s+['"]cc['"]|require\s*\(\s*['"]cc['"]\s*\)/);
    assert.doesNotMatch(source, /\bconsole\s*\.|\bDate\s*\.|\bMath\.random\s*\(|\blocalStorage\b|\bfetch\s*\(/);
  }
  assert.doesNotMatch(gameRootSource, /new\s+DevEventLog\b|new\s+LifecycleEpoch\b|\.\/qa\/(?:DevEventLog|DevEventTypes|LifecycleEpoch)/);
  assert.strictEqual((gameRootSource.match(/new\s+GameRootDevEventAdapter\s*\(/g) || []).length, 1);
  assert.match(gameRootSource, /eventsEnabled:\s*DEBUG\b/);
});

console.log(JSON.stringify({
  status: 'PASS',
  testGroups: passedGroups,
  eventCodes: expectedCodes.length,
  strictTypeScript: true,
  typescriptVersion: ts.version,
  compilerTarget: 'ES2015',
  compilerPath: typescriptPath,
  cocosIndependent: true,
  gameRootWired: 'M03.3C_ADAPTER_ONLY',
}));
