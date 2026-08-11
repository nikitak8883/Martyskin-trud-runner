export const POWER_UP_KIND_COUNT = 9;

export const POWER_UP_EFFECT_KEYS = Object.freeze([
    'jumpBoost',
    'dashBoost',
    'armor',
    'magnet',
    'vestBonus',
    'shieldBonus',
    'coffeeBoost',
    'blueprintBonus',
    'passBonus',
    'extraLifeAura',
] as const);

export type PowerUpEffectKey = typeof POWER_UP_EFFECT_KEYS[number];
export type PowerUpPhase = 'spawned' | 'collected' | 'active' | 'expired' | 'cleaned';
export type PowerUpLifecycleAction =
    | 'epoch_started'
    | 'spawned'
    | 'collected'
    | 'activated'
    | 'effect_expired'
    | 'expired'
    | 'cleaned'
    | 'session_cleaned'
    | 'invalidated'
    | 'qa_seeded';

export type PowerUpRejectionReason =
    | 'invalid_epoch'
    | 'stale_epoch'
    | 'session_closed'
    | 'missing_instance'
    | 'duplicate_instance'
    | 'invalid_phase'
    | 'type_mismatch';

export interface PowerUpLifecycleOptions {
    readonly getEpoch: () => number;
    readonly getTick: () => number;
    readonly allowQaMutation?: boolean;
    readonly onEvent?: (event: PowerUpLifecycleEvent) => void;
}

export interface PowerUpEffectState {
    readonly jumpBoost: number;
    readonly dashBoost: number;
    readonly armor: number;
    readonly magnet: number;
    readonly vestBonus: number;
    readonly shieldBonus: number;
    readonly coffeeBoost: number;
    readonly blueprintBonus: number;
    readonly passBonus: number;
    readonly extraLifeAura: number;
}

export interface PowerUpInstanceSnapshot {
    readonly id: string;
    readonly type: number;
    readonly kind: number;
    readonly epoch: number;
    readonly phase: PowerUpPhase;
    readonly spawnedAtTick: number;
    readonly collectedAtTick?: number;
    readonly activatedAtTick?: number;
    readonly expiredAtTick?: number;
    readonly cleanedAtTick?: number;
    readonly effectKeys: readonly PowerUpEffectKey[];
}

export interface PowerUpOneShotEffects {
    readonly resetDashCooldown: boolean;
    readonly scoreDelta: number;
    readonly healAmount: number;
    readonly invincibilityFloor: number;
}

export interface PowerUpLifecycleEvent {
    readonly sequence: number;
    readonly epoch: number;
    readonly tick: number;
    readonly action: PowerUpLifecycleAction;
    readonly reason?: string;
    readonly effectKey?: PowerUpEffectKey;
    readonly instance?: PowerUpInstanceSnapshot;
}

export interface PowerUpLifecycleSnapshot {
    readonly epoch: number | null;
    readonly sessionOpen: boolean;
    readonly effects: PowerUpEffectState;
    readonly runBonusCount: number;
    readonly runBonusSeen: readonly boolean[];
    readonly instanceCount: number;
    readonly activeInstanceCount: number;
}

export type PowerUpRecordResult =
    | { readonly accepted: true; readonly record: PowerUpInstanceSnapshot }
    | { readonly accepted: false; readonly reason: PowerUpRejectionReason };

export type PowerUpActivationResult =
    | {
        readonly accepted: true;
        readonly record: PowerUpInstanceSnapshot;
        readonly kind: number;
        readonly oneShot: PowerUpOneShotEffects;
    }
    | { readonly accepted: false; readonly reason: PowerUpRejectionReason };

interface MutablePowerUpInstance {
    id: string;
    type: number;
    kind: number;
    epoch: number;
    phase: PowerUpPhase;
    spawnedAtTick: number;
    collectedAtTick?: number;
    activatedAtTick?: number;
    expiredAtTick?: number;
    cleanedAtTick?: number;
    effectKeys: PowerUpEffectKey[];
}

function zeroEffects(): Record<PowerUpEffectKey, number> {
    return {
        jumpBoost: 0,
        dashBoost: 0,
        armor: 0,
        magnet: 0,
        vestBonus: 0,
        shieldBonus: 0,
        coffeeBoost: 0,
        blueprintBonus: 0,
        passBonus: 0,
        extraLifeAura: 0,
    };
}

function frozenOneShot(
    resetDashCooldown = false,
    scoreDelta = 0,
    healAmount = 0,
    invincibilityFloor = 0,
): PowerUpOneShotEffects {
    return Object.freeze({ resetDashCooldown, scoreDelta, healAmount, invincibilityFloor });
}

