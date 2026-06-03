# Pumpr Android Build Script (Windows only - NO git commits)
# Run from: C:\Users\admcm\pumpr after doing git pull
# Usage: .\build-android.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = "C:\Users\admcm\pumpr"
$BUILD_GRADLE = "$ROOT\frontend\android\app\build.gradle"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Pumpr Android Build Prep" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# --- Show versions from build.gradle (set on zeolite) ---
$gradleContent = Get-Content $BUILD_GRADLE -Raw
$codeMatch = [regex]::Match($gradleContent, 'versionCode\s+(\d+)')
$nameMatch = [regex]::Match($gradleContent, 'versionName\s+"([^"]+)"')
$versionCode = $codeMatch.Groups[1].Value
$versionName = $nameMatch.Groups[1].Value

Write-Host "Building:" -ForegroundColor Yellow
Write-Host "  versionCode : $versionCode" -ForegroundColor White
Write-Host "  versionName : $versionName" -ForegroundColor White
Write-Host ""

# --- cap sync ---
Write-Host "[1/1] Running cap sync android..." -ForegroundColor Yellow
Set-Location "$ROOT\frontend"
npx cap sync android
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: cap sync failed" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

# --- Instructions ---
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Ready for Android Studio!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Steps:" -ForegroundColor White
Write-Host "  1. Open Android Studio (if not already open)" -ForegroundColor White
Write-Host "  2. Build > Generate Signed Bundle / APK" -ForegroundColor White
Write-Host "  3. Choose Android App Bundle" -ForegroundColor White
Write-Host "  4. Keystore : C:\Users\admcm\pumpr-keystore.jks" -ForegroundColor White
Write-Host "  5. Output   : frontend\android\app\release\app-release.aab" -ForegroundColor White
Write-Host ""
Write-Host "Then in Play Console:" -ForegroundColor White
Write-Host "  Release > Testing > Closed Testing > Manage Track" -ForegroundColor White
Write-Host "  Create New Release > Upload AAB > Add release notes > Submit" -ForegroundColor White
Write-Host ""
Write-Host "  versionCode : $versionCode" -ForegroundColor Cyan
Write-Host "  versionName : $versionName" -ForegroundColor Cyan
Write-Host ""
