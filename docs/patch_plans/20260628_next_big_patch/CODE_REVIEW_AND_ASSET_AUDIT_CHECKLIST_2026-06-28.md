# Code-review and asset-audit checklist — next big patch

Status: planning scaffold only.

## Code-review checklist

### Runtime/state

- [ ] `GameRoot.ts` state transitions are explicit and reversible.
- [ ] Runtime input nodes are active only in the state that owns them.
- [ ] Name input is not based on browser-only `prompt()`.
- [ ] Android soft keyboard behavior is tested.
- [ ] Web keyboard behavior is tested.
- [ ] `mtr_player_name` save/load has safe fallback.
- [ ] Records and achievements are linked to the normalized custom name.
- [ ] UI labels do not leave old text behind PNG surfaces.

### Skins

- [ ] All active skin IDs are documented.
- [ ] All variants and poses are inventoried.
- [ ] Missing sprite keys are reported before fixing.
- [ ] No legacy namespace is used as an active runtime source.
- [ ] Bonus-state variant switching has no visible fallback in final QA.
- [ ] Contact sheets exist for visual review.

### Platforms

- [ ] Platform keys per level are inventoried.
- [ ] Each referenced platform PNG exists.
- [ ] Platform render size matches collision surface.
- [ ] No fallback placeholder leaks into normal gameplay.
- [ ] Platform art belongs to the level theme.

### Config/build parity

- [ ] Android and Web share `assets/resources/config/*`.
- [ ] `levels.json` has 15 levels.
- [ ] Web build and Android emulator build are both generated from the same source state.
- [ ] Device-valid release APK is built separately from emulator QA APK.

## Asset audit checklist

### Alpha/cutout defects

- [ ] Edge-connected white/near-white matte scan.
- [ ] Alpha histogram for every suspect PNG.
- [ ] Contact sheet before repair.
- [ ] Contact sheet after repair.
- [ ] Intentional white elements protected.
- [ ] Canvas size, scale, and anchor consistency checked.

### Skin matrix

| Skin | Base poses | Bonus variants | White matte defects | Anchor/scale defects | Action |
| --- | --- | --- | --- | --- | --- |
| brigadir |  |  |  |  |  |
| mudrec |  |  |  |  |  |
| cyber_makaka |  |  |  |  |  |
| red_prorab |  |  |  |  |  |
| depo_primate |  |  |  |  |  |
| orangutan_noir |  |  |  |  |  |
| lab_assistant_act |  |  |  |  |  |
| golden_brigadir |  |  |  |  |  |

### Platform matrix

| Level | Expected platform theme | Missing assets | White matte defects | Wrong texture defects | Action |
| --- | --- | --- | --- | --- | --- |
| 1 | construction scaffolds/planks/blocks |  |  |  |  |
| 2 | logistics pallets/crates/conveyors |  |  |  |  |
| 3 | office/bureaucracy supports |  |  |  |  |
| 4 | jungle bridges/vines/wood |  |  |  |  |
| 5 | farm supports/carts/fences |  |  |  |  |
| 6 | inspection stands/peacock bureau props |  |  |  |  |
| 7 | factory beams/catwalks/pipes |  |  |  |  |
| 8 | archive shelves/cabinets/paper stacks |  |  |  |  |
| 9 | reactor platforms/pipes/safety rails |  |  |  |  |
| 10 | audit corridor barriers/checkpoints |  |  |  |  |
| 11 | night shift scaffolds/light rigs |  |  |  |  |
| 12 | training department desks/boards |  |  |  |  |
| 13 | tower catwalks/elevator supports |  |  |  |  |
| 14 | ministry/factory regulatory platforms |  |  |  |  |
| 15 | final mechanism gears/bridges |  |  |  |  |

## Suggested future helper tools

These are not implemented in this planning stage.

- `tools/asset_audit/audit_png_alpha_white_matte.py`
- `tools/asset_audit/make_skin_contact_sheets.py`
- `tools/qa/capture_all_levels_web.mjs`
- `tools/qa/capture_all_levels_android.ps1`
- `tools/qa/scan_runtime_logs_for_asset_fallbacks.ps1`

