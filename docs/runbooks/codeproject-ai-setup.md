# CodeProject.AI Setup Runbook (Phase 4)

Face recognizer for Double Take. Decision: [ADR-003](../decisions/003-face-recognizer.md).

## Architecture

```
Frigate (person snapshot) → Double Take → CodeProject.AI :32168 → MQTT → HA
```

Double Take config: `config/double-take/config.yml` → `detectors.deepstack.url` = CodeProject.AI on dev PC (`DEV_PC_HOST`). Official Double Take 1.13 has no `codeproject` key — CPAI speaks the DeepStack face API.

## 1. Install on Windows dev PC

```powershell
.\scripts\install-codeproject-ai.ps1
```

Or manual:

1. Install [.NET 9 ASP.NET Runtime](https://dotnet.microsoft.com/download/dotnet/9.0) (required for CPAI 2.9.x)
2. Download [CodeProject.AI Windows x64 installer](https://codeproject.github.io/codeproject.ai/latest.html)
3. Run installer → installs Windows service
4. Open `http://localhost:32168` — dashboard should load

## 2. Enable Face Recognition module

1. Dashboard → **Modules** (or Module store)
2. Install / enable **Face Recognition** (not included in base Windows install)
3. Wait until module status is **Running**

Verify API:

```powershell
Invoke-WebRequest http://localhost:32168/v1/status/health -UseBasicParsing
```

## 3. Sync Double Take config

```powershell
.\scripts\sync-config.ps1
```

Ensure `detectors.deepstack.url` uses current dev PC IP (`192.168.68.136`).

**Windows Firewall:** allow inbound TCP **32168** from the HA subnet (or `192.168.68.175`). Without this, Double Take on HA cannot reach CPAI even when the dashboard works locally.

Restart Double Take add-on: HA → Add-ons → Double Take → Restart.

Check Double Take logs for detector connection errors.

## 4. Train faces

1. Open Double Take UI: `http://192.168.68.175:3000`
2. **Train** → create person → upload 10+ photos (tydligt ansikte, inte bara silhuett på avstånd)
3. Klicka **Train** efter uppladdning — DT skickar bilderna till CPAI (ingen manuell bounding-box)
4. Inkludera **varierade vinklar** i träningsbilder (profil, lätt nedåt) — CPAI hittar ofta inte ansikte om du tittar i telefon
5. Gå förbi **`front`** eller **`driveway_id`** — titta **mot kameran**, helst nära `driveway_id`

## 5. HA entities

After successful match, expect MQTT entities:

- `sensor.dt_<name>_confidence`
- `binary_sensor.dt_<name>_present`

## Troubleshooting

| Symptom | Fix |
|---|---|
| Port 32168 closed | Start CodeProject.AI service; check .NET 9 runtime |
| Double Take "detector error" | Wrong IP in `config.yml`; firewall block LAN → :32168 |
| `unexpected deepstack data` | CPAI returned `success: false` (no face in crop) — increase Frigate MQTT snapshot `height: 500` + `crop: true`; lower DT `detect.match.min_area` |
| `faces: []` after restart | CPAI face registry is in-memory — re-train in DT UI after every CPAI service restart |
| Training completes in &lt;2 s | CPAI unreachable — check firewall; training did not register |
| No matches | Face module not running; re-train; walk close to `front` / `driveway_id` |
| Works only when PC on | Expected — see ADR-003 tradeoffs |

Verify registry after training:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:32168/v1/vision/face/list
# expect: faces: ["thomas", ...]
```

## Related

- [double-take-setup.md](double-take-setup.md)
- [integrations/face-recognition/README.md](../../integrations/face-recognition/README.md)
