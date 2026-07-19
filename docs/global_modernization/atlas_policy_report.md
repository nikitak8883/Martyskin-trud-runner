# Atlas policy report — Module 1

Generated: 2026-07-02 15:52 +03:00  
Status: draft policy, no asset movement performed

## Decision

Use curated static atlas contracts for runtime-critical gameplay/UI assets. Dynamic atlas is allowed only for documented, measured, small ephemeral UI fragments.

## Draft atlas groups

| Atlas ID | Usage scope | Source candidates | Dynamic atlas | Fallback policy |
| --- | --- | --- | --- | --- |
| `ui_shared_core` | `hud/menu` | `ui/shared` | false | block release if missing |
| `menu_atomic_buttons` | `menu` | canonical baked-text exceptions under `objectives/themed/last_iteration/ui/main_menu` | false | block release if mixed with runtime duplicate labels |
| `main_menu_background` | `background` | `ui/main_menu_background/main_menu_bg_far.png` | false | block release if replaced by onion layers |
| `player_skins_selected` | `skin` | selected skin subset under `characters/player_skins/<skin_id>` | false | block release in QA; fallback only in production-safe path if explicit |
| `bonus_items` | `bonus` | `objectives/bonuses`, approved `objectives/equipment` mappings | false | block release if missing binding |
| `runner_collectibles` | `runner_core` | `objectives/collectibles` | false | block release |
| `level_theme_pack_<level_family>` | `background/obstacle/platform` | `objectives/themed/last_iteration/<theme>` | false | warn for decorative, block for platform/hazard |
| `achievement_ui` | `hud/menu` | `objectives/ui`, achievement card assets | false | block release for missing icon/card |
| `vfx_ephemeral_small` | `vfx` | future small particles/glows only | limited/explicit | warn if measured |

## Dynamic atlas rule

Dynamic atlas may not be the main strategy for:

- player skins;
- platforms;
- hazards;
- main menu background;
- large UI cards/titles;
- any high-frequency gameplay sprite.

Dynamic atlas may be considered only when all are true:

1. asset is small;
2. asset is non-critical or ephemeral;
3. draw-call reduction is measured;
4. memory growth is measured on Web and Android emulator;
5. fallback does not hide missing runtime bindings.

## Required future manifest fields

Each atlas group should eventually be represented with:

```json
{
  "atlasId": "string",
  "usageScope": "hud|menu|runner_core|skin|bonus|obstacle|background|vfx",
  "bundleId": "string",
  "maxTextureSize": 2048,
  "padding": 2,
  "compression": "platform_specific",
  "dynamicAtlasAllowed": false,
  "owner": "string",
  "fallbackPolicy": "block_release|warn|fallback"
}
```

## Migration order

1. Keep existing paths stable.
2. Add draft manifest and validators.
3. Validate references and `.meta` files.
4. Create contact sheets by atlas group.
5. Move or repack one group only after a report proves no broken references.

## Current blockers to atlas movement

- `objectives/themed` needs sub-classification before packing.
- `GameRoot.ts` still contains direct runtime asset decisions; registry boundaries should be introduced before asset movement.
- Android/Web content manifest version is not formalized yet.

