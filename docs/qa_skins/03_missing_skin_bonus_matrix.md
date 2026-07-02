# Missing skin bonus matrix — 2026-06-21

## Summary

The runtime has full baked coverage for the variants that currently exist on disk:

```text
base, helmet, vest, helmet_vest, boots, helmet_vest_boots, magnet, shield
```

The latest audit requests additional logical bonus IDs:

```text
blueprint, radio, banana_boost, key_pass, coffee, full_safety
```

Those dedicated PNG folders do not exist yet for any of the 8 skins. The safe release behavior for this patch is therefore:

| requested bonus/loadout | current safe rendering | reason |
| --- | --- | --- |
| `blueprint` | `base` | no skin-specific baked blueprint PNG frames |
| `radio` | `base` | no skin-specific baked radio PNG frames |
| `banana_boost` | `boots` | movement boost can use existing baked boots/loadout frames |
| `key_pass` | `base` | no skin-specific baked key/pass PNG frames |
| `coffee` | `boots` | coffee activates movement boost and can use existing baked boots/loadout frames |
| `full_safety` | `helmet_vest_boots` | existing canonical full safety equivalent |

## Required future generation

If dedicated visuals are still required, generate skin-specific baked frames instead of runtime overlays:

```text
<skin_id>/bonus/blueprint/<pose>.png
<skin_id>/bonus/radio/<pose>.png
<skin_id>/bonus/banana_boost/<pose>.png
<skin_id>/bonus/key_pass/<pose>.png
<skin_id>/bonus/coffee/<pose>.png
<skin_id>/bonus/full_safety/<pose>.png
```

Minimum pose subset for the next PNG generation pass:

- `idle`
- `run_1`
- `run_2`
- `jump`
- `crouch_dash`
- `hit`

## Current acceptance gate

The current patch is acceptable only if:

- existing baked variants continue to render;
- missing dedicated variants do not create generic item overlays;
- fallback returns to selected skin/base or an existing baked movement/safety variant;
- logs make missing dedicated variants visible for future asset work.

