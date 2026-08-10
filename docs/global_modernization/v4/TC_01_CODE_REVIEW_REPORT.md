# TC-01 code review report

Status: `PASS_NO_BUILD`

## Scope reviewed

- both Android configs, exact JSON contract/schema, no-write host CLI, shared
  PowerShell module, Cocos build wrapper and legacy QA probe integration;
- generated Gradle wrapper/AGP/compile-target/build-tools/NDK/SDK bindings;
- Java process environment, project/user/generated Gradle overrides and
  current-run process evidence;
- cross-platform schema/negative validator and 35-group Windows behavioral
  suite.

## High-risk findings closed

1. Android builds now fail before Cocos when configured JDK identity, exact
   patch or hashes do not match; ambient Java is reported but never selected.
2. The validated generated project is exactly `build/<outputName>/proj`, is
   lexically contained, rejects reparse points and is the same path executed by
   post-export Gradle.
3. Existing partial/stale exports block before Cocos; a wholly absent export is
   allowed on a clean checkout and becomes mandatory immediately after Cocos.
4. Hidden overrides include `JAVA_OPTS`, Java/JDK tool options,
   `GRADLE_USER_HOME`, Gradle project properties and generated
   `org.gradle.java.home`/`local.properties`. Whitespace-only overrides block,
   and per-user Gradle properties bind to the SID-backed Windows profile.
5. Critical Java properties reject duplicates, alternate separators, bare or
   escaped keys, continuations, form-feed and lone-CR delimiters.
6. Cocos and Gradle run inside the exact JDK process scope and `JAVA_HOME/PATH`
   restore after success or throw; Gradle also receives explicit
   `-Dorg.gradle.java.home`.
7. Entrypoint success evidence uses a current-run byte cursor, a hard 1 MiB
   per-poll cap, overlap for boundary matching, nonzero-exit precedence and an
   explicit overflow failure. The wrapper no longer rescans stale whole logs.
8. Post-export/tool verification failure cannot produce a machine report with
   exit code zero.
9. Generated execution binds the exact Gradle distribution URL,
   `gradlew.bat` and wrapper JAR hashes; daemon JVM criteria are forbidden
   because they can override `JAVA_HOME`.
10. Default Cocos invocation/success logs include a GUID and explicit
    pre-existing paths fail before Cocos, preventing cross-run success
    attribution. Gradle postpack logs are diagnostic only and do not decide
    build PASS.
11. Runtime preflight independently pins the approved JDK, Cocos and Android
    policy; a self-consistent rewrite of both config and contract to JDK 21 is
    blocked before any child process.

## Deliberate boundaries

- T4 fresh export/build/install is `DEFERRED_TO_FIRST_ANDROID_P4`, not PASS;
- ignored existing exports are historical evidence only;
- `Test-MtrAndroidToolchain.ps1` remains the stateful emulator/adb QA probe and
  is not used as TC-01 preflight;
- hosted CI executes the stdlib Python structural contract; Windows host and
  PowerShell behavior are separate local receipts;
- no SDK/Cocos/Gradle/package version was upgraded and no global environment
  was changed.

No P0/P1 finding remains within the no-build TC-01 acceptance boundary.
