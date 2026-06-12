#!/bin/sh
# Merge InfluxDB options into Danielsson Insights add-on config (run on HA host).
# Usage: sh set_insights_influx_options.sh <influx_user> <influx_password>
SLUG=25d01a20_danielsson_insights
INFLUX_USER="${1:?usage: set_insights_influx_options.sh <user> <password>}"
INFLUX_PASSWORD="${2:?usage: set_insights_influx_options.sh <user> <password>}"

cur=$(curl -s -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  "http://supervisor/addons/${SLUG}/info" | jq '.data.options')

new=$(echo "$cur" | jq \
  --arg url "http://192.168.68.175:8086" \
  --arg user "$INFLUX_USER" \
  --arg pass "$INFLUX_PASSWORD" \
  '. + {influx_url: $url, influx_user: $user, influx_password: $pass, influx_db: "home_lab", influx_v2: false}')

curl -s -X POST \
  -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"options\": ${new}}" \
  "http://supervisor/addons/${SLUG}/options"
echo
