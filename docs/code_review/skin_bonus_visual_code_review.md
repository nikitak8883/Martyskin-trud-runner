# Skin / bonus visual code review — 2026-06-21

## Scope

Reviewed files:

- `assets/scripts/GameRoot.ts`
- `assets/resources/config/player_skin_equipment_matrix.json`
- `assets/resources/config/bonus_visual_states.json`
- `assets/resources/characters/player_skins/**`

## Findings

### P0 — legacy fallback could reintroduce player equipment overlays

`drawMonkey()` correctly prefers baked skin PNG frames through `drawPlayerSkinSprite()`. However, if the baked sprite path fails completely, the legacy primitive fallback path still drew active helmet/vest/blueprint/pass/coffee/boots/magnet items directly over the player. That contradicted the latest baked-variant policy and could create the large wrong-item/rectangle visual seen in gameplay recordings.

Status: fixed.

### P0 — resolver priority preferred some equipment over shield/magnet

`resolvePlayerSkinVariant()` prioritized `vest`, `helmet`, and `boots` before `shield` and `magnet`. This could hide the active high-priority baked effect variant behind a lower-priority safety item.

Status: fixed. Priority is now:

```text
helmet_vest_boots -> helmet_vest -> shield -> magnet -> vest -> helmet -> boots -> base
```

### P1 — manifest did not document requested-but-unbaked variants

The matrix listed only implemented baked variants. It did not explicitly record that `blueprint`, `radio`, `banana_boost`, `key_pass`, `coffee`, and `full_safety` are requested logical bonuses but do not yet have dedicated PNG folders.

Status: fixed in `player_skin_equipment_matrix.json`.

## Safe fixes applied

- Suppressed legacy player equipment overlays in the no-sprite fallback path.
- Kept allowed runtime VFX only: shield aura, magnet field, dash trail/debug indicators.
- Updated resolver priority to match the baked-variant policy.
- Updated manifest policy with `requestedBonusIds`, `bakedVariants`, `resolverPriority`, `unbakedBonusFallbacks`, `runtimeVfxOnly`, and stricter forbidden fallbacks.

## Remaining risks

- Dedicated PNG frames for `blueprint`, `radio`, `key_pass`, and `coffee` are still absent. The current patch makes that safe but does not create new artwork.
- Full visual confidence still requires Android emulator QA plus web smoke QA after rebuild.

