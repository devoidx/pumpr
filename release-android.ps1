# Pumpr Android Release Script
# Run from: C:\Users\admcm\pumpr
# Usage: .\release-android.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = "C:\Users\admcm\pumpr"
$BUILD_GRADLE = "$ROOT\frontend\android\app\build.gradle"
$VERSION_TRACKER = "$ROOT\ANDROID_VERSION.txt"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Pumpr Android Release Helper" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: git pull ---
Write-Host "[1/5] Pulling latest code from git..." -ForegroundColor Yellow
Set-Location $ROOT
git pull
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: git pull failed" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

# --- Step 2: Show current versions ---
Write-Host ""
Write-Host "[2/5] Current version in build.gradle:" -ForegroundColor Yellow
$gradleContent = Get-Content $BUILD_GRADLE -Raw
$codeMatch = [regex]::Match($gradleContent, 'versionCode\s+(\d+)')
$nameMatch = [regex]::Match($gradleContent, 'versionName\s+"([^"]+)"')
$currentCode = [int]$codeMatch.Groups[1].Value
$currentName = $nameMatch.Groups[1].Value
Write-Host "  versionCode : $currentCode" -ForegroundColor White
Write-Host "  versionName : $currentName" -ForegroundColor White

# --- Step 3: Prompt for new versions ---
Write-Host ""
Write-Host "[3/5] Enter new version details:" -ForegroundColor Yellow
$suggestedCode = $currentCode + 1
$newCode = Read-Host "  New versionCode (current: $currentCode, suggested: $suggestedCode)"
if ([string]::IsNullOrWhiteSpace($newCode)) { $newCode = $suggestedCode }
$newCode = [int]$newCode

$newName = Read-Host "  New versionName (current: $currentName, e.g. 1.8.19)"
if ([string]::IsNullOrWhiteSpace($newName)) { $newName = $currentName }

if ($newCode -le $currentCode) {
    Write-Host "ERROR: versionCode must be greater than $currentCode" -ForegroundColor Red
    exit 1
}

# --- Step 4: Update build.gradle ---
Write-Host ""
Write-Host "[4/5] Updating build.gradle..." -ForegroundColor Yellow
$updated = $gradleContent `
    -replace "versionCode\s+$currentCode", "versionCode $newCode" `
    -replace "versionName\s+`"$currentName`"", "versionName `"$newName`""
Set-Content $BUILD_GRADLE $updated -NoNewline
Write-Host "  versionCode : $currentCode -> $newCode" -ForegroundColor Green
Write-Host "  versionName : $currentName -> $newName" -ForegroundColor Green

# Update the tracker file
(Get-Content $VERSION_TRACKER) | ForEach-Object {
    $_ -replace 'current versionCode : \d+', "current versionCode : $newCode" `
       -replace 'current versionName : [\d.]+', "current versionName : $newName" `
       -replace 'last uploaded       : .*', "last uploaded       : $(Get-Date -Format 'yyyy-MM-dd')"
} | Set-Content $VERSION_TRACKER
Write-Host "  ANDROID_VERSION.txt updated" -ForegroundColor Green

# --- Step 5: cap sync ---
Write-Host ""
Write-Host "[5/5] Running cap sync android..." -ForegroundColor Yellow
Set-Location "$ROOT\frontend"
npx cap sync android
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: cap sync failed" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

# --- Done: remind what to do next ---
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Pre-build steps complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Open Android Studio (if not open)" -ForegroundColor White
Write-Host "  2. Build > Generate Signed Bundle / APK" -ForegroundColor White
Write-Host "  3. Choose Android App Bundle" -ForegroundColor White
Write-Host "  4. Keystore: C:\Users\admcm\pumpr-keystore.jks" -ForegroundColor White
Write-Host "  5. Output: frontend\android\app\release\app-release.aab" -ForegroundColor White
Write-Host ""
Write-Host "Then in Play Console:" -ForegroundColor White
Write-Host "  Release > Testing > Closed Testing > Manage Track" -ForegroundColor White
Write-Host "  Create New Release > Upload AAB > Add release notes > Submit" -ForegroundColor White
Write-Host ""
Write-Host "  versionCode for this build: $newCode" -ForegroundColor Cyan
Write-Host "  versionName for this build: $newName" -ForegroundColor Cyan
Write-Host ""

# Remind to commit the version bump
$doCommit = Read-Host "Commit version bump to git now? (y/n)"
if ($doCommit -eq 'y') {
    Set-Location $ROOT
    git add frontend/android/app/build.gradle ANDROID_VERSION.txt
    git commit -m "chore: bump Android versionCode to $newCode ($newName)"
    git push
    Write-Host "Committed and pushed." -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Good luck with the release!" -ForegroundColor Cyan
