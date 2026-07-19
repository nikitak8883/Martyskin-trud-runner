/** Pure TypeScript reference seam. Adapt to the project; do not paste blindly. */
export type GameSessionState =
  | 'menu' | 'loading' | 'countdown' | 'playing' | 'paused' | 'failed' | 'completed';

export interface SessionTransition {
  from: GameSessionState;
  event: string;
  to: GameSessionState;
  reason?: string;
  atMs: number;
}

export class GameSessionStateMachine {
  private state: GameSessionState = 'menu';
  private readonly log: SessionTransition[] = [];
  constructor(private readonly maxLogEntries = 256) {}
  get current(): GameSessionState { return this.state; }
  transition(event: string, to: GameSessionState, reason?: string): void {
    const entry = { from: this.state, event, to, reason, atMs: Date.now() } satisfies SessionTransition;
    this.state = to; this.log.push(entry);
    if (this.log.length > this.maxLogEntries) this.log.splice(0, this.log.length - this.maxLogEntries);
  }
  snapshot(): readonly SessionTransition[] { return [...this.log]; }
}
