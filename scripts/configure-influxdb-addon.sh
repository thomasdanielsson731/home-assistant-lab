#!/bin/bash
# Configure InfluxDB HA add-on for LAN metrics bridge (auth off for bootstrap).
set -euo pipefail

SLUG="a0d7b954_influxdb"
TOKEN="${SUPERVISOR_TOKEN:-}"
if [ -z "$TOKEN" ] && [ -f /run/supervisor/token ]; then
  TOKEN=$(cat /run/supervisor/token)
fi
if [ -z "$TOKEN" ]; then
  echo "FAIL  SUPERVISOR_TOKEN not available"
  exit 1
fi

PAYLOAD='{"options":{"auth":false,"ssl":false,"reporting":true,"certfile":"fullchain.pem","keyfile":"privkey.pem","envvars":[]}}'

echo "Setting InfluxDB add-on options (auth=false, ssl=false)..."
RESP=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "http://supervisor/addons/${SLUG}/options")
BODY=$(echo "$RESP" | head -n -1)
CODE=$(echo "$RESP" | tail -n 1)
echo "  options HTTP $CODE"
echo "  $BODY"

if [ "$CODE" != "200" ]; then
  exit 1
fi

echo "Restarting InfluxDB add-on..."
curl -s -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  "http://supervisor/addons/${SLUG}/restart" | head -c 200
echo ""
echo "OK"
