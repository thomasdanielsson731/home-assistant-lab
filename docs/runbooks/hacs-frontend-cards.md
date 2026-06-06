# HACS Frontend Cards Runbook

Required custom Lovelace cards for the Home Lab dashboard.

## Installed Cards

| Card | HACS name | Resource URL | Used in |
|---|---|---|---|
| Mushroom Cards | Mushroom | `/hacsfiles/lovelace-mushroom/...` | All views |
| Advanced Camera Card | Advanced Camera Card | `/hacsfiles/advanced-camera-card/...` | Cameras |
| mini-graph-card | mini-graph-card | `/hacsfiles/mini-graph-card/mini-graph-card-bundle.js` | Home → env graphs |

Resources are declared in `configuration.yaml` under `lovelace: resources:` (synced from repo).

## Install mini-graph-card

### Option A — Script (recommended)

From Windows dev PC:

```powershell
.\scripts\install-mini-graph-card.ps1
.\scripts\sync-config.ps1
```

Then **Developer Tools → YAML → Reload all YAML configuration** and hard-refresh the browser (Ctrl+F5).

### Option B — HACS UI

1. **HACS → Frontend**
2. Search **mini-graph-card** (author: Karlis Lukes)
3. **Download** → **Reload** frontend (or restart HA)

### Option C — HAOS SSH

```bash
bash /config/scripts/install-mini-graph-card.sh
```

## Verify

1. Open **Home Lab → Home**
2. Scroll to **LAST 7 DAYS** — five sparkline cards (no "Configuration error")
3. **LAST 90 DAYS** — aggregated 6 h buckets (`points_per_hour: 0.1667`, `group_by: interval`)

## Troubleshooting

| Symptom | Fix |
|---|---|
| Configuration error on all mini-graph cards | Resource missing — check `configuration.yaml` + bundle file exists under `www/community/mini-graph-card/` |
| 90-day graphs empty | Recorder needs time; `purge_keep_days: 90` in `configuration.yaml` |
| Stale card after update | Ctrl+F5 or reinstall bundle via script |

## 90-day graph config note

`group_by` must be a **string** (`interval`, `hour`, `date`) — not a YAML object. Six-hour buckets: `points_per_hour: 0.1667` (= 1/6).
