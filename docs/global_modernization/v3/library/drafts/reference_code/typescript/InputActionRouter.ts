export type InputAction = 'jump' | 'glide' | 'dash' | 'pause';
export interface InputContext { sessionState: string; playerState: string; nowMs: number; }
export interface InputHandler { canHandle(action: InputAction, ctx: InputContext): boolean; handle(action: InputAction, ctx: InputContext): void; }
export class InputActionRouter {
  constructor(private readonly handlers: readonly InputHandler[]) {}
  dispatch(action: InputAction, ctx: InputContext): boolean {
    const handler = this.handlers.find(h => h.canHandle(action, ctx));
    if (!handler) return false;
    handler.handle(action, ctx); return true;
  }
}
