# POST-COMMAND: Project Cleanup After Final Martyskin Build

## Purpose

This document is an additional post-command for Codex/agent work after the main corrective integration task is complete.

The current project folder has accumulated many obsolete iterations, temporary builds, extracted APKs, copied web versions, duplicated assets, old generated backgrounds, failed Cocos2d-x ports, debug artifacts, caches, and throwaway archives. The result is unacceptable: the project size is several GB for a small game, and it is no longer obvious what is the final working project and what is garbage.

After the main task is completed, the agent must perform a **controlled cleanup**, leaving only the final relevant project, documentation, source assets, build instructions, and final distributable artifacts.

This cleanup is mandatory, but it must be done safely.

---

## Critical Safety Rule

Do **not** blindly run destructive commands such as:

```bash
rm -rf *
git clean -xfd
```

Do **not** delete anything before producing an inventory and classification.

Do **not** delete the final working source tree.

Do **not** delete canonical lore/docs.

Do **not** delete final build outputs.

Do **not** delete original source assets that are still referenced by the final project.

Do **not** delete Git metadata.

Do **not** delete files outside the repository/project root.

The cleanup must be performed as an audited process, not as a filesystem massacre. This is not “burn the jungle”; this is “remove old banana peels without demolishing the train station”.

---

## Required Cleanup Workflow

### Phase 1 — Identify Project Root

First identify the actual project root.

The project root is the directory containing one or more of:

```text
.git/
AGENTS.md
README.md
docs/
Classes/
Resources/
proj.android/
android/
web/
CMakeLists.txt
build.gradle
```

If multiple candidate project roots exist, stop and report them. Do not delete anything until the final root is clear.

---

### Phase 2 — Create Cleanup Inventory

Before deleting or moving anything, generate a full inventory.

Create:

```text
docs/CLEANUP_INVENTORY.md
```

It must include:

1. current project root path;
2. total project size before cleanup;
3. directory size summary;
4. list of large files above 50 MB;
5. list of duplicate-looking folders;
6. list of old iteration folders;
7. list of build/cache folders;
8. list of archives/apks/exports;
9. proposed keep/delete/archive classification.

Suggested commands:

#### Linux/macOS/Git Bash

```bash
du -h -d 2 . | sort -h > cleanup_du_summary.txt
find . -type f -size +50M -print > cleanup_large_files.txt
find . -maxdepth 3 -type d | sort > cleanup_dirs.txt
find . -type f \( -name "*.apk" -o -name "*.aab" -o -name "*.zip" -o -name "*.7z" -o -name "*.rar" -o -name "*.ipa" -o -name "*.apks" \) -print > cleanup_artifacts.txt
```

#### PowerShell

```powershell
Get-ChildItem -Recurse | Sort-Object Length -Descending | Select-Object FullName, Length -First 100 > cleanup_large_files.txt
Get-ChildItem -Recurse -Directory | Select-Object FullName > cleanup_dirs.txt
Get-ChildItem -Recurse -Include *.apk,*.aab,*.zip,*.7z,*.rar,*.ipa,*.apks | Select-Object FullName, Length > cleanup_artifacts.txt
```

Then summarize these files into `docs/CLEANUP_INVENTORY.md`.

---

### Phase 3 — Define Canonical Final Project

Before deleting, define what is final.

Create:

```text
docs/FINAL_PROJECT_MANIFEST.md
```

It must explicitly list:

1. final Android source directory;
2. final Web source directory;
3. final Cocos2d-x source directory if applicable;
4. final shared resources directory;
5. final docs directory;
6. final config/data files;
7. final fonts;
8. final texture atlases;
9. final audio files;
10. final release artifacts;
11. final build scripts;
12. final GitHub Pages deployment folder if applicable.

Example:

```md
# FINAL_PROJECT_MANIFEST

## Canonical source
- Classes/
- Resources/
- proj.android/
- web/
- CMakeLists.txt

## Canonical docs
- AGENTS.md
- README.md
- docs/MARTYSKIN_WORLD.md
- docs/CODEX_MARTYSKIN_VIDEO_REVIEW_PROMPT.md
- docs/BUILD_AND_INSTALL.md
- docs/WEB_DEPLOY_GITHUB_PAGES.md
- docs/FINAL_PROJECT_MANIFEST.md

## Final release artifacts
- releases/android/Martyshkin-Trud-texture10-clean-20260612-release.apk
- releases/web/index.html
- releases/web/assets/
```

If a file/folder is not in this manifest and is not required by the build, it becomes a candidate for deletion or archival.

---

### Phase 4 — Classify Files

Classify the project into four groups.

#### A. Keep

Must keep:

