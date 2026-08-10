import type {
    DevEventInput,
    DevEventLogConfig,
    DevEventRecord,
    DevJsonValue,
} from './DevEventTypes';
import {
    DEFAULT_DEV_EVENT_LOG_CONFIG,
    isDevEventCode,
} from './DevEventTypes';

type NumericConfigKey = Exclude<keyof DevEventLogConfig, 'enabled'>;

const CONFIG_KEYS: readonly (keyof DevEventLogConfig)[] = Object.freeze([
    'enabled',
    'capacity',
    'maxStateLength',
    'maxReasonLength',
    'maxStringLength',
    'maxArrayLength',
    'maxObjectKeys',
    'maxDepth',
    'maxPayloadNodes',
    'maxPayloadBytes',
    'maxExportBytes',
]);

const INPUT_KEYS: readonly (keyof DevEventInput)[] = Object.freeze([
    'epoch',
    'tick',
    'code',
    'state',
    'reason',
    'payload',
]);

const REQUIRED_INPUT_KEYS: readonly (keyof DevEventInput)[] = Object.freeze([
    'epoch',
    'tick',
    'code',
]);

const CONFIG_LIMITS: Readonly<Record<NumericConfigKey, readonly [number, number]>> = Object.freeze({
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
    if (typeof config.enabled !== 'boolean') {
        throw new Error('DevEventLog enabled must be boolean');
    }
    for (const key of Object.keys(CONFIG_LIMITS) as NumericConfigKey[]) {
        const value = config[key];
        const [minimum, maximum] = CONFIG_LIMITS[key];
        if (!Number.isInteger(value) || value < minimum || value > maximum) {
            throw new Error(`DevEventLog ${key} must be an integer in [${minimum}, ${maximum}], got ${value}`);
        }
    }
}

function ownPropertyDescriptors(value: object): PropertyDescriptorMap {
    const result = Object.create(null) as PropertyDescriptorMap;
    for (const key of Object.getOwnPropertyNames(value)) {
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (descriptor) result[key] = descriptor;
    }
    return result;
}

function normalizeConfig(input: Partial<DevEventLogConfig>): DevEventLogConfig {
    if (input === null || typeof input !== 'object') {
        throw new Error('DevEventLog config must be a plain object');
    }

    let isArray = false;
    let prototype: object | null;
    let descriptors: PropertyDescriptorMap;
    let symbolCount = 0;
    try {
        isArray = Array.isArray(input);
        prototype = Object.getPrototypeOf(input) as object | null;
        descriptors = ownPropertyDescriptors(input);
        symbolCount = Object.getOwnPropertySymbols(input).length;
    } catch {
        throw new Error('DevEventLog config must be an inspectable plain object');
    }
    if (isArray || (prototype !== Object.prototype && prototype !== null)) {
        throw new Error('DevEventLog config must be a plain object');
    }
    if (symbolCount > 0) {
        throw new Error('DevEventLog config must not contain symbol keys');
    }

    const overrides = Object.create(null) as Record<string, unknown>;
    for (const key of Object.keys(descriptors)) {
        if ((CONFIG_KEYS as readonly string[]).indexOf(key) < 0) {
            throw new Error(`Unknown DevEventLog config key: ${key}`);
        }
        const descriptor = descriptors[key];
        if (!descriptor || !Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
            throw new Error(`DevEventLog config ${key} must be a data property`);
        }
        overrides[key] = descriptor.value;
    }

    const config = {
        ...DEFAULT_DEV_EVENT_LOG_CONFIG,
        ...overrides,
    } as DevEventLogConfig;
    validateConfig(config);
    return Object.freeze(config);
}

function normalizeInput(input: DevEventInput): DevEventInput {
    if (input === null || typeof input !== 'object') {
        throw new Error('DevEvent input must be a plain object');
    }

    let isArray = false;
    let prototype: object | null;
    let descriptors: PropertyDescriptorMap;
    let symbolCount = 0;
    try {
        isArray = Array.isArray(input);
        prototype = Object.getPrototypeOf(input) as object | null;
        descriptors = ownPropertyDescriptors(input);
        symbolCount = Object.getOwnPropertySymbols(input).length;
    } catch {
        throw new Error('DevEvent input must be an inspectable plain object');
    }
    if (isArray || (prototype !== Object.prototype && prototype !== null)) {
        throw new Error('DevEvent input must be a plain object');
    }
    if (symbolCount > 0) {
        throw new Error('DevEvent input must not contain symbol keys');
    }

    const values = Object.create(null) as Record<string, unknown>;
    for (const key of Object.keys(descriptors)) {
        if ((INPUT_KEYS as readonly string[]).indexOf(key) < 0) {
            throw new Error(`Unknown DevEvent input key: ${key}`);
        }
        const descriptor = descriptors[key];
        if (!descriptor || !Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
            throw new Error(`DevEvent input ${key} must be a data property`);
        }
        values[key] = descriptor.value;
    }
    for (const key of REQUIRED_INPUT_KEYS) {
        if (!Object.prototype.hasOwnProperty.call(values, key)) {
            throw new Error(`DevEvent input requires own data property: ${key}`);
        }
    }

    return {
        epoch: values.epoch as number,
        tick: values.tick as number,
        code: values.code as DevEventInput['code'],
        ...(Object.prototype.hasOwnProperty.call(values, 'state')
            ? { state: values.state as string | undefined }
            : {}),
        ...(Object.prototype.hasOwnProperty.call(values, 'reason')
            ? { reason: values.reason as string | undefined }
            : {}),
        ...(Object.prototype.hasOwnProperty.call(values, 'payload')
            ? { payload: values.payload }
            : {}),
    };
}

function boundedString(value: string, maximum: number): string {
    let end = 0;
    let codePoints = 0;
    while (end < value.length && codePoints < maximum) {
        const first = value.charCodeAt(end);
        if (first >= 0xd800 && first <= 0xdbff && end + 1 < value.length) {
            const second = value.charCodeAt(end + 1);
            end += second >= 0xdc00 && second <= 0xdfff ? 2 : 1;
        } else {
            end += 1;
        }
        codePoints += 1;
    }
    return value.slice(0, end);
}

function marker(value: string, config: DevEventLogConfig): string {
    return boundedString(value, config.maxStringLength);
}

function toSafeJson(
    value: unknown,
    config: DevEventLogConfig,
    depth = 0,
    seen = new Set<object>(),
    budget = { remainingNodes: config.maxPayloadNodes },
): DevJsonValue {
    if (budget.remainingNodes <= 0) return marker('[node-limit]', config);
    budget.remainingNodes -= 1;

    if (value === null) return null;
    if (typeof value === 'boolean') return value;
    if (typeof value === 'number') return Number.isFinite(value) ? value : null;
    if (typeof value === 'string') return boundedString(value, config.maxStringLength);
    if (typeof value === 'bigint') return boundedString(value.toString(), config.maxStringLength);
    if (typeof value === 'function' || typeof value === 'symbol' || typeof value === 'undefined') return null;
    if (typeof value !== 'object') return marker('[unsupported-value]', config);
    if (depth >= config.maxDepth) return marker('[depth-limit]', config);
    if (seen.has(value)) return marker('[circular]', config);

    let isArray: boolean;
    try {
        isArray = Array.isArray(value);
    } catch {
        return marker('[uninspectable-object]', config);
    }

    if (isArray) {
        let descriptors: PropertyDescriptorMap;
        try {
            descriptors = ownPropertyDescriptors(value);
        } catch {
            return marker('[uninspectable-object]', config);
        }
        const lengthDescriptor = descriptors.length;
        if (!lengthDescriptor || !Object.prototype.hasOwnProperty.call(lengthDescriptor, 'value')) {
            return marker('[uninspectable-array]', config);
        }
        const arrayLength = lengthDescriptor.value;
        if (!Number.isSafeInteger(arrayLength) || arrayLength < 0) {
            return marker('[uninspectable-array]', config);
        }

        seen.add(value);
        try {
            const result: DevJsonValue[] = [];
            const boundedLength = Math.min(arrayLength, config.maxArrayLength);
            for (let index = 0; index < boundedLength; index += 1) {
                if (budget.remainingNodes <= 0) {
                    result.push(marker('[node-limit]', config));
                    break;
                }
                const descriptor = descriptors[String(index)];
                if (!descriptor) {
                    result.push(toSafeJson(null, config, depth + 1, seen, budget));
                } else if (!Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
                    result.push(toSafeJson(marker('[accessor]', config), config, depth + 1, seen, budget));
                } else {
                    result.push(toSafeJson(descriptor.value, config, depth + 1, seen, budget));
                }
            }
            return Object.freeze(result);
        } finally {
            seen.delete(value);
        }
    }

    let prototype: object | null;
    try {
        prototype = Object.getPrototypeOf(value) as object | null;
    } catch {
        return marker('[uninspectable-object]', config);
    }
    if (prototype !== Object.prototype && prototype !== null) {
        return marker('[unsupported-object]', config);
    }

    let descriptors: PropertyDescriptorMap;
    try {
        descriptors = ownPropertyDescriptors(value);
    } catch {
        return marker('[uninspectable-object]', config);
    }

    seen.add(value);
    try {
        const keys = Object.keys(descriptors)
            .filter((key) => descriptors[key]?.enumerable === true)
            .sort()
            .slice(0, config.maxObjectKeys);
        const result = Object.create(null) as Record<string, DevJsonValue>;
        for (const originalKey of keys) {
            if (budget.remainingNodes <= 0) {
                const truncationKey = marker('__mtr_truncated__', config);
                if (!Object.prototype.hasOwnProperty.call(result, truncationKey)) {
                    result[truncationKey] = marker('[node-limit]', config);
                }
                break;
            }
            const key = boundedString(originalKey, config.maxStringLength);
            if (Object.prototype.hasOwnProperty.call(result, key)) continue;
            const descriptor = descriptors[originalKey];
            if (!descriptor || !Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
                result[key] = toSafeJson(marker('[accessor]', config), config, depth + 1, seen, budget);
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
        if (code < 0x80) {
            bytes += 1;
        } else if (code < 0x800) {
            bytes += 2;
        } else if (code >= 0xd800 && code <= 0xdbff && index + 1 < value.length) {
            const next = value.charCodeAt(index + 1);
            if (next >= 0xdc00 && next <= 0xdfff) {
                bytes += 4;
                index += 1;
            } else {
                bytes += 3;
            }
        } else {
            bytes += 3;
        }
    }
    return bytes;
}

function payloadLimitFallback(config: DevEventLogConfig): DevJsonValue {
    const boundedMarker = marker('[payload-byte-limit]', config);
    if (utf8ByteLength(JSON.stringify(boundedMarker)) <= config.maxPayloadBytes) {
        return boundedMarker;
    }
    // JSON.stringify('') is exactly two UTF-8 bytes, matching the validated
    // minimum and keeping the byte bound true even for maxPayloadBytes = 2.
    return '';
}

function boundedPayload(value: unknown, config: DevEventLogConfig): DevJsonValue {
    const payload = toSafeJson(value, config);
    const serialized = JSON.stringify(payload);
    return utf8ByteLength(serialized) <= config.maxPayloadBytes
        ? payload
        : payloadLimitFallback(config);
}

function requireNonNegativeSafeInteger(value: number, label: string): void {
    if (!Number.isSafeInteger(value) || value < 0) {
        throw new Error(`${label} must be a non-negative safe integer, got ${value}`);
    }
}

/**
 * Fixed-capacity ring buffer. Ring-slot insertion is O(1), while recursive
 * payload output and export are bounded by configuration. Initial own-key
 * discovery is proportional to the supplied object, so runtime adapters must
 * pass small allowlisted payload literals rather than hostile/unbounded input.
 */
export class DevEventLog {
    private readonly config: DevEventLogConfig;
    private readonly buffer: Array<DevEventRecord | undefined>;
    private start = 0;
    private length = 0;
    private nextSequence = 1;

    public constructor(config: Partial<DevEventLogConfig> = {}) {
        this.config = normalizeConfig(config);
        this.buffer = new Array<DevEventRecord | undefined>(this.config.capacity);
    }

    public get enabled(): boolean {
        return this.config.enabled;
    }

    public get size(): number {
        return this.length;
    }

    public get capacity(): number {
        return this.config.capacity;
    }

    public append(input: DevEventInput): DevEventRecord | undefined {
        if (!this.config.enabled || this.config.capacity === 0) return undefined;
        const normalized = normalizeInput(input);
        const { epoch, tick, code, state, reason, payload } = normalized;
        requireNonNegativeSafeInteger(epoch, 'DevEvent epoch');
        requireNonNegativeSafeInteger(tick, 'DevEvent tick');
        if (!isDevEventCode(code)) {
            const value = typeof code === 'string'
                ? boundedString(code, 64)
                : typeof code;
            throw new Error(`Unknown DevEvent code: ${value}`);
        }
        if (this.nextSequence > Number.MAX_SAFE_INTEGER) {
            throw new Error('DevEvent sequence exhausted');
        }
        if (state !== undefined && typeof state !== 'string') {
            throw new Error('DevEvent state must be a string');
        }
        if (reason !== undefined && typeof reason !== 'string') {
            throw new Error('DevEvent reason must be a string');
        }

        const event: DevEventRecord = Object.freeze({
            sequence: this.nextSequence,
            epoch,
            tick,
            code,
            ...(state === undefined
                ? {}
                : { state: boundedString(state, this.config.maxStateLength) }),
            ...(reason === undefined
                ? {}
                : { reason: boundedString(reason, this.config.maxReasonLength) }),
            ...(payload === undefined
                ? {}
                : { payload: boundedPayload(payload, this.config) }),
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
        const first = Math.max(0, snapshot.length - Math.min(maxEvents, snapshot.length));
        const encoded: string[] = [];
        let bytes = 2;
        for (let index = snapshot.length - 1; index >= first; index -= 1) {
            const item = JSON.stringify(snapshot[index]);
            const addition = utf8ByteLength(item) + (encoded.length > 0 ? 1 : 0);
            if (bytes + addition > maxBytes) break;
            encoded.unshift(item);
            bytes += addition;
        }
        return `[${encoded.join(',')}]`;
    }
}
