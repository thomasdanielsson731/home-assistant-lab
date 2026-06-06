#!/usr/bin/env bash
# repo-maintenance.sh — Auto-commit, push, and sync config to HAOS (Linux/macOS)
#
# Usage:
#   ./scripts/repo-maintenance.sh
#   ./scripts/repo-maintenance.sh --reload
#   ./scripts/repo-maintenance.sh --dry-run

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$REPO_ROOT/logs"
LOG_FILE="$LOG_DIR/maintenance.log"
RELOAD=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --reload) RELOAD=true ;;
    --dry-run) DRY_RUN=true ;;
  esac
done

log() {
  mkdir -p "$LOG_DIR"
  echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOG_FILE"
}

cd "$REPO_ROOT"
log "=== Maintenance start ==="

# Load .env
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a; source "$REPO_ROOT/.env"; set +a
fi

# ── 1. Git commit + push ─────────────────────────────────────────────────────

if [[ -n "$(git status --porcelain 2>/dev/null | grep -vE '^\?\? .*\.env$|secrets\.yaml|^\?\? logs/')" ]]; then
  log "Uncommitted changes detected"
  if [[ "$DRY_RUN" == true ]]; then
    log "[dry-run] Would commit and push"
  else
    git add -A
    git reset HEAD -- .env 2>/dev/null || true
    git reset HEAD -- config/home-assistant/secrets.yaml 2>/dev/null || true
    if [[ -n "$(git diff --cached --name-only)" ]]; then
      git commit -m "chore: auto maintenance snapshot $(date '+%Y-%m-%d %H:%M')"
      git push origin HEAD && log "Pushed to origin" || log "WARN: git push failed"
    fi
  fi
else
  log "Working tree clean — skip commit"
fi

# ── 2. Sync config ───────────────────────────────────────────────────────────

if [[ "$DRY_RUN" == true ]]; then
  "$SCRIPT_DIR/sync-config.sh" --dry-run
else
  log "Syncing config to HAOS ..."
  "$SCRIPT_DIR/sync-config.sh"
  log "Sync complete"
fi

# ── 3. Reload HA (optional) ──────────────────────────────────────────────────

if [[ "$RELOAD" == true && "$DRY_RUN" == false ]]; then
  HA_HOST="${HA_HOST:-192.168.68.175}"
  if [[ -n "${HA_TOKEN:-}" ]]; then
    log "Reloading HA YAML via REST ..."
    curl -sf -X POST \
      -H "Authorization: Bearer $HA_TOKEN" \
      "http://${HA_HOST}:8123/api/services/homeassistant/reload_core_config" \
      && log "HA YAML reload requested" || log "WARN: REST reload failed"
  else
    log "Reloading HA via SSH ..."
    ssh -p "${HA_SSH_PORT:-22222}" -o StrictHostKeyChecking=no \
      "${HA_USER:-root}@${HA_HOST}" "ha core restart" \
      && log "HA core restart initiated" || log "WARN: HA restart failed"
  fi
fi

log "=== Maintenance done ==="
