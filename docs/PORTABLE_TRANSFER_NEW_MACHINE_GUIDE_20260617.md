# New Machine Restore Guide 20260617

## 1. Copy and verify
1. Copy the portable archive from:
   `C:\Test\MTRCocosCreator_portable_transfer_20260617`
2. On the new machine, extract the zip.
3. Verify the archive checksum with the generated `SHA256SUMS.txt`.

PowerShell example:

```powershell
Get-FileHash "MTRCocosCreator-portable-20260617.zip" -Algorithm SHA256
```

Compare it with the `ARCHIVE_SHA256` line in `SHA256SUMS.txt`.

## 2. Expected extracted folder
The archive extracts into:

```text
MTRCocosCreator/
```

## 3. Required tools
- Cocos Creator matching the project runtime
- Node.js/npm for project tooling if needed
- Python 3 for helper scripts
- Android Studio / Android SDK / adb for Android installs
- JDK compatible with the Gradle project
- Git, if using the backup bundle

## 4. Restore Git backup from bundle
If using the generated bundle:

```powershell
git clone "MTRCocosCreator-git-backup-20260617.bundle" "MTRCocosCreator"
cd "MTRCocosCreator"
```

The local zip archive is the primary transfer artifact; Git is an additional backup.

## 5. Android install command
After extraction, install the final APK:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r ".\releases\android\Martyshkin-Trud-texture10-clean-20260612-release.apk"
```

If Android reports a signature mismatch:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" uninstall com.martyskin.trudrunner
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install ".\releases\android\Martyshkin-Trud-texture10-clean-20260612-release.apk"
```

## 6. Web local run

```powershell
cd ".\releases\web"
python -m http.server 8088
```

Open:

```text
http://127.0.0.1:8088/
```
