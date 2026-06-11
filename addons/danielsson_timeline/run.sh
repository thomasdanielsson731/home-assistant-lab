#!/usr/bin/with-contenv bashio
# Danielsson Timeline add-on — runs timeline_server.py from synced repo copy.
# Sync repo to /share/danielsson-insights/ before enabling (see docs/runbooks/timeline-addon.md).

SCRIPTS_PATH="$(bashio::config 'scripts_path')"
EVENTS_PATH="$(bashio::config 'events_path')"

if [ ! -f "${SCRIPTS_PATH}/timeline_server.py" ]; then
  bashio::log.fatal "timeline_server.py not found at ${SCRIPTS_PATH}"
  exit 1
fi

mkdir -p "${EVENTS_PATH}"
export PYTHONPATH="${SCRIPTS_PATH}:${PYTHONPATH}"

bashio::log.info "Starting timeline server from ${SCRIPTS_PATH}"
cd "${SCRIPTS_PATH}/.." || exit 1
exec python3 "${SCRIPTS_PATH}/timeline_server.py"