/**
 * M03.6 single owner for power-up entity phases, effect timers and per-run
 * collection counters. Cocos rendering and one-shot game mutations remain in
 * GameRoot and consume immutable activation commands returned by this owner.
 */
export class PowerUpLifecycle {
    private readonly instances = new Map<string, MutablePowerUpInstance>();
    private effects: Record<PowerUpEffectKey, number> = zeroEffects();
    private runCount = 0;
    private runSeen: boolean[] = new Array(POWER_UP_KIND_COUNT).fill(false);
    private activeEpoch: number | null = null;
    private sessionOpen = false;
    private nextSequence = 1;

    public constructor(private readonly options: PowerUpLifecycleOptions) {
        if (typeof options.getEpoch !== 'function' || typeof options.getTick !== 'function') {
            throw new Error('PowerUpLifecycle requires injected epoch and tick readers');
        }
    }

    public beginEpoch(expectedEpoch: number, reason: string): PowerUpLifecycleSnapshot {
        const epoch = this.readEpoch();
        const tick = this.readTick();
        if (expectedEpoch !== epoch) throw new Error('Power-up epoch start does not match the injected epoch');
        this.cleanupInstances(`epoch:${reason}`, epoch, tick);
        this.effects = zeroEffects();
        this.runCount = 0;
        this.runSeen = new Array(POWER_UP_KIND_COUNT).fill(false);
        this.activeEpoch = epoch;
        this.sessionOpen = true;
        this.emit('epoch_started', epoch, tick, reason);
        return this.snapshot();
    }

    public invalidate(expectedEpoch: number, reason: string): PowerUpLifecycleSnapshot {
        const epoch = this.readEpoch();
        const tick = this.readTick();
        if (expectedEpoch !== epoch) throw new Error('Power-up invalidation does not match the injected epoch');
        this.cleanupInstances(`invalidate:${reason}`, epoch, tick);
        this.effects = zeroEffects();
        this.activeEpoch = epoch;
        this.sessionOpen = false;
        this.emit('invalidated', epoch, tick, reason);
        return this.snapshot();
    }

    public spawn(id: string, type: number): PowerUpRecordResult {
        this.assertSynchronizedOpenSession();
        if (!/^[A-Za-z0-9][A-Za-z0-9:._-]{0,127}$/.test(id)) {
            throw new Error(`Invalid power-up instance id: ${id}`);
        }
        const kind = this.requireKind(type);
        if (this.instances.has(id)) return { accepted: false, reason: 'duplicate_instance' };
        const epoch = this.readEpoch();
        const tick = this.readTick();
        const record: MutablePowerUpInstance = {
            id,
            type,
            kind,
            epoch,
            phase: 'spawned',
            spawnedAtTick: tick,
            effectKeys: [],
        };
        this.instances.set(id, record);
        this.emit('spawned', epoch, tick, undefined, undefined, record);
        return { accepted: true, record: this.freezeRecord(record) };
    }

    public collect(id: string, expectedEpoch: number): PowerUpRecordResult {
        const rejection = this.precondition(id, expectedEpoch);
        if (rejection) return rejection;
        const record = this.instances.get(id) as MutablePowerUpInstance;
        if (record.phase !== 'spawned') return { accepted: false, reason: 'invalid_phase' };
        const tick = this.readTick();
        record.phase = 'collected';
        record.collectedAtTick = tick;
        this.emit('collected', expectedEpoch, tick, undefined, undefined, record);
        return { accepted: true, record: this.freezeRecord(record) };
    }

