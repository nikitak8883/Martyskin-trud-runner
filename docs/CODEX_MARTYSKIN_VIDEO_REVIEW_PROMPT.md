CODEX TASK / TECHNICAL SPECIFICATION
Project: Martyskin Trud / Martyskin World
Purpose: full corrective rebuild and final integration of Android + Web versions based on the current Cocos2d-x branch and the analyzed Android screen recording.

=====================================================================
0. MANDATORY WORK MODE
=====================================================================
You are not being asked for a cosmetic tweak. You must perform a full audit, corrective redesign, synchronization, rebuild, and final packaging of BOTH versions of the game:
1) Android version
2) Web version

You must first inspect the entire repository/workspace and read all project documentation available, especially:
- AGENTS.md
- docs/MARTYSKIN_WORLD.md
- docs/CHAT_HISTORY_SUMMARY.md
- docs/ANDROID_VERSION_NOTES.md
- docs/WEB_VERSION_NOTES.md
- docs/COCOS2DX_PORTING_NOTES.md
- any level configs, sprite atlases, audio folders, screenshots, concept art, and local image references.

If there are local project images, concept art, previous screenshots, or generated references, you are explicitly authorized to use them as source/reference material for generating or repainting backgrounds, textures, props, UI art, and level storytelling visuals.
You are also authorized to use any suitable LOCAL or CLOUD tooling/frameworks needed for the job, including but not limited to:
- Cocos2d-x tools
- Emscripten / WebAssembly toolchain
- Gradle / Android SDK
- image generation / image editing tools
- vector tools / raster tools
- texture atlas packers
- audio generation / editing tools
- profiling / debugging / optimization tools
- Git / GitHub tooling

If direct autonomous Git integration is available in the environment, perform it. If not, create clean commits locally and provide the exact push instructions.

IMPORTANT: do not ignore requirements, do not simplify the art into primitive shapes, do not keep placeholder visuals in the final build, and do not replace required thematic backgrounds with abstract gradients or random overlays.

=====================================================================
1. VIDEO REVIEW: WHAT IS WRONG IN THE CURRENT ANDROID BUILD
=====================================================================
The uploaded Android screen recording shows that there has been progress, but the current result is still not acceptable. The following issues are considered confirmed defects and must be corrected.

A. Background / visual composition defects
1. Background is effectively double-layered in the wrong way:
   - one rear image layer exists;
   - one more front texture layer floats above it;
   - these two layers are not visually synchronized and do not read as a single scene.
2. The background art does not match the exact theme of the level strongly enough.
3. Background and gameplay layer do not feel like parts of the same world.
4. Some foreground texture overlays visually collide with gameplay elements.
5. There is a visible impression of texture stacking / texture overlap / layer collision.
6. The parallax logic is either weak or incoherent.
7. The level needs a dynamic, story-driven background that evolves with progression.

B. Texture and prop defects
1. Platforms are again “nothing objects” instead of meaningful structures.
2. Platforms must be rebuilt into actual construction scaffolding, beams, temporary bridges, suspended work platforms, maintenance structures, or other level-relevant supports.
3. Multiple texture groups are not stylistically synchronized.
4. Props need a complete re-pass so every object reads clearly and belongs to the level theme.
5. Texture collisions / overlay problems need to be fully eliminated.

C. Primate / character defects
1. The primate sprite still needs a full art pass:
   - more detail;
   - better silhouette;
   - more readable limbs, body, helmet, face, tail;
   - stronger animation.
2. Skins are too shallow.
3. Skins must be made genuinely different:
   - different primate species/types;
   - different clothing/accessories;
   - visible personality.
4. Increase the number of skins if needed.
5. Add special temporary visual transformation bonuses that change the primate’s appearance humorously:
   - level-themed outfit pieces;
   - altered shape;
   - funny temporary costume states.

D. Typography / UI defects
1. Font readability is insufficient.
2. The Russian text must be cleaner, more readable, and better integrated.
3. UI text and object labels need stronger hierarchy and better legibility.
4. Debug-looking outlines / helper rectangles / intrusive boxes must not be visible in release mode.
5. Story banner presentation must be improved so it does not feel like an awkward overlay.

E. Audio defects
1. Audio is effectively absent / missing / broken according to the user review.
2. Full rebuild of audio is required:
   - relevant music;
   - relevant SFX;
   - working toggles and volume control;
   - correct loading and playback on Android and Web.

F. Engine usage / graphics quality defects
1. The current build does not fully exploit the graphics/rendering potential of the engine.
2. Graphics require a total rebuild toward maximum reasonable engine capability and GPU-aware optimization.
3. Visual effects, post effects, particles, animation polish, and layer synchronization are insufficient.

G. Hidden developer review mode missing
1. Add a secret developer mode via hidden combination or code.
2. In developer mode:
   - all levels unlock;
   - HP become infinite;
   - optionally show debug info toggles;
   - allow full review of assets/levels without normal progression restrictions.

=====================================================================
2. OVERALL MISSION
=====================================================================
Take the latest working Android gameplay version as the baseline for mechanics and feature set, then rebuild/refine/synchronize the entire presentation for BOTH Android and Web on top of the Cocos2d-x architecture.