```text
.git/
AGENTS.md
README.md
docs/
Classes/
Resources/
Source/
assets/
config/
fonts/
audio/
textures/
proj.android/
android/
web/
CMakeLists.txt
build.gradle
gradle/
gradlew
gradlew.bat
settings.gradle
package.json
package-lock.json
yarn.lock
pnpm-lock.yaml
```

Only keep these if they belong to the final build or documentation.

#### B. Keep final release only

Keep final output artifacts only if they are current and named clearly.

Recommended final output structure:

```text
releases/
  android/
    Martyshkin-Trud-texture10-clean-20260612-release.apk
    Martyshkin-Trud-texture10-clean-20260612-release.aab
  web/
    index.html
    assets/
  checksums/
    SHA256SUMS.txt
```

Old APKs, old web zips, debug APKs, extracted APKs, old signed releases, and failed test exports should not remain scattered around the project root.

#### C. Archive optionally

If an old iteration may be useful historically but not needed for the final project, move it into:

```text
_archive/old_iterations/YYYY-MM-DD/
```

But keep this archive small. Do not preserve gigabytes of garbage “just in case”.

Acceptable archive candidates:

```text
old prompts
small screenshots
important reference images
small prototypes
short notes
manual test reports
```

Bad archive candidates:

```text
old build directories
debug APK spam
node_modules
.gradle
build/
intermediates/
duplicated engine folders
duplicated texture exports
temporary generated images that are not used
```

#### D. Delete

Safe deletion candidates after verification:

```text
*/build/
*/.gradle/
*/.idea/caches/
*/node_modules/
*/dist/
*/out/
*/bin/
*/obj/
*/DerivedData/
*/.cxx/
*/.externalNativeBuild/
*/intermediates/
*/outputs/        # except final release copies already moved to releases/
*.apk            # except final release in releases/android/
*.aab            # except final release in releases/android/
*.ipa            # except final release if relevant
*.apks
*.xapk
*.zip            # except explicitly final archival packages
*.7z
*.rar
*.tmp
*.log
*.bak
*.old
*.orig
*.iml
cleanup_*.txt    # after summarized into docs/CLEANUP_INVENTORY.md
```

Old iteration folders with names like these are deletion/archive candidates:

```text
MartyskinTrudRunner_v1*
MartyskinTrudRunner_v2*
MartyskinTrudRunner_v3*
MartyskinTrudRunner_v4*
MartyskinTrudRunner_v5*
MartyskinTrudRunner_v6*
MartyskinTrudRunner_v7*
MartyskinTrudRunner_v8*
MartyskinTrudRunner_v9*
MartyskinTrudWeb_v1*
MartyskinTrudWeb_v2*
historical_project_fixed*
*_old
*_backup
*_copy
*_broken
*_test
*_debug
*_tmp
```

Exception: if the final source currently lives inside one of these versioned folders, do not delete it. First promote it to the canonical final structure, update the manifest, verify build, then clean the obsolete copies.

---

## Phase 5 — Preserve Final Artifacts First

Before deleting old outputs, copy the final working artifacts into `releases/`.

Required:

```text
releases/android/
releases/web/
releases/checksums/
```

If Android final build exists:

```text
releases/android/Martyshkin-Trud-texture10-clean-20260612-release.apk
```

If Web final build exists:

```text
releases/web/index.html
```

If assets are external:

```text
releases/web/assets/
```

Generate checksums:

```bash
sha256sum releases/android/* releases/web/* > releases/checksums/SHA256SUMS.txt
```

On PowerShell:

```powershell
Get-FileHash releases/android/*, releases/web/* -Algorithm SHA256 > releases/checksums/SHA256SUMS.txt
```

If checksum generation fails, explain why.

---

## Phase 6 — Dry Run Cleanup

Before deleting anything, produce a dry-run deletion list.

Create:

```text
docs/CLEANUP_PLAN.md
```

It must include:

```md
# CLEANUP_PLAN

## Will keep
...

## Will move to archive
...

## Will delete
...

## Not sure / requires user review
...
```

If operating autonomously, only delete items that are clearly non-canonical and reproducible.

Anything uncertain must go into `Not sure / requires user review`, not into deletion.

---

## Phase 7 — Execute Cleanup

After inventory, manifest, and plan exist, perform cleanup.

Preferred process:

1. move uncertain historical material to `_archive/old_iterations/`;
2. delete obvious build/cache outputs;
3. delete old debug artifacts;
4. delete stale archives;
5. verify the final source still builds;
6. verify final release artifacts still exist;
7. regenerate size report.

Suggested Linux/macOS/Git Bash commands after review:

