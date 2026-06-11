# Danielsson Timeline — HAOS Add-on (scaffold)

Moves the Analytics / Environment UI from the Windows dev PC onto HAOS with Supervisor Ingress.

**Status:** scaffold only — not published to a community add-on repository yet.

## Prerequisites

1. Sync this repo to `/share/danielsson-insights/` on the HA host (scripts + events dirs).
2. Register this add-on in a local add-on repository or copy into `/addons/`.
3. Set `events_path` and `scripts_path` in the add-on configuration.

## Ingress

When enabled, HA sidebar **Analytics** can iframe `http://homeassistant.local:8123/api/hassio_ingress/<token>/timeline` instead of the dev PC IP.

See [docs/runbooks/timeline-addon.md](../../docs/runbooks/timeline-addon.md) for the full migration runbook.
