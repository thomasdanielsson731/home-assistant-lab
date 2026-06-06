#!/usr/bin/env bash
# Install mini-graph-card to HA www/community (HACS-compatible path).
# Run on HAOS host: bash /config/scripts/install-mini-graph-card.sh
# Or from dev PC via SSH (see install-mini-graph-card.ps1).

set -euo pipefail

VERSION="${MINI_GRAPH_VERSION:-v0.13.0}"
DEST="/config/www/community/mini-graph-card"
URL="https://github.com/kalkih/mini-graph-card/releases/download/${VERSION}/mini-graph-card-bundle.js"

mkdir -p "$DEST"
curl -fsSL "$URL" -o "${DEST}/mini-graph-card-bundle.js"
echo "Installed mini-graph-card ${VERSION} -> ${DEST}/mini-graph-card-bundle.js"
echo "Ensure lovelace resource is registered in configuration.yaml:"
echo "  url: /local/community/mini-graph-card/mini-graph-card-bundle.js"