    public activate(id: string, type: number, expectedEpoch: number): PowerUpActivationResult {
        const rejection = this.precondition(id, expectedEpoch);
        if (rejection) return rejection;
        const record = this.instances.get(id) as MutablePowerUpInstance;
        if (record.phase !== 'collected') return { accepted: false, reason: 'invalid_phase' };
        const kind = this.requireKind(type);
        if (record.kind !== kind || record.type !== type) return { accepted: false, reason: 'type_mismatch' };
        const tick = this.readTick();

        const effectKeys: PowerUpEffectKey[] = [];
        let oneShot = frozenOneShot();
        this.runCount += 1;
        this.runSeen[kind] = true;
        switch (kind) {
            case 0:
                this.effects.jumpBoost = 14;
                this.effects.blueprintBonus = Math.max(this.effects.blueprintBonus, 5);
                effectKeys.push('jumpBoost', 'blueprintBonus');
                break;
            case 1:
                this.effects.dashBoost = 12;
                effectKeys.push('dashBoost');
                oneShot = frozenOneShot(true);
                break;
            case 2:
                this.effects.shieldBonus = 18;
                effectKeys.push('shieldBonus');
                break;
            case 3:
                this.effects.magnet = 14;
                effectKeys.push('magnet');
                break;
            case 4:
                this.effects.vestBonus = 16;
                effectKeys.push('vestBonus');
                break;
            case 5:
                this.effects.coffeeBoost = 10;
                this.effects.jumpBoost = Math.max(this.effects.jumpBoost, 8);
                this.effects.dashBoost = Math.max(this.effects.dashBoost, 6);
                effectKeys.push('coffeeBoost', 'jumpBoost', 'dashBoost');
                oneShot = frozenOneShot(true);
                break;
            case 6:
                this.effects.blueprintBonus = 16;
                effectKeys.push('blueprintBonus');
                oneShot = frozenOneShot(false, 50);
                break;
            case 7:
                this.effects.passBonus = 16;
                effectKeys.push('passBonus');
                oneShot = frozenOneShot(false, 0, 0, 0.75);
                break;
            case 8:
                this.effects.extraLifeAura = 10;
                effectKeys.push('extraLifeAura');
                oneShot = frozenOneShot(false, 100, 1);
                break;
        }

        record.phase = 'active';
        record.activatedAtTick = tick;
        record.effectKeys = effectKeys;
        this.emit('activated', expectedEpoch, tick, undefined, undefined, record);
        return {
            accepted: true,
            record: this.freezeRecord(record),
            kind,
            oneShot,
        };
    }

    public tick(dt: number): PowerUpLifecycleSnapshot {
        this.assertSynchronizedOpenSession();
        if (!Number.isFinite(dt) || dt < 0) throw new Error('Power-up dt must be a finite non-negative number');
        const epoch = this.readEpoch();
        const tick = this.readTick();
        for (const key of POWER_UP_EFFECT_KEYS) {
            const previous = this.effects[key];
            this.effects[key] -= dt;
            if (previous > 0 && this.effects[key] <= 0) {
                this.emit('effect_expired', epoch, tick, 'timer_elapsed', key);
            }
        }
        this.expireCompletedInstances(epoch, tick);
        return this.snapshot();
    }

    public consumeArmor(expectedEpoch: number): boolean {
        const rejection = this.sessionPrecondition(expectedEpoch);
        if (rejection || this.effects.armor <= 0) return false;
        const tick = this.readTick();
        this.effects.armor = 0;
        this.emit('effect_expired', expectedEpoch, tick, 'consumed', 'armor');
        this.expireCompletedInstances(expectedEpoch, tick);
        return true;
    }

    public cleanupWorldInstances(reason: string): PowerUpLifecycleSnapshot {
        this.assertSynchronizedOpenSession();
        this.cleanupInstances(reason, this.readEpoch(), this.readTick());
        return this.snapshot();
    }

    public cleanupSession(reason: string): PowerUpLifecycleSnapshot {
        this.assertSynchronizedEpoch();
        const epoch = this.readEpoch();
        const tick = this.readTick();
        this.cleanupInstances(reason, epoch, tick);
        this.effects = zeroEffects();
        this.sessionOpen = false;
        this.emit('session_cleaned', epoch, tick, reason);
        return this.snapshot();
    }

