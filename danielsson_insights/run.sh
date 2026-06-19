#!/command/with-contenv bashio
# Danielsson Insights — timeline + normalizer + bridges on HAOS (host network).

SCRIPTS_PATH="$(bashio::config 'scripts_path')"
EVENTS_PATH="$(bashio::config 'events_path')"
REPO_ROOT="$(dirname "${SCRIPTS_PATH}")"

if [ ! -f "${SCRIPTS_PATH}/timeline_server.py" ]; then
  bashio::log.fatal "Missing ${SCRIPTS_PATH}/timeline_server.py — run deploy-insights-to-ha.ps1"
  exit 1
fi

mkdir -p "${EVENTS_PATH}"

ENV_FILE="${REPO_ROOT}/.env"
cat > "${ENV_FILE}" <<EOF
HA_HOST=$(bashio::config 'mqtt_host')
MQTT_USER=$(bashio::config 'mqtt_user')
MQTT_PASS=$(bashio::config 'mqtt_password')
CAM_USER=$(bashio::config 'cam_user')
CAM_PASS=$(bashio::config 'cam_password')
AXIS_ROOT_PASSWORD=$(bashio::config 'axis_root_password')
HA_TOKEN=$(bashio::config 'ha_token')
FRIGATE_URL=http://$(bashio::config 'mqtt_host'):5000
INFLUX_URL=$(bashio::config 'influx_url')
INFLUX_USER=$(bashio::config 'influx_user')
INFLUX_PASSWORD=$(bashio::config 'influx_password')
INFLUX_DB=$(bashio::config 'influx_db')
INFLUX_V2=$(bashio::config 'influx_v2')
INDOOR_TEMP_ENTITIES=$(bashio::config 'indoor_temp_entities')
EOF
if [ -n "${INDOOR_TEMP_ENTITIES}" ]; then
  echo "INDOOR_TEMP_ENTITIES=${INDOOR_TEMP_ENTITIES}" >> "${ENV_FILE}"
fi
chmod 600 "${ENV_FILE}"

export PYTHONPATH="${SCRIPTS_PATH}${PYTHONPATH:+:${PYTHONPATH}}"
cd "${REPO_ROOT}" || exit 1

start_bg() {
  local name="$1"
  local script="$2"
  bashio::log.info "Starting ${name}"
  python3 "${SCRIPTS_PATH}/${script}" &
}

if bashio::config 'enable_bridges'; then
  start_bg "event_normalizer" "event_normalizer.py"
  start_bg "bridge_watchdog" "bridge_watchdog.py"
  start_bg "air_quality_bridge" "air_quality_bridge.py"
  start_bg "audio_bridge" "audio_bridge.py"
  start_bg "aoa_bridge" "aoa_bridge.py"
  start_bg "insights_counters_bridge" "insights_counters_bridge.py"  # MQTT danielsson/insights/*_24h
  if bashio::config.has_value 'influx_url'; then
    start_bg "influx_metrics_bridge" "influx_metrics_bridge.py"
  fi
  start_bg "baseline_engine" "baseline_engine.py --loop"
fi

bashio::log.info "Starting timeline_server on :8765"
exec python3 "${SCRIPTS_PATH}/timeline_server.py"
