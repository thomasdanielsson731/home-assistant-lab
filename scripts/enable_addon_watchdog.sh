#!/bin/sh
# Enable Supervisor watchdog (auto-restart) for Danielsson Insights add-on.
# Run on the HA host: sh enable_addon_watchdog.sh
SLUG=25d01a20_danielsson_insights
curl -s -X POST \
  -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"watchdog": true}' \
  "http://supervisor/addons/${SLUG}/options"
echo
ha apps info "$SLUG" | grep -E 'watchdog|state'
