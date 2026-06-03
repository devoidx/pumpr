#!/bin/bash
# Pumpr Android Version Bump Script
# Run on zeolite from /opt/pumpr BEFORE doing the Windows build
# Usage: bash scripts/bump-android-version.sh

set -e

ROOT="/opt/pumpr"
BUILD_GRADLE="$ROOT/frontend/android/app/build.gradle"
VERSION_TRACKER="$ROOT/ANDROID_VERSION.txt"
VERSION_JS="$ROOT/frontend/src/version.js"

echo ""
echo "======================================"
echo "  Pumpr Android Version Bump"
echo "======================================"
echo ""

# --- Read current versions ---
CURRENT_CODE=$(grep -oP 'versionCode \K\d+' "$BUILD_GRADLE")
CURRENT_NAME=$(grep -oP 'versionName "\K[^"]+' "$BUILD_GRADLE")
CURRENT_WEB=$(grep -oP "VERSION = '\K[^']+" "$VERSION_JS")

echo "Current Android versionCode : $CURRENT_CODE"
echo "Current Android versionName : $CURRENT_NAME"
echo "Current web version         : $CURRENT_WEB"
echo ""

# --- Prompt for new values ---
SUGGESTED_CODE=$((CURRENT_CODE + 1))
read -p "New versionCode (current: $CURRENT_CODE, suggested: $SUGGESTED_CODE): " NEW_CODE
NEW_CODE=${NEW_CODE:-$SUGGESTED_CODE}

read -p "New versionName (current: $CURRENT_NAME, suggested: $CURRENT_WEB): " NEW_NAME
NEW_NAME=${NEW_NAME:-$CURRENT_WEB}

# --- Validate ---
if [ "$NEW_CODE" -le "$CURRENT_CODE" ]; then
  echo "ERROR: versionCode must be greater than $CURRENT_CODE"
  exit 1
fi

echo ""
echo "Updating build.gradle..."
sed -i "s/versionCode $CURRENT_CODE/versionCode $NEW_CODE/" "$BUILD_GRADLE"
sed -i "s/versionName \"$CURRENT_NAME\"/versionName \"$NEW_NAME\"/" "$BUILD_GRADLE"
echo "  versionCode : $CURRENT_CODE -> $NEW_CODE"
echo "  versionName : $CURRENT_NAME -> $NEW_NAME"

echo "Updating ANDROID_VERSION.txt..."
sed -i "s/current versionCode : .*/current versionCode : $NEW_CODE/" "$VERSION_TRACKER"
sed -i "s/current versionName : .*/current versionName : $NEW_NAME/" "$VERSION_TRACKER"
sed -i "s/last uploaded       : .*/last uploaded       : $(date +%Y-%m-%d)/" "$VERSION_TRACKER"
echo "  Done"

echo ""
echo "Committing and pushing..."
cd "$ROOT"
git add frontend/android/app/build.gradle ANDROID_VERSION.txt
git commit -m "chore: bump Android versionCode to $NEW_CODE ($NEW_NAME)"
git push
echo "  Done"

echo ""
echo "======================================"
echo "  Zeolite steps complete!"
echo "======================================"
echo ""
echo "Now on Windows:"
echo "  1. cd C:\\Users\\admcm\\pumpr"
echo "  2. git pull"
echo "  3. .\\build-android.ps1"
echo ""
echo "  versionCode for this build : $NEW_CODE"
echo "  versionName for this build : $NEW_NAME"
echo ""
