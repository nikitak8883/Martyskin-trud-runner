import { DevEventLog } from './DevEventLog';
import type { DevEventRecord } from './DevEventTypes';
import { LifecycleEpoch } from './LifecycleEpoch';
import type {
    GameSessionState,
    GameSessionTransitionResult,
} from '../gameplay/state/GameSessionState';

export type { DevEventRecord } from './DevEventTypes';

export const GAME_ROOT_DEV_EVENT_CAPACITY = 128;
export const GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES = 32768;

export type GameRootResetReason =
    | 'boot'
    | 'start_level'
    | 'qa_end_state'
    | 'qa_reset_loop';

export type GameRootEpochInvalidationReason = GameRootResetReason | 'component_destroy';

export interface GameRootDevEventAdapterOptions {
    readonly eventsEnabled: boolean;
    readonly onEvent?: (event: DevEventRecord) => void;
}

/**
 * The single M03.3C observation seam around GameRoot's existing writer.
 *
 * It owns diagnostics and publishes lifecycle epochs, but never owns or mutates
 * GameRoot state or callback scheduling. Release builds still advance epochs
 * for GameRuntimeLifecycleOwner while the bounded event log remains disabled
 * by the caller's DEBUG compile-time flag.
 */
export class GameRootDevEventAdapter {
    private readonly events: DevEventLog;
    private readonly lifecycle = new LifecycleEpoch();
    private readonly onEvent?: (event: DevEventRecord) => void;
    private activeResetEpoch: number | null = null;

    public constructor(options: GameRootDevEventAdapterOptions) {
        this.events = new DevEventLog({
            enabled: options.eventsEnabled,
            capacity: GAME_ROOT_DEV_EVENT_CAPACITY,
            maxExportBytes: GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES,
        });
        this.onEvent = options.eventsEnabled ? options.onEvent : undefined;
    }

    public get eventsEnabled(): boolean {
        return this.events.enabled;
    }

    public currentEpoch(): number {
        return this.lifecycle.current();
    }

    public recordTransition(transition: GameSessionTransitionResult, tick: number): void {
        const result = transition.accepted === false ? transition.code : 'accepted';
        this.append({
            epoch: this.lifecycle.current(),
            tick,
            code: transition.accepted
                ? 'session.transition.accepted'
                : 'session.transition.rejected',
            state: transition.accepted && transition.changed ? transition.to : transition.from,
            reason: transition.reason,
            payload: {
                accepted: transition.accepted,
                changed: transition.changed,
                from: transition.from,
                to: transition.to,
                result,
            },
        });
    }

    public beginReset(state: GameSessionState, reason: GameRootResetReason, tick: number): number {
        if (this.activeResetEpoch !== null) {
            throw new Error('GameRoot reset diagnostics cannot be nested');
        }
        const previousEpoch = this.lifecycle.current();
        const epoch = this.lifecycle.advance();
        this.activeResetEpoch = epoch;
        this.append({
            epoch,
            tick,
            code: 'session.epoch.changed',
            state,
            reason,
            payload: { previousEpoch, currentEpoch: epoch },
        });
        this.append({
            epoch,
            tick,
            code: 'session.reset.begin',
            state,
            reason,
            payload: { previousEpoch },
        });
        return epoch;
    }

    public endReset(epoch: number, state: GameSessionState, reason: GameRootResetReason, tick: number): void {
        if (this.activeResetEpoch !== epoch || !this.lifecycle.isCurrent(epoch)) {
            throw new Error('GameRoot reset diagnostics ended with a stale epoch');
        }
        this.append({
            epoch,
            tick,
            code: 'session.reset.end',
            state,
            reason,
            payload: { currentEpoch: epoch },
        });
        this.activeResetEpoch = null;
    }

    public invalidate(state: GameSessionState, reason: 'component_destroy', tick: number): number {
        const previousEpoch = this.lifecycle.current();
        const epoch = this.lifecycle.advance();
        this.activeResetEpoch = null;
        this.append({
            epoch,
            tick,
            code: 'session.epoch.changed',
            state,
            reason,
            payload: { previousEpoch, currentEpoch: epoch },
        });
        return epoch;
    }

    public snapshot(): readonly DevEventRecord[] {
        return this.events.snapshot();
    }

    public exportJson(
        maxEvents = GAME_ROOT_DEV_EVENT_CAPACITY,
        maxBytes = GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES,
    ): string {
        return this.events.exportJson(maxEvents, maxBytes);
    }

    private append(input: Parameters<DevEventLog['append']>[0]): void {
        const event = this.events.append(input);
        if (!event || !this.onEvent) return;
        try {
            this.onEvent(event);
        } catch {
            // Development telemetry is observational and cannot fail gameplay.
        }
    }
}
