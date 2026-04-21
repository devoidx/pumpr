#!/bin/bash
set -e
HASH=$(git -C /opt/pumpr rev-parse --short HEAD)
VERSION=$(grep "export const VERSION" /opt/pumpr/frontend/src/version.js | grep -o "[0-9.]*")

echo "Building v${VERSION} (${HASH})..."

cd /opt/pumpr
docker compose build --build-arg BUILD_HASH=$HASH frontend
docker compose up -d frontend

echo "✅ Built v${VERSION} (${HASH})"
