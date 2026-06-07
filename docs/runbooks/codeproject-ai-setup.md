# CodeProject.AI Setup Runbook (Phase 4)

Face recognizer for Double Take. Decision: [ADR-003](../decisions/003-face-recognizer.md).

## Architecture

```
Frigate (person snapshot) → Double Take → CodeProject.AI :32168 → MQTT → HA
```

Double Take config: `config/double-take/config.yml` → `detectors.codeproject.url` = dev PC (`DEV_PC_HOST` in `.env`).

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

Ensure `detectors.codeproject.url` uses current dev PC IP (`192.168.68.136`).

Restart Double Take add-on: HA → Add-ons → Double Take → Restart.

Check Double Take logs for detector connection errors.

## 4. Train faces

1. Open Double Take UI: `http://192.168.68.175:3000`
2. **Train** → upload 10+ photos per person: Thomas, Nils, Hugo, Anna
3. Walk past `front` camera — verify match in UI

## 5. HA entities

After successful match, expect MQTT entities:

- `sensor.dt_<name>_confidence`
- `binary_sensor.dt_<name>_present`

## Troubleshooting

| Symptom | Fix |
|---|---|
| Port 32168 closed | Start CodeProject.AI service; check .NET 9 runtime |
| Double Take "detector error" | Wrong IP in `config.yml`; firewall block LAN → :32168 |
| No matches | Face module not running; need more training images |
| Works only when PC on | Expected — see ADR-003 tradeoffs |

## Related

- [double-take-setup.md](double-take-setup.md)
- [integrations/face-recognition/README.md](../../integrations/face-recognition/README.md)
