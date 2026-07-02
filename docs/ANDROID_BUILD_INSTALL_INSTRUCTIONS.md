# Android build/install

## Android Studio

1. Open project.
2. Wait Gradle Sync.
3. Select `app`.
4. Build > Generate Signed Bundle / APK.
5. Use release APK for sharing.
6. Test install locally first.
7. For sending to friends, use Google Drive. Telegram sometimes breaks APK transfer.

## Console

```bash
cd PROJECT_ROOT
./gradlew clean
./gradlew :app:assembleRelease
```

APK usually:
`app/build/outputs/apk/release/`
