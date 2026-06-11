# Timeline HAOS Add-on — Migration Runbook

**Goal:** Run `timeline_server.py` on the HA host with Supervisor Ingress so Analytics works 24/7 without the Windows dev PC.

**Status:** `addons/danielsson_insights/` + `scripts/deploy-insights-to-ha.ps1` — automated deploy.

---

## Why migrate

| Today (dev PC) | After add-on (HAOS) |
|---|---|
| `:8765` only when PC is on | Always on with HA |
| Firewall rule for LAN iframe | Ingress — same origin as HA |
| Bridges write `events/` locally | Sync or move normalizer to HA |

---

## Step 1 — Deploy from dev PC

```powershell
.\scripts\deploy-insights-to-ha.ps1 -UseIngressSecrets
```

Copies `scripts/` + `events/*.jsonl` to `/share/danielsson-insights/`, installs add-on to `/addons/danielsson_insights/`, sets Ingress URLs in `secrets.yaml`.

---

## Step 2 — Supervisor

1. **Settings → Add-ons → Add-on store** → add repository if needed (local `/addons` after deploy).
2. Install **Danielsson Insights** → configure MQTT + camera passwords + `ha_token` (long-lived token for presence fusion).
3. Start add-on → **Open Web UI** → `/timeline`.

---

## Step 3 — Cut over from dev PC

When HA add-on is stable:

1. Stop `start-bridges.ps1` services on dev PC (keep CodeProject.AI).
2. Ingress URLs already set by `-UseIngressSecrets`:
   - `/api/hassio_ingress/local_danielsson_insights/timeline`
   - `/api/hassio_ingress/local_danielsson_insights/environment`
3. Reload HA YAML + frontend.

---

## Event pipeline (full migration)

Add-on runs on HA host with `host_network: true`:

- `event_normalizer.py` — MQTT at `192.168.68.175:1883`
- Bridges — camera LAN IPs
- `timeline_server.py` — `:8765` + Ingress

---

## Health check

After migration, `scripts/health-check.py` should report:

- `timeline_server` heartbeat in `metrics.jsonl` (zone `_bridge/timeline_server`)
- Timeline UI on `127.0.0.1:8765` on HA host (or Ingress probe)

Bridge watchdog on dev PC can be stopped once all bridges run on HA.
