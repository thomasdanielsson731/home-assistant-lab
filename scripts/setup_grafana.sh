#!/bin/sh
# Provision Grafana datasource + 7-day dashboard on HAOS (share + add-on env).
# Run on HA via SSH add-on (needs SUPERVISOR_TOKEN + jq).
#
# Usage: sh setup_grafana.sh <influx_user> <influx_password>
set -eu

SLUG="a0d7b954_grafana"
INFLUX_USER="${1:?usage: setup_grafana.sh <influx_user> <influx_password>}"
INFLUX_PASSWORD="${2:?usage: setup_grafana.sh <influx_user> <influx_password>}"

if [ -z "${SUPERVISOR_TOKEN:-}" ]; then
  echo "FAIL  SUPERVISOR_TOKEN not set (run via HA SSH add-on)"
  exit 1
fi

ROOT="/share/grafana"
mkdir -p "${ROOT}/provisioning/datasources" \
         "${ROOT}/provisioning/dashboards" \
         "${ROOT}/dashboards" \
         "${ROOT}/data"

cat > "${ROOT}/provisioning/datasources/influx.yaml" <<EOF
apiVersion: 1
datasources:
  - name: Home Lab InfluxDB
    uid: homelab-influx
    type: influxdb
    access: proxy
    url: http://a0d7b954-influxdb:8086
    database: home_lab
    user: ${INFLUX_USER}
    jsonData:
      httpMode: GET
    secureJsonData:
      password: ${INFLUX_PASSWORD}
EOF
chmod 600 "${ROOT}/provisioning/datasources/influx.yaml"

if [ -f "${ROOT}/provisioning/dashboards/default.yaml" ]; then
  :
elif [ -f /share/danielsson-insights/scripts/../config/grafana/provisioning/dashboards/default.yaml ]; then
  cp /share/danielsson-insights/config/grafana/provisioning/dashboards/default.yaml \
    "${ROOT}/provisioning/dashboards/default.yaml"
else
  cat > "${ROOT}/provisioning/dashboards/default.yaml" <<'YAML'
apiVersion: 1
providers:
  - name: homelab
    orgId: 1
    folder: Home Lab
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /share/grafana/dashboards
YAML
fi

if [ ! -f "${ROOT}/dashboards/home-metrics-7d.json" ]; then
  echo "WARN  missing ${ROOT}/dashboards/home-metrics-7d.json — run deploy-grafana.ps1 first"
fi

cur=$(curl -s -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  "http://supervisor/addons/${SLUG}/info" | jq '.data.options')

new=$(echo "$cur" | jq '
  .env_vars = (
    [.env_vars[]? | select(.name != "GF_PATHS_PROVISIONING" and .name != "GF_PATHS_DATA")] +
    [
      {"name": "GF_PATHS_PROVISIONING", "value": "/share/grafana/provisioning"}
    ]
  )
')

echo "Updating Grafana add-on options..."
code=$(curl -s -o /tmp/grafana_opts.json -w '%{http_code}' -X POST \
  -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"options\": ${new}}" \
  "http://supervisor/addons/${SLUG}/options")
echo "  options HTTP ${code}"
cat /tmp/grafana_opts.json
echo

if [ "$code" != "200" ]; then
  exit 1
fi

echo "Restarting Grafana..."
curl -s -X POST \
  -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  "http://supervisor/addons/${SLUG}/restart" | head -c 200
echo
echo "OK  Grafana provisioning applied"