Goal: final project must feel like a polished, cohesive, funny, story-driven “Martyskin World” game, not a prototype.

You must:
- fully integrate the required changes into the project;
- rebuild art, background, UI, audio, and level synchronization;
- complete final builds for Android and Web;
- provide working install/run/deploy instructions;
- perform at least 4 mandatory cycles of debugging/optimization/fault-finding.

=====================================================================
3. MANDATORY ART AND WORLD SYNCHRONIZATION
=====================================================================
The background, level geometry, gameplay props, UI, labels, primate skins, and visual effects must all be synchronized into a single cohesive visual language.

MANDATORY RULES:
1. Background and level must become a single whole.
2. Each level must have a thematic dynamic background generated from:
   - existing project lore;
   - local image library / references from the project;
   - newly generated supporting art where necessary.
3. Backgrounds must be generated or repainted as needed using the project lore and local references.
4. All textures must be re-synchronized stylistically:
   - background;
   - foreground;
   - platforms;
   - obstacles;
   - bonuses;
   - NPCs;
   - player skins;
   - UI panels.
5. Level progression should visually reveal more of the story as the player advances.
6. Story banners must fit the scene and not feel detached.

=====================================================================
4. BACKGROUND REWORK REQUIREMENTS
=====================================================================
For each level, create a dynamic thematic background.
The background must include:
- far background layer;
- mid background layer;
- near background layer;
- optional foreground ambience layer;
- parallax motion;
- theme-specific props;
- humor/signage/details;
- progression-based reveal/state changes.

Fix the current “double background” issue by either:
- merging the current rear image and front texture system into a single coherent multi-layer composition;
OR
- replacing them with a fully rebuilt layered scene.

Thematic examples:
1. Construction site level:
   - cranes;
   - scaffold zones;
   - stacks of materials;
   - funny signs;
   - smoke / dust / welding sparks;
   - primate workers.
2. Window level:
   - crooked facades;
   - dangling frames;
   - half-installed glass;
   - repair chaos.
3. Bureaucracy level:
   - archives, stamps, papers, cabinets;
   - forms spilling into the world.
4. Parking level:
   - badly parked vehicles;
   - cones;
   - warped line markings;
   - “I’ll be right back” humor.
5. Chicken/pavlin/inspection levels:
   - full world-building around those themes.
6. All later levels must be equally themed and equally coherent.

=====================================================================
5. PLATFORM AND OBSTACLE REBUILD
=====================================================================
Platforms must no longer be generic floating elements.
Rebuild them into meaningful level objects, such as:
- scaffold planks;
- steel beams;
- temporary catwalks;
- cable trays;
- pallets;
- suspended platforms;
- maintenance bridges;
- office shelves / archive supports where appropriate;
- rail depot walkways on depot-themed levels.

Obstacle art must be fully reworked and synchronized.
Each obstacle must be visually readable and theme-correct.
Russian labels must be returned and integrated cleanly.
Examples:
- “КИРПИЧ С ДУШОЙ”;
- “ОТЧЁТ”;
- “ОКНО В БОК”;
- “БРИГАДА НА МЕСТЕ”;
- “220V И ВЕРА”;
- “НЕ БОЯТЬСЯ”;
- “ДОРОГА ЗАКРЫТА”;
- “КРАСКА С ДУШОЙ”;
- “БАЛКА СЮРПРИЗ”.

Also add additional humorous signs/banners where appropriate.

=====================================================================
6. PRIMATE, SKINS, AND TEMPORARY VISUAL BONUS STATES
=====================================================================
The main primate must receive a full texture/art/animation overhaul.
Required improvements:
- more detailed face;
- clearer limbs;
- clearer helmet and accessories;
- better tail rendering;
- better run/jump/dash frames;
- stronger silhouette at gameplay scale.

Skins:
- make skins genuinely distinct in species/look/costume;
- increase skin count if useful;
- each skin must have a proper preview in the selection menu;
- add clothing/accessories and visual identity.

Temporary visual bonus states:
Implement humorous temporary appearance modifiers caused by bonuses.
Examples:
- construction foreman vest;
- inspector goggles;
- bureau clerk glasses + stamp bag;
- electrician gloves/helmet;
- cosmic monkey suit;
- chicken accreditation badge;
- peacock feather cape;
- banana magnet backpack.

These must be visually level-aware where possible.

=====================================================================
7. FONT, TEXT, UI, READABILITY
=====================================================================
Rework text rendering and typography.
Tasks:
1. Choose or integrate a more readable font with good Cyrillic support.
2. Rework text scale, outlines, contrast, and placement.
3. Ensure readability on phone screens.
4. Ensure Russian text is clean and correctly spelled.
5. Story banners should animate in/out cleanly.
6. UI panels must not cover critical gameplay information.
7. Release builds must not show intrusive debug visuals.

