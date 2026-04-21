#!/bin/bash
# Build frontend with current git hash
HASH=$(git rev-parse --short HEAD)
echo "VITE_BUILD_HASH=$HASH" >> /opt/pumpr/frontend/.env
cd /opt/pumpr/frontend && npm run build
# Clean up the hash from .env (it changes each build)
grep -v "VITE_BUILD_HASH" /opt/pumpr/frontend/.env > /tmp/.env.tmp && mv /tmp/.env.tmp /opt/pumpr/frontend/.env
echo "Built v$(grep VERSION /opt/pumpr/frontend/src/version.js | grep -o '[0-9.]*') ($HASH)"
