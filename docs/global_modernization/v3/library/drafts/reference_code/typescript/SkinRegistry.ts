export type SkinId = string; export type AnimationId = string; export type BonusId = string;
export interface SkinFrameSet { base: Record<AnimationId, readonly string[]>; bonus: Record<BonusId, Record<AnimationId, readonly string[]>>; }
export interface SkinDefinition { skinId: SkinId; displayName: string; bundleId: string; frames: SkinFrameSet; fallbackPolicy: 'fail_visible_in_dev'|'base_frame_with_warning'|'forbidden'; }
export class SkinRegistry {
  private readonly skins = new Map<SkinId,SkinDefinition>();
  register(def: SkinDefinition): void { if(this.skins.has(def.skinId)) throw new Error(`Duplicate skin: ${def.skinId}`); this.skins.set(def.skinId,def); }
  require(id: SkinId): SkinDefinition { const x=this.skins.get(id); if(!x) throw new Error(`Unknown skin: ${id}`); return x; }
}
