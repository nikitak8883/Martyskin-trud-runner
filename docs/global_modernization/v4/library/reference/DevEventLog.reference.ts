import type {
  DevEventInput,
  DevEventLogConfig,
  DevEventRecord,
  DevJsonValue,
} from './DevEventTypes.reference';
import {
  DEFAULT_DEV_EVENT_LOG_CONFIG,
  isDevEventCode,
} from './DevEventTypes.reference';

const CONFIG_LIMITS: Readonly<Record<Exclude<keyof DevEventLogConfig, 'enabled'>, readonly [number, number]>> = Object.freeze({
  capacity: Object.freeze([0, 4096] as const),
  maxStateLength: Object.freeze([0, 256] as const),
  maxReasonLength: Object.freeze([0, 512] as const),
  maxStringLength: Object.freeze([0, 4096] as const),
  maxArrayLength: Object.freeze([0, 256] as const),
  maxObjectKeys: Object.freeze([0, 256] as const),
  maxDepth: Object.freeze([0, 16] as const),
  maxPayloadNodes: Object.freeze([1, 4096] as const),
  maxPayloadBytes: Object.freeze([2, 262144] as const),
  maxExportBytes: Object.freeze([2, 1048576] as const),
});

function validateConfig(config: DevEventLogConfig): void {
  if (typeof config.enabled !== 'boolean') throw new Error('DevEventLog enabled must be boolean');
  for (const key of Object.keys(CONFIG_LIMITS) as Array<Exclude<keyof DevEventLogConfig, 'enabled'>>) {
    const value = config[key];
    const [minimum, maximum] = CONFIG_LIMITS[key];
    if (!Number.isInteger(value) || value < minimum || value > maximum) {
      throw new Error(`DevEventLog ${key} must be an integer in [${minimum}, ${maximum}], got ${value}`);
    }
  }
}

function boundedString(value: unknown, maximum: number): string {
  return String(value).slice(0, maximum);
}

function boundedInputString(value: unknown, maximum: number, label: string): string {
  if (typeof value !== 'string') throw new Error(`${label} must be a string`);
  return value.slice(0, maximum);
}

function nonPlainObjectMarker(value: object, maximum: number): string {
  let tag = 'object';
  try { tag = Object.prototype.toString.call(value).slice(8, -1).toLowerCase() || 'object'; } catch {}
  return boundedString(`[unsupported-${tag}]`, maximum);
}

function toSafeJson(
  value: unknown,
  config: DevEventLogConfig,
  depth = 0,
  seen = new Set<object>(),
  budget = { remainingNodes: config.maxPayloadNodes },
): DevJsonValue {
  if (budget.remainingNodes <= 0) return '[node-limit]';
  budget.remainingNodes -= 1;
  if (value == null || typeof value === 'boolean') return value as null | boolean;
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  if (typeof value === 'string') return boundedString(value, config.maxStringLength);
  if (typeof value === 'bigint') return boundedString(value.toString(), config.maxStringLength);
  if (typeof value === 'function' || typeof value === 'symbol' || typeof value === 'undefined') return null;
  if (typeof value !== 'object') return boundedString(value, config.maxStringLength);
  if (depth >= config.maxDepth) return '[depth-limit]';
  if (seen.has(value)) return '[circular]';

  seen.add(value);
  try {
    if (Array.isArray(value)) {
      const result: DevJsonValue[] = [];
      for (const item of value.slice(0, config.maxArrayLength)) {
        if (budget.remainingNodes <= 0) { result.push('[node-limit]'); break; }
        result.push(toSafeJson(item, config, depth + 1, seen, budget));
      }
      return Object.freeze(result);
    }

    let prototype: object | null;
    try { prototype = Object.getPrototypeOf(value) as object | null; } catch { return '[uninspectable-object]'; }
    if (prototype !== Object.prototype && prototype !== null) return nonPlainObjectMarker(value, config.maxStringLength);

    let descriptors: PropertyDescriptorMap;
    try { descriptors = Object.getOwnPropertyDescriptors(value); } catch { return '[uninspectable-object]'; }
    const keys = Object.keys(descriptors).sort().slice(0, config.maxObjectKeys);
    const result = Object.create(null) as Record<string, DevJsonValue>;
    for (const originalKey of keys) {
      if (budget.remainingNodes <= 0) {
        if (!Object.prototype.hasOwnProperty.call(result, '__mtr_truncated__')) result.__mtr_truncated__ = '[node-limit]';
        break;
      }
      const key = boundedString(originalKey, config.maxStringLength);
      if (Object.prototype.hasOwnProperty.call(result, key)) continue;
      const descriptor = descriptors[originalKey];
      if (!descriptor || !Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
        result[key] = '[accessor]';
      } else {
        result[key] = toSafeJson(descriptor.value, config, depth + 1, seen, budget);
      }
    }
    return Object.freeze(result);
  } finally {
    seen.delete(value);
  }
}

