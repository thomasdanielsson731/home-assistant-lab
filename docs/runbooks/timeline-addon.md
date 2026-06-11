# Timeline HAOS Add-on — Migration Runbook

**Goal:** Run `timeline_server.py` on the HA host with Supervisor Ingress so Analytics works 24/7 without the Windows dev PC.

**Status:** scaffold in `addons/danielsson_timeline/` — manual registration required.

---

## Why migrate

| Today (dev PC) | After add-on (HAOS) |
|---|---|
| `:8765` only when PC is on | Always on with HA |
| Firewall rule for LAN iframe | Ingress — same origin as HA |
| Bridges write `events/` locally | Sync or move normalizer to HA |

---

## Step 1 — Sync repo to HA share

```bash
# From dev PC (PowerShell) — one-time copy of scripts + empty events dir
scp -P 22222 -r scripts root@192.168.68.175:/share/danielsson-insights/
ssh root@192.168.68.175 -p 22222 "mkdir -p /share/danielsson-insights/events"
```

Ongoing: extend `sync-config.ps1` or a dedicated task to rsync `events/` if normalizer stays on dev PC.

---

## Step 2 — Register local add-on

1. Copy `addons/danielsson_timeline/` to the HA add-ons git repo or use **Local add-ons** in Supervisor.
2. Rebuild the add-on image from Supervisor → Add-on store → Local add-ons.
3. Configure:
   - `scripts_path`: `/share/danielsson-insights/scripts`
   - `events_path`: `/share/danielsson-insights/events`

---

## Step 3 — Enable Ingress

1. Start the add-on (boot: manual until verified).
2. Open the add-on **Open Web UI** — should show `/timeline`.
3. Update `config/home-assistant/dashboards/house-timeline.yaml` iframe URL to Ingress path (or use the built-in Ingress panel).

---

## Step 4 — Event pipeline

**Option A (minimal):** Keep `event_normalizer.py` on dev PC; rsync `events/timeline.jsonl` + `metrics.jsonl` to HA every minute.

**Option B (full):** Run normalizer on HA (MQTT is local to Mosquitto) — retire dev PC bridges except CodeProject.AI.

---

## Health check

After migration, `scripts/health-check.py` should report:

- `timeline_server` heartbeat in `metrics.jsonl` (zone `_bridge/timeline_server`)
- Timeline UI on `127.0.0.1:8765` on HA host (or Ingress probe)

Bridge watchdog on dev PC can be stopped once all bridges run on HA.
