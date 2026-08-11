export const GAMEPLAY_COLLISION_KINDS = Object.freeze([
    'platform_land',
    'ground_clamp',
    'collectible_pickup',
    'bonus_pickup',
    'obstacle_hit',
    'npc_stomp',
    'npc_hit',
    'level_finish',
] as const);

export type GameplayCollisionKind = typeof GAMEPLAY_COLLISION_KINDS[number];
export type GameplayCollectibleKind = 'banana' | 'coconut' | 'figLeaf';
export type GameplayFinishState = 'clear' | 'over' | 'finished';

interface GameplayCollisionIntentBase<TKind extends GameplayCollisionKind, TPayload> {
    readonly kind: TKind;
    readonly entityId: string;
    readonly otherId: 'player';
    readonly payload: Readonly<TPayload>;
}

export type GameplayCollisionIntent =
    | GameplayCollisionIntentBase<'platform_land', { platformIndex: number; targetY: number }>
    | GameplayCollisionIntentBase<'ground_clamp', { targetY: number }>
    | GameplayCollisionIntentBase<'collectible_pickup', {
        collectibleIndex: number;
        collectibleKind: GameplayCollectibleKind;
        screenX: number;
        worldY: number;
    }>
    | GameplayCollisionIntentBase<'bonus_pickup', {
        bonusIndex: number;
        bonusType: number;
        screenX: number;
        worldY: number;
    }>
    | GameplayCollisionIntentBase<'obstacle_hit', {
        obstacleIndex: number;
        obstacleType: number;
        screenX: number;
        worldY: number;
    }>
    | GameplayCollisionIntentBase<'npc_stomp', { npcIndex: number; screenX: number }>
    | GameplayCollisionIntentBase<'npc_hit', { npcIndex: number; screenX: number; worldY: number }>
    | GameplayCollisionIntentBase<'level_finish', {
        levelIndex: number;
        nextState: GameplayFinishState;
    }>;

export type GameplayCollisionEvent = GameplayCollisionIntent & {
    readonly sequence: number;
    readonly epoch: number;
    readonly tick: number;
};

export interface GameplayCollisionRouterOptions {
    readonly getEpoch: () => number;
    readonly getTick: () => number;
    readonly onEvent: (event: GameplayCollisionEvent) => void;
}

const GAMEPLAY_COLLISION_KIND_SET: ReadonlySet<string> = new Set(GAMEPLAY_COLLISION_KINDS);

/**
 * Pure M03.5 synchronous routing seam. Detection and side effects remain in
 * GameRoot. This router never sorts, batches, retries or stores entity state.
 */
export class GameplayCollisionRouter {
    private nextSequence = 1;
    private dispatching = false;

    public constructor(private readonly options: GameplayCollisionRouterOptions) {}

    public route(intent: GameplayCollisionIntent): GameplayCollisionEvent {
        if (this.dispatching) throw new Error('GameplayCollisionRouter does not allow reentrant routing');
        if (!GAMEPLAY_COLLISION_KIND_SET.has(intent.kind)) {
            throw new Error(`Unknown gameplay collision kind: ${String(intent.kind)}`);
        }
        if (!intent.entityId.trim()) throw new Error('Gameplay collision entityId must be non-empty');
        if (intent.otherId !== 'player') throw new Error('Gameplay collision otherId must be player');

        const epoch = this.options.getEpoch();
        const tick = this.options.getTick();
        if (!Number.isSafeInteger(epoch) || epoch < 0) {
            throw new Error('Gameplay collision epoch must be a non-negative safe integer');
        }
        if (!Number.isSafeInteger(tick) || tick < 0) {
            throw new Error('Gameplay collision tick must be a non-negative safe integer');
        }
        if (!Number.isSafeInteger(this.nextSequence) || this.nextSequence < 1) {
            throw new Error('Gameplay collision sequence exhausted');
        }

        const payload = Object.freeze({ ...intent.payload });
        const event = Object.freeze({
            ...intent,
            payload,
            sequence: this.nextSequence,
            epoch,
            tick,
        }) as GameplayCollisionEvent;
        this.nextSequence += 1;

        this.dispatching = true;
        try {
            this.options.onEvent(event);
        } finally {
            this.dispatching = false;
        }
        return event;
    }
}
