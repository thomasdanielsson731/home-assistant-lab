# Timeline HAOS Add-on — Migration Runbook

**Goal:** Run `timeline_server.py` on the HA host with Supervisor Ingress so Analytics works 24/7 without the Windows dev PC.

Add-on source: **`repository.yaml`** + **`danielsson_insights/`** at **repo root** (required by Supervisor).

---

## Step 1 — Add repository in Supervisor

**Settings → Add-ons → Add-on store → ⋮ → Repositories**

Paste **exactly** this URL (nothing else — no spaces, no error text):

```
https://github.com/thomasdanielsson731/home-assistant-lab
```

If you see `Malformed input to a URL function`, the field contains extra characters — clear it and paste again.

Then **Check for updates** in the add-on store. You should see **Danielsson Home Lab Add-ons** → **Danielsson Insights**.

---

## Step 2 — Deploy scripts to HA share

From dev PC (before or after installing the add-on):

```powershell
.\scripts\deploy-insights-to-ha.ps1
```

Copies `scripts/` + `events/*.jsonl` to `/share/danielsson-insights/`.

---

## Step 3 — Install and configure add-on

1. Install **Danielsson Insights** from the new repository.
2. Configure: MQTT password, camera password, `axis_root_password`, `ha_token` (long-lived HA token for presence fusion).
3. Start add-on → **Open Web UI** → `/timeline`.

---

## Step 4 — Ingress URLs in secrets

After the add-on is installed:

```powershell
.\scripts\deploy-insights-to-ha.ps1 -UseIngressSecrets
```

This detects the app slug (e.g. `8915c73b_danielsson_insights`) and writes:

```yaml
timeline_url: "/api/hassio_ingress/<slug>/timeline"
environment_url: "/api/hassio_ingress/<slug>/environment"
```

---

## Step 5 — Cut over from dev PC

When the add-on is stable:

1. Stop `start-bridges.ps1` on dev PC (keep CodeProject.AI).
2. Reload HA frontend.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Build fails: `lookup ghcr.io ... no such host` | Set HA DNS: `ha dns options --servers dns://1.1.1.1 --servers dns://8.8.8.8` then retry install |
| `s6-overlay-suexec: fatal: can only run as pid 1` | Add `init: false` to `config.yaml` (included since 0.2.1), rebuild add-on |
| Ingress 404 | Re-run `deploy-insights-to-ha.ps1 -UseIngressSecrets` after add-on started |

---

## Health check

On HA host after cut-over:

- Add-on state: **started**
- Ingress opens `/timeline` and `/environment`
- `events/metrics.jsonl` receives `_bridge/*` heartbeats from `bridge_watchdog.py`
