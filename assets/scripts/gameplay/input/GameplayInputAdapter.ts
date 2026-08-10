import type { GameSessionState } from '../state/GameSessionState';

export const GAMEPLAY_INPUT_PAUSE_DEBOUNCE_MS = 220;

export type GameplayInputAction = 'jump' | 'glide' | 'dash' | 'pause';
export type GameplayInputPhase = 'trigger' | 'start' | 'stop';
export type GameplayInputSource =
    | 'keyboard'
    | 'global_touch'
    | 'hud_button'
    | 'pause_zone'
    | 'qa'
    | 'session_reset';

export interface GameplayInputIntent {
    readonly action: GameplayInputAction;
    readonly phase: GameplayInputPhase;
    readonly source: GameplayInputSource;
}

export interface GameplayInputContext extends GameplayInputIntent {
    readonly sessionState: GameSessionState;
    readonly nowMs: number;
}

export interface GameplayPauseInputContext extends GameplayInputContext {
    readonly acceptedCount: number;
}

export type GameplayInputDispatchReason =
    | 'handled'
    | 'invalid_phase'
    | 'invalid_clock'
    | 'session_not_playing'
    | 'pause_debounced';

export interface GameplayInputDispatchResult extends GameplayInputContext {
    readonly accepted: boolean;
    readonly reason: GameplayInputDispatchReason;
    readonly pauseAcceptedCount: number;
}

export interface GameplayInputAdapterOptions {
    readonly getSessionState: () => GameSessionState;
    readonly nowMs: () => number;
    readonly onJump: (context: GameplayInputContext) => void;
    readonly onGlideChanged: (active: boolean, context: GameplayInputContext) => void;
    readonly onDash: (context: GameplayInputContext) => void;
    readonly onPause: (context: GameplayPauseInputContext) => void;
}

/**
 * Pure M03.4 intent seam. Cocos listeners remain owned by GameRoot; this class
 * owns action validation and the single pause-debounce clock only.
 */
export class GameplayInputAdapter {
    private lastAcceptedPauseMs: number | null = null;
    private acceptedPauseCount = 0;

    public constructor(private readonly options: GameplayInputAdapterOptions) {}

    public get pauseAcceptedCount(): number {
        return this.acceptedPauseCount;
    }

    public dispatch(intent: GameplayInputIntent): GameplayInputDispatchResult {
        const sessionState = this.options.getSessionState();
        const nowMs = this.options.nowMs();
        const context: GameplayInputContext = { ...intent, sessionState, nowMs };

        if (!Number.isFinite(nowMs)) return this.result(context, false, 'invalid_clock');
        if (!this.hasValidPhase(intent)) return this.result(context, false, 'invalid_phase');

        switch (intent.action) {
            case 'jump':
                if (sessionState !== 'playing') return this.result(context, false, 'session_not_playing');
                this.options.onJump(context);
                return this.result(context, true, 'handled');
            case 'dash':
                if (sessionState !== 'playing') return this.result(context, false, 'session_not_playing');
                this.options.onDash(context);
                return this.result(context, true, 'handled');
            case 'glide':
                if (intent.phase === 'start' && sessionState !== 'playing') {
                    return this.result(context, false, 'session_not_playing');
                }
                this.options.onGlideChanged(intent.phase === 'start', context);
                return this.result(context, true, 'handled');
            case 'pause':
                if (
                    this.lastAcceptedPauseMs !== null
                    && nowMs - this.lastAcceptedPauseMs < GAMEPLAY_INPUT_PAUSE_DEBOUNCE_MS
                ) {
                    return this.result(context, false, 'pause_debounced');
                }
                this.lastAcceptedPauseMs = nowMs;
                this.acceptedPauseCount += 1;
                this.options.onPause({ ...context, acceptedCount: this.acceptedPauseCount });
                return this.result(context, true, 'handled');
        }
    }

    public releaseGlide(source: 'global_touch' | 'keyboard' | 'session_reset'): GameplayInputDispatchResult {
        return this.dispatch({ action: 'glide', phase: 'stop', source });
    }

    private hasValidPhase(intent: GameplayInputIntent): boolean {
        return intent.action === 'glide'
            ? intent.phase === 'start' || intent.phase === 'stop'
            : intent.phase === 'trigger';
    }

    private result(
        context: GameplayInputContext,
        accepted: boolean,
        reason: GameplayInputDispatchReason,
    ): GameplayInputDispatchResult {
        return {
            ...context,
            accepted,
            reason,
            pauseAcceptedCount: this.acceptedPauseCount,
        };
    }
}
