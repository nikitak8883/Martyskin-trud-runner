import type { GameSessionState } from '../state/GameSessionState';

export type GameplayUiIntent =
    | { readonly action: 'navigate'; readonly next: GameSessionState; readonly reason: string }
    | { readonly action: 'start_level'; readonly levelIndex: number }
    | { readonly action: 'preview_skin'; readonly skinIndex: number }
    | { readonly action: 'confirm_skin' }
    | { readonly action: 'open_developer_gate' }
    | { readonly action: 'submit_developer_gate' };

export type GameplayUiIntentReason =
    | 'handled'
    | 'transition_rejected'
    | 'invalid_level_index'
    | 'invalid_skin_index'
    | 'invalid_source_state';

export interface GameplayUiIntentResult {
    readonly accepted: boolean;
    readonly action: GameplayUiIntent['action'];
    readonly sourceState: GameSessionState;
    readonly reason: GameplayUiIntentReason;
}

export interface GameplayUiIntentAdapterOptions {
    readonly getSessionState: () => GameSessionState;
    readonly getLevelCount: () => number;
    readonly getSkinCount: () => number;
    readonly onNavigate: (next: GameSessionState, reason: string) => boolean;
    readonly onStartLevel: (levelIndex: number) => void;
    readonly onPreviewSkin: (skinIndex: number) => void;
    readonly onConfirmSkin: () => void;
    readonly onOpenDeveloperGate: () => void;
    readonly onSubmitDeveloperGate: () => void;
}

/**
 * M03.7A ownership seam. Immediate-mode UI emits typed intents; existing
 * GameRoot mutation methods remain the sole legacy bridge until M03.7B.
 */
export class GameplayUiIntentAdapter {
    public constructor(private readonly options: GameplayUiIntentAdapterOptions) {}

    public dispatch(intent: GameplayUiIntent): GameplayUiIntentResult {
        const sourceState = this.options.getSessionState();
        switch (intent.action) {
            case 'navigate':
                if (!this.options.onNavigate(intent.next, intent.reason)) {
                    return this.result(intent.action, sourceState, false, 'transition_rejected');
                }
                return this.result(intent.action, sourceState, true, 'handled');
            case 'start_level':
                if (!this.validIndex(intent.levelIndex, this.options.getLevelCount())) {
                    return this.result(intent.action, sourceState, false, 'invalid_level_index');
                }
                this.options.onStartLevel(intent.levelIndex);
                return this.result(intent.action, sourceState, true, 'handled');
            case 'preview_skin':
                if (sourceState !== 'skins') {
                    return this.result(intent.action, sourceState, false, 'invalid_source_state');
                }
                if (!this.validIndex(intent.skinIndex, this.options.getSkinCount())) {
                    return this.result(intent.action, sourceState, false, 'invalid_skin_index');
                }
                this.options.onPreviewSkin(intent.skinIndex);
                return this.result(intent.action, sourceState, true, 'handled');
            case 'confirm_skin':
                if (sourceState !== 'skins') {
                    return this.result(intent.action, sourceState, false, 'invalid_source_state');
                }
                this.options.onConfirmSkin();
                return this.result(intent.action, sourceState, true, 'handled');
            case 'open_developer_gate':
                if (sourceState !== 'menu') {
                    return this.result(intent.action, sourceState, false, 'invalid_source_state');
                }
                this.options.onOpenDeveloperGate();
                return this.result(intent.action, sourceState, true, 'handled');
            case 'submit_developer_gate':
                if (sourceState !== 'devgate') {
                    return this.result(intent.action, sourceState, false, 'invalid_source_state');
                }
                this.options.onSubmitDeveloperGate();
                return this.result(intent.action, sourceState, true, 'handled');
        }
    }

    private validIndex(value: number, count: number): boolean {
        return Number.isInteger(value) && Number.isInteger(count) && count > 0 && value >= 0 && value < count;
    }

    private result(
        action: GameplayUiIntent['action'],
        sourceState: GameSessionState,
        accepted: boolean,
        reason: GameplayUiIntentReason,
    ): GameplayUiIntentResult {
        return Object.freeze({ accepted, action, sourceState, reason });
    }
}