```bash
mkdir -p _archive/old_iterations
mkdir -p releases/android releases/web releases/checksums

# Delete common build/cache folders
find . -type d \( -name build -o -name .gradle -o -name node_modules -o -name dist -o -name out -o -name bin -o -name obj -o -name .cxx -o -name .externalNativeBuild -o -name intermediates \) -prune -exec rm -rf {} +

# Delete loose obsolete artifacts, excluding releases/
find . -path ./releases -prune -o -type f \( -name "*.apk" -o -name "*.aab" -o -name "*.ipa" -o -name "*.apks" -o -name "*.xapk" -o -name "*.zip" -o -name "*.7z" -o -name "*.rar" -o -name "*.tmp" -o -name "*.bak" -o -name "*.old" -o -name "*.orig" -o -name "*.log" \) -print
```

Do not execute deletion command until the printed list is reviewed.

PowerShell equivalent must also be provided if the user is on Windows.

---

## Phase 8 — Rebuild After Cleanup

After cleanup, verify that both builds still work.

Mandatory:

```text
Android build: must still build.
Web build: must still build/run.
```

Run the actual project-specific commands.

If the project uses Gradle:

```bash
./gradlew assembleRelease
```

or on Windows:

```powershell
.\gradlew.bat assembleRelease
```

If Web build is static:

```bash
python3 -m http.server 8080
```

Then test:

```text
http://localhost:8080
```

If Web build uses npm:

```bash
npm install
npm run build
npm run preview
```

If Cocos2d-x + Web/Emscripten is used, run the correct Cocos/Emscripten commands and document them.

---

## Phase 9 — Final Size Report

Create:

```text
docs/CLEANUP_REPORT.md
```

It must include:

1. project size before cleanup;
2. project size after cleanup;
3. amount of space saved;
4. files/folders deleted;
5. files/folders archived;
6. final project structure;
7. final build verification result;
8. remaining large files and why they are kept;
9. manual review items, if any.

Example:

```md
# CLEANUP_REPORT

## Size
- Before: 7.1 GB
- After: 850 MB
- Saved: 6.25 GB

## Deleted
- old Android debug build outputs
- stale web prototypes
- duplicate APK archives
- Gradle caches
- old generated background experiments

## Archived
- short concept screenshots
- old prompt notes

## Verified
- Android release build: passed
- Web build: passed
- GitHub Pages output: present

## Remaining large files
- Resources/textures/atlas/main_atlas.png — required by final build
- Resources/audio/bgm_main.ogg — required by final build
```

---

## Phase 10 — Git Integration

If the repository is under Git and the environment allows Git operations:

1. inspect status:

```bash
git status --short
```

2. add cleanup docs and deletion changes:

```bash
git add .
```

3. commit:

```bash
git commit -m "Clean obsolete Martyskin project iterations and build artifacts"
```

4. if remote push is allowed:

```bash
git push
```

If pushing is not available, provide exact commands for the user.

If a PR workflow is used, create a PR titled:

```text
Cleanup obsolete Martyskin project iterations and artifacts
```

PR body must summarize:
- what was deleted;
- what was archived;
- final size reduction;
- build verification results.

---

## Additional Rules

### Do not delete these without explicit confirmation

```text
docs/MARTYSKIN_WORLD.md
docs/CODEX_MARTYSKIN_VIDEO_REVIEW_PROMPT.md
docs/CODEX_MARTYSKIN_POST_CLEANUP.md
AGENTS.md
README.md
final source folders
final Resources/assets
final releases/
.git/
```

### Do not preserve junk just because it is old

Old debug builds and failed iterations are not “history”; they are banana peels.

### If unsure, archive small files and report large files

If an old folder contains potentially valuable reference images or prompts, preserve only:
- source prompt text;
- reference images;
- final selected images;
- small notes.

Do not archive:
- build folders;
- caches;
- node_modules;
- duplicate generated garbage;
- old APKs unless explicitly marked final.

---

## Final Acceptance Criteria

The cleanup is complete only when:

1. `docs/CLEANUP_INVENTORY.md` exists.
2. `docs/FINAL_PROJECT_MANIFEST.md` exists.
3. `docs/CLEANUP_PLAN.md` exists.
4. `docs/CLEANUP_REPORT.md` exists.
5. Final Android build still works.
6. Final Web build still works.
7. Final release artifacts are in `releases/`.
8. Obsolete iterations are removed or archived.
9. Project size is substantially reduced.
10. Git status is clean or all remaining changes are clearly reported.
11. User can tell what is final without archaeological excavation.

Expected final feeling: “Вот проект”.  
Not: “Где-то среди семи гигабайт лежит примат, удачи”.