function utf8ByteLength(value: string): number {
  let bytes = 0;
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    if (code < 0x80) bytes += 1;
    else if (code < 0x800) bytes += 2;
    else if (code >= 0xd800 && code <= 0xdbff && index + 1 < value.length) {
      const next = value.charCodeAt(index + 1);
      if (next >= 0xdc00 && next <= 0xdfff) { bytes += 4; index += 1; }
      else bytes += 3;
    } else bytes += 3;
  }
  return bytes;
}

function boundedPayload(value: unknown, config: DevEventLogConfig): DevJsonValue {
  const payload = toSafeJson(value, config);
  const serialized = JSON.stringify(payload);
  return utf8ByteLength(serialized) <= config.maxPayloadBytes ? payload : '[payload-byte-limit]';
}

function requireNonNegativeSafeInteger(value: number, label: string): void {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new Error(`${label} must be a non-negative safe integer, got ${value}`);
  }
}

/** Fixed-capacity ring buffer. Append is O(1); serialization is separately bounded. */
export class DevEventLog {
  private readonly config: DevEventLogConfig;
  private readonly buffer: Array<DevEventRecord | undefined>;
  private start = 0;
  private length = 0;
  private nextSequence = 1;

  public constructor(config: Partial<DevEventLogConfig> = {}) {
    this.config = Object.freeze({ ...DEFAULT_DEV_EVENT_LOG_CONFIG, ...config });
    validateConfig(this.config);
    this.buffer = new Array<DevEventRecord | undefined>(this.config.capacity);
  }

  public get enabled(): boolean { return this.config.enabled; }
  public get size(): number { return this.length; }
  public get capacity(): number { return this.config.capacity; }

  public append(input: DevEventInput): DevEventRecord | undefined {
    if (!this.config.enabled || this.config.capacity === 0) return undefined;
    requireNonNegativeSafeInteger(input.epoch, 'DevEvent epoch');
    requireNonNegativeSafeInteger(input.tick, 'DevEvent tick');
    if (!isDevEventCode(input.code)) throw new Error(`Unknown DevEvent code: ${String(input.code)}`);
    if (this.nextSequence > Number.MAX_SAFE_INTEGER) throw new Error('DevEvent sequence exhausted');

    const event: DevEventRecord = Object.freeze({
      sequence: this.nextSequence,
      epoch: input.epoch,
      tick: input.tick,
      code: input.code,
      ...(input.state === undefined ? {} : { state: boundedInputString(input.state, this.config.maxStateLength, 'DevEvent state') }),
      ...(input.reason === undefined ? {} : { reason: boundedInputString(input.reason, this.config.maxReasonLength, 'DevEvent reason') }),
      ...(input.payload === undefined ? {} : { payload: boundedPayload(input.payload, this.config) }),
    });
    this.nextSequence += 1;

    if (this.length < this.config.capacity) {
      this.buffer[(this.start + this.length) % this.config.capacity] = event;
      this.length += 1;
    } else {
      this.buffer[this.start] = event;
      this.start = (this.start + 1) % this.config.capacity;
    }
    return event;
  }

  public snapshot(): readonly DevEventRecord[] {
    const result: DevEventRecord[] = [];
    for (let index = 0; index < this.length; index += 1) {
      const event = this.buffer[(this.start + index) % this.config.capacity];
      if (event) result.push(event);
    }
    return Object.freeze(result);
  }

  public clear(): void {
    this.buffer.fill(undefined);
    this.start = 0;
    this.length = 0;
  }

  public exportJson(maxEvents = this.config.capacity, maxBytes = this.config.maxExportBytes): string {
    requireNonNegativeSafeInteger(maxEvents, 'DevEvent export maxEvents');
    if (!Number.isSafeInteger(maxBytes) || maxBytes < 2 || maxBytes > this.config.maxExportBytes) {
      throw new Error(`DevEvent export maxBytes must be in [2, ${this.config.maxExportBytes}], got ${maxBytes}`);
    }
    const snapshot = this.snapshot();
    const start = Math.max(0, snapshot.length - Math.min(maxEvents, snapshot.length));
    const encoded: string[] = [];
    let bytes = 2;
    for (let index = snapshot.length - 1; index >= start; index -= 1) {
      const item = JSON.stringify(snapshot[index]);
      const addition = utf8ByteLength(item) + (encoded.length > 0 ? 1 : 0);
      if (bytes + addition > maxBytes) break;
      encoded.unshift(item);
      bytes += addition;
    }
    return `[${encoded.join(',')}]`;
  }
}
