# M04-C-QA-SOURCE-MATTE-01: independent source correction

Status: implementation prepared; runtime acceptance NOT_RUN; Release not accepted.
Roadmap: M04-C/FAMILIES still partial,20/73(27.3973%),53 mandatory+7 conditional remain.

## Source and scope

Anchor093ba378dcf738142a1d06e5335823b04128da4b removes only the unqualified
attempt02 logistics PAC/meta and records the source-art hold. The frozen
protocol revision4, original source inventory, paired input builds and
qualification evidence remain immutable. Registered attempt02 samples stay0.

Two static platform sprites replaced through the existing pinned source
override, shared by Android/Web:

- base_platforms_001:677x109,alpha bbox[6,6,671,103],UUID
  b2a2ae16-6016-41d5-80dc-b61ade2cd7d7,PNG
  42C8EA09D19E0CD624E2456A4637A18D2CE9F71EF608C0865525B0C7B3E97517.
- extended_platforms_003:466x162,alpha bbox[6,6,460,156],UUID
  bd3f7950-3e52-4545-93df-a4d0f632d436,PNG
  676192F42CC4FEA67CA2DEC8350D300A6E7E6887EB3B0635AD74DBA18563D3A2.

All26 original metadata files remain byte-identical;24 other logistics PNGs,
runtime code, native code and build settings remain unchanged. Import trim,
pivot, UUID and collision/layout contracts are unchanged. Generated pixels
are not claimed to be identical to the original painted artwork. Codex reviewed
the full object, palette, five pallet supports and rope topology before apply.

## Cutout and recovery guards

Built-in imagegen edited each target separately. A failed net proposal retained
opaque white backing and was quarantined, not integrated. Both pallet proposals
had alpha1 margin residue; normalizing the full bbox visibly shrank the wood.
The accepted second proposal has an explicit reviewed extraction frame
[19,198,2140,520]. The normalizer refuses any frame excluding even one alpha>=2
source pixel. No color-threshold mask or automatic semantic white removal exists.
An additional alpha128 silhouette-bbox gate rejects nearly invisible outliers
which otherwise fake the import bounds. The old lifebuoy reproduction remains
unchanged. Generated source files and metadata pins stay outside Cocos assets.

Four pallet openings and fifteen mesh cells plus four loop centers have
23 alpha-zero region assertions. Remaining two nearwhite opaque net pixels
are material highlights, not classified automatically as defects. White-pixel
counts1313->0 and3306->2 are documentary support, not the sole acceptance gate.
The July net source fix hash equals the prepatch source8F3E...; this is not a
new atlas regression. Its legacy manifest runtimeSha256 was stale BDC1...;
the reviewed override now binds the actual replacement without changing old
sheet/sourceBounds lineage.

## Validation at source commit boundary

- Reviewed-source17 tests PASS, including all-record preflight/no partial
  writes, repinned opaque-gap negatives, each PNG normalization reproduction,
  visible-silhouette and invalid frame negatives, unchanged metadata/lineage,
  and six metadata paths round-tripped under both Git autocrlf policies.
- Independent private Verify-Source.py PASS:24 PNG negative controls,
  all26 metadata pins, only two allowed manifest entry changes, unpacked
  topology and protected runtime/native/build settings.
- git diff --check PASS. No unrelated workspace files staged.
- Full37-step static suite, fresh serial Web/Android builds and four silent
  runtime cycles per platform: pending; do not use old paired qualification
  as acceptance for this patch or as timing samples.

Prompts, rejected proposal hashes and environment issue are recorded in
[generation history](LOGISTICS_REVIEWED_SOURCE_PROMPTS_20261002.json).
The base interpreter lacked zlib_ng; existing bootstrap-verified isolated
venv-py313-2fbd8ac10b67 was used without global installation or codec fallback.

Next: clean-source validation and fresh silent builds/QA, then immutable
successor evidence and explicit Hermes resume binding. Full campaign/skin-pose
coverage, new atlas preregistration, technical Release and owner/signing gates
remain separate. Physical devices,main/Pages publication and global changes
are not authorized by this source slice.
