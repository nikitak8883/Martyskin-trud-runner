# Missing requirements

## Critical missing

None for local Web generation, Android x86_64 build or Android 16 emulator runtime QA.

## Optional or external validation

- Real Galaxy S25 Ultra validation is still recommended for One UI 8.5, Snapdragon/Adreno, ARM64, S Pen, Samsung services and device-specific power behavior.
- A fresh ARM release build has not been installed on the real phone in this session.
- Git metadata is intentionally not restored in place yet; the verified bundle remains available.
- Global Android environment variables are optional because project profiles use explicit paths.

## Non-blocking tool warnings

- SDK XML version warning from the older required CMake/AGP integration against newer Android Studio metadata.
- Debug-only network-interface enumeration denial from Android SELinux.
- One startup warning about shading scale before the custom Builtin pipeline becomes ready.

None of these warnings prevented scene load, menu readiness, native rendering, background/resume or APK generation.

## `.gitignore` attention

Before restoring Git metadata or creating a checkpoint commit, consider explicitly ignoring local properties, signing material and `.env` files. No Git or `.gitignore` mutation was performed during restoration.