=====================================================================
8. AUDIO REBUILD
=====================================================================
Audio currently fails the product requirement.
You must generate/integrate a full audio package:
- background music for menu and gameplay;
- level-appropriate monkey-themed/comedic music;
- jump, dash, collect, hit, stomp, banner, bonus, pause, clear sounds;
- optional monkey vocal stingers;
- correct volume controls;
- correct enable/disable logic;
- correct Android and Web loading behavior.

If there are missing files, generate or synthesize replacements.
If platform limitations exist, implement compatible fallback behavior.

=====================================================================
9. ENGINE / RENDERING / GPU / OPTIMIZATION
=====================================================================
You are authorized to push the rendering and GPU utilization to the maximum reasonable level for this project while keeping performance stable.

Required rendering/graphics work:
- proper virtual resolution pipeline;
- clean layering;
- parallax background system;
- sprite batching / atlases;
- particles;
- glow / soft bloom-like post effects where possible;
- vignette / atmosphere;
- camera shake;
- improved animation timing;
- GPU-friendly rendering choices;
- removal of wasteful per-frame allocations;
- object pools for particles / transient objects;
- release-vs-debug separation.

Optimization requirements:
- memory optimization;
- GPU optimization;
- CPU optimization;
- reduced garbage/per-frame allocation;
- avoid texture duplication;
- audit loading paths;
- audit scene transitions;
- profile Android and Web builds.

=====================================================================
10. PHYSICS / MECHANICS
=====================================================================
Mechanics have improved but still require serious refinement.
Do a full tuning pass for:
- jump height;
- jump feel;
- double jump;
- dash timing and cooldown;
- collision stability;
- platform landing;
- bonus timings;
- NPC stomp logic;
- damage logic;
- review mode behavior.

Use stable frame-rate-independent logic.
If needed, introduce fixed or semi-fixed timestep logic.

=====================================================================
11. DEVELOPER MODE
=====================================================================
Implement a hidden developer mode.
Provide at least one hidden activation method, for example:
- secret tap pattern in menu;
- hidden code entry sequence;
- specific button combination;
- long-press combination.

In developer mode:
- unlock all levels;
- infinite HP;
- optionally infinite bonus duration toggle;
- optionally show/hide debug overlay;
- optionally quick level jump.

This mode is required to support full QA/review.

=====================================================================
12. LEVEL COUNT AND CONTENT
=====================================================================
Expand and maintain at least 15 levels.
All levels must feel authored, not random.
All must have:
- title;
- subtitle;
- theme;
- story banners;
- synchronized background;
- synchronized obstacles/platforms;
- tuned difficulty;
- target banana count;
- speed/length values;
- visual identity.

=====================================================================
13. AUTONOMOUS FINALIZATION
=====================================================================
You must perform the final assembly of both versions yourself if the environment allows it.
Deliverables expected from you:
1. final Android build / package;
2. final Web build;
3. updated source project;
4. updated docs;
5. final installation instructions;
6. final Git/GitHub deployment instructions;
7. if Git access is available, perform the integration/commit/push or prepare clean PR-ready changes.

=====================================================================
14. REQUIRED DOCUMENTATION OUTPUT
=====================================================================
Produce detailed step-by-step documentation for:
A. Installing the Android app on a phone.
B. Running the Web version locally.
C. Uploading/deploying the Web version to GitHub / GitHub Pages.
D. Building the project from source.
E. Using developer mode.

These instructions must be detailed, explicit, beginner-friendly, and complete.
If automatic installation/deployment was not possible, clearly explain the manual steps.

=====================================================================
15. MINIMUM DEBUG / OPTIMIZATION / FAULT-FINDING CYCLES
=====================================================================
MANDATORY MINIMUM: 4 full cycles.
You must explicitly perform and report at least these 4 cycles:

Cycle 1 — structural audit and defect identification
- inspect repo;
- inspect builds;
- inspect assets;
- inspect rendering pipeline;
- identify breakpoints and blockers.

Cycle 2 — visual/art/background synchronization pass
- fix background system;
- fix texture overlap;
- rebuild platforms/props;
- improve player art/skins;
- improve text/UI readability.

Cycle 3 — mechanics/audio/engine optimization pass
- tune physics;
- integrate audio;
- optimize resource handling;
- improve engine usage;
- remove debug pollution from release.

Cycle 4 — final QA/build/deployment pass
- rebuild Android and Web;
- verify menus, levels, audio, dev mode;
- verify docs;
- verify deployment path;
- produce final report.

If problems remain after 4 cycles, continue further cycles until stable, but the report must document at least the first 4.

=====================================================================
16. REQUIRED FINAL REPORT FORMAT
=====================================================================
At the end, provide:
1. Summary of what was changed.
2. List of changed files.
3. Newly generated assets.
4. Build commands used.
5. What was tested.
6. Results of the 4 required cycles.
7. Remaining manual checks.
8. Installation instructions.
9. Web/GitHub deployment instructions.
10. Known limitations, if any.

Final acceptance condition:
The result must feel like a polished, unified, funny, visually coherent “Martyskin World” game with synchronized backgrounds, props, text, audio, and mechanics — not a prototype, not a placeholder, and not a set of disconnected texture layers.
