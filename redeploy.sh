#!/usr/bin/env bash
set -euo pipefail

# Go to the directory where this script is located (and where docker-compose.yml lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "===> Updating repository (git pull)..."
git pull

# Detect docker-compose command
if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
else
  echo "ERROR: Neither 'docker-compose' nor 'docker compose' was found."
  exit 1
fi

echo "===> Rebuilding and restarting containers..."
$COMPOSE_CMD up -d --build

echo "===> Removing dangling images..."
docker image prune -f

echo "===> Done."