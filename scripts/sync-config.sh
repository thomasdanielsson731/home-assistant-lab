#!/usr/bin/env bash
# Sync local config/ directory to HA host via rsync over SSH.
# Requires: rsync, ssh access to HA host on port 22222 (SSH add-on default).
#
# Usage: ./scripts/sync-config.sh [--dry-run]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment
ENV_FILE="$REPO_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

HA_HOST="${HA_HOST:?Set HA_HOST in .env (e.g. 192.168.1.50)}"
HA_USER="${HA_USER:-root}"
HA_SSH_PORT="${HA_SSH_PORT:-22222}"
HA_CONFIG_PATH="${HA_CONFIG_PATH:-/config}"

DRY_RUN=""
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN="--dry-run"
  echo "[dry-run] No files will be transferred."
fi

echo "Syncing config to ${HA_USER}@${HA_HOST}:${HA_CONFIG_PATH} ..."

rsync -avz --progress \
  $DRY_RUN \
  --exclude='secrets.yaml' \
  --exclude='.storage/' \
  --exclude='*.db' \
  --exclude='*.db-*' \
  --exclude='*.log' \
  -e "ssh -p ${HA_SSH_PORT}" \
  "$REPO_ROOT/config/home-assistant/" \
  "${HA_USER}@${HA_HOST}:${HA_CONFIG_PATH}/"

rsync -avz --progress \
  $DRY_RUN \
  -e "ssh -p ${HA_SSH_PORT}" \
  "$REPO_ROOT/config/frigate/config.yml" \
  "${HA_USER}@${HA_HOST}:${HA_CONFIG_PATH}/frigate/config.yml"

rsync -avz --progress \
  $DRY_RUN \
  -e "ssh -p ${HA_SSH_PORT}" \
  "$REPO_ROOT/config/double-take/config.yml" \
  "${HA_USER}@${HA_HOST}:${HA_CONFIG_PATH}/double-take/config.yml"

echo "Done. Restart affected add-ons in HA if config changed."
