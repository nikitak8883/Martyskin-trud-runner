# Избранные исходные фрагменты

Эти excerpts — минимальный source subset для внешней оценки M03.2. Полный `GameRoot.ts` (5,434 строки) намеренно не включён: его хеш, карта ответственности и точный location приведены в остальных документах.

## `GameSessionState.ts` — полный M03.2 contract

```ts
export const GAME_SESSION_STATES = Object.freeze([
    'menu',
    'playing',
    'paused',
    'clear',
    'over',
    'finished',
    'skins',
    'levels',
    'sound',
    'records',
    'achievements',
    'name',
    'devgate',
    'devpanel',
] as const);

export type GameSessionState = typeof GAME_SESSION_STATES[number];

export type GameSessionMode =
    | 'MENU'
    | 'CHARACTER_SELECT'
    | 'LEVEL_SELECT'
    | 'RUNNING'
    | 'PAUSED'
    | 'GAME_OVER'
    | 'ACHIEVEMENTS'
    | 'DEV_MODE';

interface GameSessionTransitionBase {
    readonly from: GameSessionState;
    readonly to: GameSessionState;
    readonly reason: string;
    readonly changed: boolean;
}

export interface AcceptedGameSessionTransition extends GameSessionTransitionBase {
    readonly accepted: true;
}

export interface RejectedGameSessionTransition extends GameSessionTransitionBase {
    readonly accepted: false;
    readonly changed: false;
    readonly code: 'invalid_transition';
}

export type GameSessionTransitionResult =
    | AcceptedGameSessionTransition
    | RejectedGameSessionTransition;

function frozenTargets(...states: GameSessionState[]): readonly GameSessionState[] {
    return Object.freeze(states.slice());
}

export const GAME_SESSION_TRANSITION_TARGETS: Readonly<Record<GameSessionState, readonly GameSessionState[]>> =
    Object.freeze({
        menu: frozenTargets('playing', 'clear', 'over', 'finished', 'skins', 'levels', 'sound', 'records', 'achievements', 'name', 'devgate', 'devpanel'),
        playing: frozenTargets('paused', 'clear', 'over', 'finished'),
        paused: frozenTargets('playing', 'sound', 'menu'),
        clear: frozenTargets('playing', 'menu'),
        over: frozenTargets('playing', 'menu'),
        finished: frozenTargets('playing', 'records'),
        skins: frozenTargets('playing', 'menu'),
        levels: frozenTargets('playing', 'menu'),
        sound: frozenTargets('playing', 'menu'),
        records: frozenTargets('playing', 'achievements', 'menu'),
        achievements: frozenTargets('playing', 'records', 'menu'),
        name: frozenTargets('playing', 'menu'),
        devgate: frozenTargets('playing', 'devpanel', 'menu'),
        devpanel: frozenTargets('playing', 'menu'),
    });

const GAME_SESSION_MODE_BY_STATE: Readonly<Record<GameSessionState, GameSessionMode>> =
    Object.freeze({
        menu: 'MENU',
        playing: 'RUNNING',
        paused: 'PAUSED',
        clear: 'RUNNING',
        over: 'GAME_OVER',
        finished: 'RUNNING',
        skins: 'CHARACTER_SELECT',
        levels: 'LEVEL_SELECT',
        sound: 'PAUSED',
        records: 'ACHIEVEMENTS',
        achievements: 'ACHIEVEMENTS',
        name: 'CHARACTER_SELECT',
        devgate: 'DEV_MODE',
        devpanel: 'DEV_MODE',
    });

export function gameSessionModeForState(state: GameSessionState): GameSessionMode {
    return GAME_SESSION_MODE_BY_STATE[state];
}

export function isGameSessionTransitionAllowed(from: GameSessionState, to: GameSessionState): boolean {
    return from === to || GAME_SESSION_TRANSITION_TARGETS[from].indexOf(to) >= 0;
}

export function evaluateGameSessionTransition(
    from: GameSessionState,
    to: GameSessionState,
    reason = 'runtime',
): GameSessionTransitionResult {
    if (!isGameSessionTransitionAllowed(from, to)) {
        return {
            accepted: false,
            changed: false,
            code: 'invalid_transition',
            from,
            to,
            reason,
        };
    }
    return {
        accepted: true,
        changed: from !== to,
        from,
        to,
        reason,
    };
}
```

## `GameRoot.transitionTo` — sole mutable writer adapter

```ts
private transitionTo(next: State, reason = 'runtime'): GameSessionTransitionResult {
    const prev = this.state;
    const transition = evaluateGameSessionTransition(prev, next, reason);
    if (transition.accepted === false) {
        this.syncGameState();
        console.warn(`MTR_FSM_REJECT code=${transition.code} state=${prev}->${next} reason=${reason}`);
        return transition;
    }
    if (!transition.changed) {
        this.syncGameState();
        return transition;
    }
    if (prev === 'name' && next !== 'name') this.commitPlayerNameFromInput(false);
    const prevMode = this.modeForState(prev);
    const nextMode = this.modeForState(next);
    if (next === 'skins') this.pendingSkinSelection = this.selectedSkin;
    this.state = next;
    if (next === 'name') this.syncPlayerNameEditString();
    this.syncGameState();
    console.log(`MTR_FSM:${prevMode}->${nextMode} state=${prev}->${next} reason=${reason}`);
    return transition;
}
```

## Review cues

- Does the transition table preserve required state edges without introducing accidental broad states?
- Is `console.warn` on rejected edges acceptable for development logs, given M03.3 owns bounded event logging and release silence?
- Does M03.3 need a lifecycle token before recording delayed events?
- Should the asynchronous non-playing → `playing` compatibility policy be kept until lifecycle ownership is explicit?
