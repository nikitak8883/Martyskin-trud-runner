# Skin asset inventory — 2026-06-21 patch pass

## Scope

Source task: `C:\Projects\Monkey Work\Tasks\3\MTR_LATEST_UPDATE_AUDIT_AND_FIX_TZ_2026-06-21.zip`.

Runtime asset root:

```text
assets/resources/characters/player_skins
```

## Current baked coverage

The current runtime asset set contains complete baked PNG animation frames for the eight canonical player skins:

- `brigadir`
- `mudrec`
- `cyber_makaka`
- `red_prorab`
- `depo_primate`
- `orangutan_noir`
- `lab_assistant_act`
- `golden_brigadir`

For each skin, the following baked variants are present with all 9 runtime poses:

- `base`
- `helmet`
- `vest`
- `helmet_vest`
- `boots`
- `helmet_vest_boots`
- `magnet`
- `shield`

Runtime poses checked:

- `idle`
- `run_1`
- `run_2`
- `jump`
- `jump_2`
- `fall`
- `crouch_dash`
- `hit`
- `victory`

This equals `8 skins × 8 variants × 9 poses = 576` baked gameplay PNG frames, plus preview/headshot assets.

## Dedicated variants not present yet

The latest audit requested explicit dedicated variants for:

- `blueprint`
- `radio`
- `banana_boost`
- `key_pass`
- `coffee`
- `full_safety`

No separate baked PNG folders for those variants are present in the current asset tree. The patch therefore does not invent generic overlays. It maps these cases through the manifest/resolver to the nearest safe baked variant or to `base`, with a warning path for missing future dedicated frames.

## Patch policy

Runtime clothing/key-item overlays on the player are forbidden unless they are soft VFX:

- allowed: aura, magnet field, short dash trails, hit/readability/debug effects;
- forbidden: generic helmet/vest/clipboard/pass/coffee/magnet model drawn over the player fallback.

