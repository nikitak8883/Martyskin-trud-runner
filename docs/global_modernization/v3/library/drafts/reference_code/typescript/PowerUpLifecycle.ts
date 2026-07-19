export type PowerUpPhase = 'spawned' | 'collected' | 'active' | 'expired' | 'cleaned';
export interface PowerUpInstance { id: string; type: string; phase: PowerUpPhase; startedAtMs?: number; expiresAtMs?: number; }
export interface PowerUpHooks { activate(x: PowerUpInstance): void; expire(x: PowerUpInstance): void; cleanup(x: PowerUpInstance): void; }
export class PowerUpLifecycle {
  private readonly active = new Map<string, PowerUpInstance>();
  constructor(private readonly hooks: PowerUpHooks) {}
  activate(x: PowerUpInstance, nowMs: number, durationMs?: number): void {
    x.phase='active'; x.startedAtMs=nowMs; x.expiresAtMs=durationMs == null ? undefined : nowMs+durationMs; this.active.set(x.id,x); this.hooks.activate(x);
  }
  tick(nowMs: number): void { for (const x of this.active.values()) if (x.expiresAtMs != null && nowMs >= x.expiresAtMs) this.expire(x.id); }
  expire(id: string): void { const x=this.active.get(id); if(!x) return; x.phase='expired'; this.hooks.expire(x); this.cleanup(id); }
  cleanup(id: string): void { const x=this.active.get(id); if(!x) return; x.phase='cleaned'; this.hooks.cleanup(x); this.active.delete(id); }
  cleanupAll(): void { for (const id of [...this.active.keys()]) this.cleanup(id); }
}
