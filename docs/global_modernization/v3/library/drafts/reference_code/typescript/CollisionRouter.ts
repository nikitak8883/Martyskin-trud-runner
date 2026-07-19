export type CollisionKind = 'pickup' | 'obstacle' | 'platform' | 'trigger' | 'finish';
export interface CollisionEvent { kind: CollisionKind; entityId: string; otherId?: string; atMs: number; payload?: unknown; }
export type CollisionHandler = (event: CollisionEvent) => void;
export class CollisionRouter {
  private readonly handlers = new Map<CollisionKind, Set<CollisionHandler>>();
  on(kind: CollisionKind, handler: CollisionHandler): () => void {
    const set = this.handlers.get(kind) ?? new Set<CollisionHandler>(); set.add(handler); this.handlers.set(kind, set);
    return () => set.delete(handler);
  }
  route(event: CollisionEvent): void { for (const handler of this.handlers.get(event.kind) ?? []) handler(event); }
  clear(): void { this.handlers.clear(); }
}
