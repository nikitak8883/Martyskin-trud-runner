# PNG alpha validation

- Decoded files: `14`
- Files with risk flags: `12`
- Quarantine candidates JSON: `C:\Projects\Monkey Work\MTRCocosCreator_portable_transfer_20260617\MTRCocosCreator\assets\resources\characters\player_skins\_shared\manifests\quarantine_candidates.json`

| group | file | alpha | bbox | bbox coverage | checkerboard risk | status |
| --- | --- | --- | --- | --- | --- | --- |
| source_group_01 | `ChatGPT Image Jun 19, 2026, 12_50_06 PM (1).png` | False | [0, 0, 1447, 1085] | 1.0000 | True | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas, possible_baked_checkerboard |
| source_group_01 | `ChatGPT Image Jun 19, 2026, 12_50_06 PM (2).png` | False | [0, 0, 1447, 1085] | 1.0000 | False | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas |
| source_group_02 | `ChatGPT Image Jun 19, 2026, 12_50_25 PM (1).png` | False | [0, 0, 1447, 1085] | 1.0000 | False | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas |
| source_group_02 | `ChatGPT Image Jun 19, 2026, 12_50_25 PM (2).png` | False | [0, 0, 1447, 1085] | 1.0000 | False | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas |
| source_group_03 | `ChatGPT Image Jun 19, 2026, 12_50_38 PM (1).png` | True | [101, 35, 875, 1535] | 0.7396 | False | pass |
| source_group_03 | `ChatGPT Image Jun 19, 2026, 12_50_38 PM (2).png` | True | [30, 74, 983, 1525] | 0.8807 | False | pass |
| source_group_04 | `ChatGPT Image Jun 19, 2026, 12_50_51 PM (1).png` | False | [0, 0, 1447, 1085] | 1.0000 | False | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas |
| source_group_04 | `ChatGPT Image Jun 19, 2026, 12_50_51 PM (2).png` | False | [0, 0, 1447, 1085] | 1.0000 | False | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas |
| source_group_05 | `ChatGPT Image Jun 19, 2026, 12_51_01 PM (1).png` | False | [0, 0, 1447, 1085] | 1.0000 | False | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas |
| source_group_05 | `ChatGPT Image Jun 19, 2026, 12_51_01 PM (2).png` | False | [0, 0, 1447, 1085] | 1.0000 | False | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas |
| source_group_06 | `ChatGPT Image Jun 19, 2026, 12_51_11 PM (1).png` | False | [0, 0, 1447, 1085] | 1.0000 | True | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas, possible_baked_checkerboard |
| source_group_06 | `ChatGPT Image Jun 19, 2026, 12_51_11 PM (2).png` | False | [0, 0, 1447, 1085] | 1.0000 | False | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas |
| source_group_07 | `ChatGPT Image Jun 19, 2026, 12_51_19 PM (1).png` | False | [0, 0, 1447, 1085] | 1.0000 | False | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas |
| source_group_07 | `ChatGPT Image Jun 19, 2026, 12_51_19 PM (2).png` | False | [0, 0, 1447, 1085] | 1.0000 | True | no_alpha_channel, almost_no_transparency, content_bbox_fills_canvas, possible_baked_checkerboard |

A risk flag does not mean the asset is unusable; it means cutting should wait for visual confirmation or masking rules.
