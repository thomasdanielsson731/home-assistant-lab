# Frigate Setup Runbook

## Prerequisites
- HAOS running
- Mosquitto MQTT add-on installed and running
- Axis camera IPs known

## 1. Add Frigate Repository

In HA: **Settings → Add-ons → Add-on Store → ⋮ → Repositories**

Add: `https://github.com/blakeblackshear/frigate-hass-addons`

## 2. Install Frigate Add-on

Install **Frigate** (not the beta unless intentional). Do not start yet.

## 3. Deploy Config

Copy `config/frigate/config.yml` to `/config/frigate/config.yml` on the HA host, or use sync script:

```bash
./scripts/sync-config.sh
```

## 4. Start Frigate

Start the add-on. Check logs for RTSP connection errors.

## 5. Verify Detection

Navigate to Frigate UI at `http://<ha-ip>:5000`. Confirm:
- Camera stream visible
- Bounding boxes appear on detected objects
- MQTT events arriving (check MQTT Explorer or HA Developer Tools → Events)

## 6. Add Frigate Integration to HA

**Settings → Devices & Services → Add Integration → Frigate**

Host: `127.0.0.1:5000`

## 7. Lovelace Card

Add the Frigate card via HACS → Frontend, then in your dashboard:

```yaml
type: custom:frigate-card
camera_entity: camera.front_door
```

## Troubleshooting

| Symptom | Check |
|---|---|
| Black camera feed | RTSP URL wrong or camera unreachable |
| No detections | `detect` FPS too low, wrong resolution, or model not loaded |
| High CPU | Lower detect FPS or reduce concurrent cameras |
| MQTT not receiving events | MQTT broker config in `config.yml` |
