#!/bin/sh
# Configure and restart Cloudflared add-on on HAOS (when UI Configuration tab fails).
# Run on HA host: sh configure-cloudflared.sh
# Or via SSH: ssh root@192.168.68.175 -p 22222 'sh -s' < scripts/configure-cloudflared.sh

set -e
SLUG="${CLOUDFLARED_SLUG:-396f0234_cloudflared}"
HOSTNAME="${EXTERNAL_HOSTNAME:-ha.danielsson.cloud}"
INSIGHTS_HOSTNAME="${INSIGHTS_HOSTNAME:-insights.danielsson.cloud}"
INSIGHTS_SERVICE_HOST="${INSIGHTS_SERVICE_HOST:-192.168.68.175}"
TUNNEL_NAME="${TUNNEL_NAME:-haos-danielsson}"

if [ -z "$SUPERVISOR_TOKEN" ]; then
  echo "SUPERVISOR_TOKEN not set — run on HAOS (SSH add-on shell)"
  exit 1
fi

echo "Applying Cloudflared options for ${HOSTNAME}..."
curl -sf -X POST \
  -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"options\":{\"external_hostname\":\"${HOSTNAME}\",\"tunnel_name\":\"${TUNNEL_NAME}\",\"log_level\":\"info\",\"additional_hosts\":[{\"hostname\":\"${INSIGHTS_HOSTNAME:-insights.danielsson.cloud}\",\"service\":\"http://${INSIGHTS_SERVICE_HOST:-192.168.68.175}:8765\"}]}}" \
  "http://supervisor/addons/${SLUG}/options"

echo
echo "Restarting add-on..."
ha apps restart "${SLUG}"
sleep 5
ha apps info "${SLUG}" | grep -E '^state:|external_hostname|tunnel_name'
echo
echo "OAuth URL (open in browser, leave add-on running):"
ha apps logs "${SLUG}" 2>/dev/null | grep 'https://dash.cloudflare.com/argotunnel' | tail -1
