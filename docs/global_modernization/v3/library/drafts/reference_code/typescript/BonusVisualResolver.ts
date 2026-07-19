import type { SkinRegistry, SkinId, AnimationId, BonusId } from './SkinRegistry';
export interface ResolveRequest { skinId: SkinId; animationId: AnimationId; frameIndex: number; bonusId?: BonusId; devMode: boolean; }
export interface ResolveResult { framePath: string; usedFallback: boolean; warning?: string; }
export class BonusVisualResolver {
  constructor(private readonly registry: SkinRegistry) {}
  resolve(r: ResolveRequest): ResolveResult {
    const skin=this.registry.require(r.skinId); const bonus=r.bonusId ? skin.frames.bonus[r.bonusId]?.[r.animationId] : undefined;
    if(bonus?.length) return {framePath:bonus[r.frameIndex % bonus.length],usedFallback:false};
    const base=skin.frames.base[r.animationId];
    if(!base?.length) throw new Error(`Missing base animation ${r.skinId}/${r.animationId}`);
    if(r.bonusId && skin.fallbackPolicy==='forbidden') throw new Error(`Missing baked bonus ${r.skinId}/${r.bonusId}/${r.animationId}`);
    const warning=r.bonusId ? `Missing baked bonus frame: ${r.skinId}/${r.bonusId}/${r.animationId}` : undefined;
    return {framePath:base[r.frameIndex % base.length],usedFallback:Boolean(r.bonusId),warning:r.devMode?warning:undefined};
  }
}
