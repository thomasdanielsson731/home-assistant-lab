#!/bin/sh
# Add insights.danielsson.cloud to Cloudflared tunnel (Danielsson Insights :8765).
set -e
SLUG="${CLOUDFLARED_SLUG:-396f0234_cloudflared}"
HOSTNAME="${EXTERNAL_HOSTNAME:-ha.danielsson.cloud}"
INSIGHTS_HOST="${INSIGHTS_HOSTNAME:-insights.danielsson.cloud}"
INSIGHTS_SERVICE="${INSIGHTS_SERVICE:-http://192.168.68.175:8765}"

if [ -z "$SUPERVISOR_TOKEN" ]; then
  echo "SUPERVISOR_TOKEN not set — run on HAOS (SSH add-on shell)"
  exit 1
fi

PAYLOAD=$(cat <<EOF
{"options":{"external_hostname":"${HOSTNAME}","log_level":"info","additional_hosts":[{"hostname":"${INSIGHTS_HOST}","service":"${INSIGHTS_SERVICE}"}]}}
EOF
)

echo "Applying Cloudflared additional_hosts: ${INSIGHTS_HOST} -> ${INSIGHTS_SERVICE}"
curl -sf -X POST \
  -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" \
  "http://supervisor/addons/${SLUG}/options"

echo
echo "Restarting Cloudflared..."
ha apps restart "${SLUG}"
sleep 6
ha apps info "${SLUG}" | sed -n '/^options:/,/^[a-z]/p'
