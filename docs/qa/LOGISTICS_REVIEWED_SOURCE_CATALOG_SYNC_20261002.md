# Source-alpha follow-up: current catalog synchronization

Implementation parent279cd51b2245a0b35fefd73d02c3b75fdeac2297.
Roadmap20/73,53 mandatory+7 conditional; M04-C and Release remain partial.

The first clean37-step static cycle produced33 PASS/4 FAIL. The failures were
SOURCE_FINGERPRINT/observed-byte mismatches and stale contact-sheet hashes
after the two deliberate PNG replacements, not new geometry/UUID regressions.
The complete failed run remains at private project
temp/logistics-source-alpha-20261002/static/c1/report.json. It is not a passed
cycle and will not be overwritten or counted toward four passing cycles.

Only the mutable current inventory is synchronized to the actual source:
two PNGs total+98 bytes, reviewed-source manifest+807 canonical text bytes,
source payload+905 bytes. File counts, ownership selectors, packing policy,
accepted atlas measurements, source checkpoint ancestry and every Cocos
metadata fingerprint are unchanged. Source payload is now
85758D221070A927D2734A53DB8A708EE8133285313010687FEB2B4D9A26651B.
No thresholds, old performance decisions or frozen experiment inputs change.

The existing pinned contact-sheet generator regenerated the current catalog:
1558 assets/29 sheets/7 categories. Only two source records and one obstacle
sheet changed;1556 other source records and28 sheet records are identical.
Canonical --check PASS, index SHA-256
44DA7944C170A35BD66B900A532EC155D8185F6B59D8B078857F0825D192737D.
The old active index, manifest and30 rendered files were retained locally in
workspace-private temp/logistics-source-alpha-20261002/prepatch-current-catalog
before regeneration; Git also retains their source history. Existing generator
ownership/containment rules are unchanged. No blanket cleanup took place.

M04-A validator now reports PASS/findings0,1647 source files,1558 images,
24 ownership scopes,14 atlas groups and12 accepted static atlases. Full suite
repetition and runtime acceptance are still pending, so this preparatory fix
does not admit atlas inputs or claim Release. Next: four new clean static
cycles, fresh serial Web/Android builds, four silent runtime cycles and
strict successor recovery binding.
