# Danielsson Insights — HAOS Add-on Runbook

**Goal:** Run the full analytics platform on HAOS 24/7 (no Windows dev PC bridges).

Add-on source: **`danielsson_insights/`** at repo root + Supervisor repository URL.

**Current version:** 0.2.4 — includes `influx_metrics_bridge`, Supervisor watchdog, Ingress-safe relative URLs.

Face recognition removed — [ADR-006](../decisions/006-no-face-no-companion-presence.md). No dev PC bridges required.

---

## Step 1 — Add repository in Supervisor

**Settings → Add-ons → Add-on store → ⋮ → Repositories**

```
https://github.com/thomasdanielsson731/home-assistant-lab
```

**Check for updates** → **Danielsson Home Lab Add-ons** → **Danielsson Insights**.

---

## Step 2 — Deploy scripts to HA share

From dev PC:

```powershell
.\scripts\deploy-insights-to-ha.ps1
```

Copies `scripts/` + `events/*.jsonl` to `/share/danielsson-insights/`.

---

## Step 3 — Install and configure add-on

1. Install **Danielsson Insights**.
2. Configure: MQTT password, camera password, `axis_root_password`, `ha_token`.
3. **InfluxDB (optional):** set `influx_url`, `influx_user`, `influx_password`, `influx_db` — or run on HA:

   ```bash
   sh /share/danielsson-insights/scripts/set_insights_influx_options.sh homelab <password>
   ```

4. Start add-on → verify `http://192.168.68.175:8765/timeline`.

---

## Step 4 — Dashboard URLs in secrets

**Recommended:** direct port (avoids Ingress 401 in iframe):

```powershell
.\scripts\deploy-insights-to-ha.ps1 -UseDirectSecrets
```

Writes:

```yaml
timeline_url: "http://192.168.68.175:8765/timeline"
environment_url: "http://192.168.68.175:8765/environment"
```

**Optional Ingress** (add-on sidebar panel only — not Lovelace iframe):

```powershell
.\scripts\deploy-insights-to-ha.ps1 -UseIngressSecrets
```

---

## Step 5 — Cut over from dev PC

```powershell
.\scripts\stop-bridges.ps1          # stop legacy dev PC processes
.\scripts\verify-insights-ha.ps1    # smoke test
```

Remove `HomeLab-Bridges` from Windows Startup if present.

---

## Enable Supervisor watchdog

Auto-restart if `/timeline` stops responding:

```bash
sh /share/danielsson-insights/scripts/enable_addon_watchdog.sh
```

Or via Supervisor API: `{"watchdog": true}` on add-on options.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Build fails: `lookup ghcr.io ... no such host` | `ha dns options --servers dns://1.1.1.1 --servers dns://8.8.8.8` |
| `s6-overlay-suexec: fatal` | `init: false` in `config.yaml` (included since 0.2.1) |
| Analytics/Environment **401** in dashboard | `-UseDirectSecrets` — not Ingress in iframe |
| Blank page, API errors | Redeploy scripts + restart add-on; check ingress regression tests |
| No Influx data | Set `influx_url` option; check logs for `Wrote N metric rows` |
| Ingress 404 | Re-run `-UseIngressSecrets` after add-on reinstall |

---

## Health check

```powershell
python scripts/health-check.py
.\scripts\verify-insights-ha.ps1
```

On HA:

```bash
ha apps info 25d01a20_danielsson_insights
ha apps logs 25d01a20_danielsson_insights
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.68.175:8765/timeline
```

---

## What runs inside the add-on

| Process | Role |
|---|---|
| `timeline_server.py` | Analytics + Environment UI + API (:8765) |
| `event_normalizer.py` | MQTT → events/metrics |
| `bridge_watchdog.py` | Heartbeat metrics |
| `air_quality_bridge.py` | D6210 → MQTT |
| `audio_bridge.py` | SPL WebSocket → MQTT |
| `aoa_bridge.py` | getOccupancy poll → MQTT |
| `influx_metrics_bridge.py` | metrics.jsonl → InfluxDB (if `influx_url` set) |
