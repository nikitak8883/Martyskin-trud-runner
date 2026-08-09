/** Reference-only M03.3A contract. Default is fail-closed disabled. */
export const DEV_EVENT_CODES = Object.freeze([
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
] as const);

export type DevEventCode = typeof DEV_EVENT_CODES[number];
export type DevScalar = string | number | boolean | null;
export type DevJsonValue = DevScalar | readonly DevJsonValue[] | Readonly<{ [key: string]: DevJsonValue }>;

export interface DevEventRecord {
  readonly sequence: number;
  readonly epoch: number;
  readonly tick: number;
  readonly code: DevEventCode;
  readonly state?: string;
  readonly reason?: string;
  readonly payload?: DevJsonValue;
}

export interface DevEventInput {
  readonly epoch: number;
  readonly tick: number;
  readonly code: DevEventCode;
  readonly state?: string;
  readonly reason?: string;
  readonly payload?: unknown;
}

export interface DevEventLogConfig {
  readonly enabled: boolean;
  readonly capacity: number;
  readonly maxStateLength: number;
  readonly maxReasonLength: number;
  readonly maxStringLength: number;
  readonly maxArrayLength: number;
  readonly maxObjectKeys: number;
  readonly maxDepth: number;
  readonly maxPayloadNodes: number;
  readonly maxPayloadBytes: number;
  readonly maxExportBytes: number;
}

export const DEFAULT_DEV_EVENT_LOG_CONFIG: DevEventLogConfig = Object.freeze({
  enabled: false,
  capacity: 256,
  maxStateLength: 64,
  maxReasonLength: 96,
  maxStringLength: 256,
  maxArrayLength: 24,
  maxObjectKeys: 24,
  maxDepth: 4,
  maxPayloadNodes: 512,
  maxPayloadBytes: 16384,
  maxExportBytes: 65536,
});

export function isDevEventCode(value: unknown): value is DevEventCode {
  return typeof value === 'string' && (DEV_EVENT_CODES as readonly string[]).indexOf(value) >= 0;
}
