export type GameRuntimeCallbackScope = 'component' | 'session';
export type GameRuntimeLifecycleEventCode =
    | 'callback.scheduled'
    | 'callback.executed'
    | 'callback.cancelled'
    | 'callback.stale'
    | 'listener.registered'
    | 'listener.unregistered'
    | 'owner.destroyed';

export interface GameRuntimeLifecycleEvent {
    readonly code: GameRuntimeLifecycleEventCode;
    readonly key: string;
    readonly scope: GameRuntimeCallbackScope | 'listener' | 'owner';
    readonly epoch: number;
    readonly reason: string;
}

export interface GameRuntimeLifecycleSnapshot {
    readonly destroyed: boolean;
    readonly epoch: number;
    readonly componentCallbacks: number;
    readonly sessionCallbacks: number;
    readonly listeners: number;
}

export interface GameRuntimeLifecycleOwnerOptions {
    readonly getEpoch: () => number;
    readonly scheduleOnce: (callback: () => void, delaySeconds: number) => void;
    readonly unschedule: (callback: () => void) => void;
    readonly onEvent?: (event: GameRuntimeLifecycleEvent) => void;
}

interface PendingCallback {
    readonly key: string;
    readonly scope: GameRuntimeCallbackScope;
    readonly epoch: number;
    readonly wrapped: () => void;
}

interface OwnedListener {
    readonly key: string;
    readonly unsubscribe: () => void;
}

/**
 * Pure M03.7A owner for Cocos one-shot callbacks and listener cleanup.
 * Scheduling and unsubscription are injected so this contract stays directly
 * testable without importing the engine.
 */
export class GameRuntimeLifecycleOwner {
    private readonly pending = new Set<PendingCallback>();
    private readonly listeners = new Map<string, OwnedListener>();
    private destroyed = false;

    public constructor(private readonly options: GameRuntimeLifecycleOwnerOptions) {}

    public scheduleOnce(
        key: string,
        scope: GameRuntimeCallbackScope,
        callback: () => void,
        delaySeconds: number,
    ): void {
        this.assertActive();
        if (!key.trim()) throw new Error('Lifecycle callback key cannot be empty');
        if (!Number.isFinite(delaySeconds) || delaySeconds < 0) {
            throw new Error('Lifecycle callback delay must be finite and non-negative');
        }
        const epoch = this.options.getEpoch();
        let entry: PendingCallback;
        const wrapped = () => {
            this.pending.delete(entry);
            if (this.destroyed) return;
            if (scope === 'session' && epoch !== this.options.getEpoch()) {
                this.emit('callback.stale', key, scope, epoch, 'epoch_changed');
                return;
            }
            this.emit('callback.executed', key, scope, epoch, 'elapsed');
            callback();
        };
        entry = { key, scope, epoch, wrapped };
        this.pending.add(entry);
        try {
            this.options.scheduleOnce(wrapped, delaySeconds);
        } catch (error) {
            this.pending.delete(entry);
            throw error;
        }
        this.emit('callback.scheduled', key, scope, epoch, 'scheduled');
    }

    public registerListener(key: string, subscribe: () => void, unsubscribe: () => void): void {
        this.assertActive();
        if (!key.trim()) throw new Error('Lifecycle listener key cannot be empty');
        if (this.listeners.has(key)) throw new Error(`Lifecycle listener already registered: ${key}`);
        subscribe();
        this.listeners.set(key, { key, unsubscribe });
        this.emit('listener.registered', key, 'listener', this.options.getEpoch(), 'registered');
    }

    public cancelSession(reason: string): number {
        return this.cancelCallbacks('session', reason);
    }

    public destroy(reason: string): GameRuntimeLifecycleSnapshot {
        if (this.destroyed) return this.snapshot();
        this.cancelCallbacks(undefined, reason);
        for (const listener of Array.from(this.listeners.values()).reverse()) {
            try {
                listener.unsubscribe();
            } finally {
                this.listeners.delete(listener.key);
                this.emit('listener.unregistered', listener.key, 'listener', this.options.getEpoch(), reason);
            }
        }
        this.destroyed = true;
        this.emit('owner.destroyed', 'runtime', 'owner', this.options.getEpoch(), reason);
        return this.snapshot();
    }

    public snapshot(): GameRuntimeLifecycleSnapshot {
        let componentCallbacks = 0;
        let sessionCallbacks = 0;
        for (const entry of this.pending) {
            if (entry.scope === 'component') componentCallbacks++;
            else sessionCallbacks++;
        }
        return Object.freeze({
            destroyed: this.destroyed,
            epoch: this.options.getEpoch(),
            componentCallbacks,
            sessionCallbacks,
            listeners: this.listeners.size,
        });
    }

    private cancelCallbacks(scope: GameRuntimeCallbackScope | undefined, reason: string): number {
        let cancelled = 0;
        for (const entry of Array.from(this.pending)) {
            if (scope && entry.scope !== scope) continue;
            this.pending.delete(entry);
            this.options.unschedule(entry.wrapped);
            cancelled++;
            this.emit('callback.cancelled', entry.key, entry.scope, entry.epoch, reason);
        }
        return cancelled;
    }

    private assertActive(): void {
        if (this.destroyed) throw new Error('Lifecycle owner is destroyed');
    }

    private emit(
        code: GameRuntimeLifecycleEventCode,
        key: string,
        scope: GameRuntimeCallbackScope | 'listener' | 'owner',
        epoch: number,
        reason: string,
    ): void {
        if (!this.options.onEvent) return;
        this.options.onEvent(Object.freeze({ code, key, scope, epoch, reason }));
    }
}