    public seedAllEffectsForQa(durationSeconds: number, expectedEpoch: number): PowerUpLifecycleSnapshot {
        if (!this.options.allowQaMutation) throw new Error('Power-up QA mutation is disabled');
        const rejection = this.sessionPrecondition(expectedEpoch);
        if (rejection) throw new Error(`Power-up QA seed rejected: ${rejection.reason}`);
        if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) {
            throw new Error('Power-up QA duration must be a finite positive number');
        }
        const tick = this.readTick();
        for (const key of POWER_UP_EFFECT_KEYS) this.effects[key] = durationSeconds;
        this.emit('qa_seeded', expectedEpoch, tick, `duration=${durationSeconds}`);
        return this.snapshot();
    }

    public effectSeconds(key: PowerUpEffectKey): number {
        return this.effects[key];
    }

    public get runBonusCount(): number {
        return this.runCount;
    }

    public seenKinds(): readonly boolean[] {
        return Object.freeze(this.runSeen.slice());
    }

    public instance(id: string): PowerUpInstanceSnapshot | null {
        const record = this.instances.get(id);
        return record ? this.freezeRecord(record) : null;
    }

    public snapshot(): PowerUpLifecycleSnapshot {
        let activeInstanceCount = 0;
        for (const record of this.instances.values()) if (record.phase === 'active') activeInstanceCount += 1;
        return Object.freeze({
            epoch: this.activeEpoch,
            sessionOpen: this.sessionOpen,
            effects: Object.freeze({ ...this.effects }),
            runBonusCount: this.runCount,
            runBonusSeen: Object.freeze(this.runSeen.slice()),
            instanceCount: this.instances.size,
            activeInstanceCount,
        });
    }

    private precondition(id: string, expectedEpoch: number): { readonly accepted: false; readonly reason: PowerUpRejectionReason } | null {
        const sessionRejection = this.sessionPrecondition(expectedEpoch);
        if (sessionRejection) return sessionRejection;
        const record = this.instances.get(id);
        if (!record) return { accepted: false, reason: 'missing_instance' };
        if (record.epoch !== expectedEpoch) return { accepted: false, reason: 'stale_epoch' };
        return null;
    }

    private sessionPrecondition(expectedEpoch: number): { readonly accepted: false; readonly reason: PowerUpRejectionReason } | null {
        if (!Number.isSafeInteger(expectedEpoch) || expectedEpoch < 0) {
            return { accepted: false, reason: 'invalid_epoch' };
        }
        const currentEpoch = this.readEpoch();
        if (this.activeEpoch !== currentEpoch || expectedEpoch !== currentEpoch) {
            return { accepted: false, reason: 'stale_epoch' };
        }
        if (!this.sessionOpen) return { accepted: false, reason: 'session_closed' };
        return null;
    }

    private expireCompletedInstances(epoch: number, tick: number): void {
        for (const record of Array.from(this.instances.values())) {
            if (record.phase !== 'active') continue;
            if (record.effectKeys.some((key) => this.effects[key] > 0)) continue;
            record.phase = 'expired';
            record.expiredAtTick = tick;
            this.emit('expired', epoch, tick, 'effects_inactive', undefined, record);
            this.cleanupRecord(record, 'expired', epoch, tick);
        }
    }

    private cleanupInstances(reason: string, epoch: number, tick: number): void {
        for (const record of Array.from(this.instances.values())) {
            this.cleanupRecord(record, reason, epoch, tick);
        }
    }

    private cleanupRecord(record: MutablePowerUpInstance, reason: string, epoch: number, tick: number): void {
        record.phase = 'cleaned';
        record.cleanedAtTick = tick;
        this.emit('cleaned', epoch, tick, reason, undefined, record);
        this.instances.delete(record.id);
    }

    private assertSynchronizedOpenSession(): void {
        this.assertSynchronizedEpoch();
        if (!this.sessionOpen) throw new Error('Power-up session is closed');
    }

    private assertSynchronizedEpoch(): void {
        const currentEpoch = this.readEpoch();
        if (this.activeEpoch !== currentEpoch) {
            throw new Error(`Power-up lifecycle epoch is not synchronized: owner=${this.activeEpoch} injected=${currentEpoch}`);
        }
    }

    private requireKind(type: number): number {
        if (!Number.isSafeInteger(type) || type < 0 || type >= POWER_UP_KIND_COUNT) {
            throw new Error(`Power-up type must be an integer in 0..${POWER_UP_KIND_COUNT - 1}`);
        }
        return type;
    }

    private readEpoch(): number {
        const epoch = this.options.getEpoch();
        if (!Number.isSafeInteger(epoch) || epoch < 0) {
            throw new Error('Injected power-up epoch must be a non-negative safe integer');
        }
        return epoch;
    }

    private readTick(): number {
        const tick = this.options.getTick();
        if (!Number.isSafeInteger(tick) || tick < 0) {
            throw new Error('Injected power-up tick must be a non-negative safe integer');
        }
        return tick;
    }

    private freezeRecord(record: MutablePowerUpInstance): PowerUpInstanceSnapshot {
        return Object.freeze({
            id: record.id,
            type: record.type,
            kind: record.kind,
            epoch: record.epoch,
            phase: record.phase,
            spawnedAtTick: record.spawnedAtTick,
            collectedAtTick: record.collectedAtTick,
            activatedAtTick: record.activatedAtTick,
            expiredAtTick: record.expiredAtTick,
            cleanedAtTick: record.cleanedAtTick,
            effectKeys: Object.freeze(record.effectKeys.slice()),
        });
    }

    private emit(
        action: PowerUpLifecycleAction,
        epoch: number,
        tick: number,
        reason?: string,
        effectKey?: PowerUpEffectKey,
        record?: MutablePowerUpInstance,
    ): void {
        if (!this.options.onEvent) return;
        if (!Number.isSafeInteger(this.nextSequence) || this.nextSequence < 1) {
            throw new Error('Power-up lifecycle event sequence exhausted');
        }
        const event = Object.freeze({
            sequence: this.nextSequence,
            epoch,
            tick,
            action,
            reason,
            effectKey,
            instance: record ? this.freezeRecord(record) : undefined,
        });
        this.nextSequence += 1;
        this.options.onEvent(event);
    }
}
