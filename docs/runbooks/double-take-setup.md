# Double Take Setup Runbook

## What Double Take Does

Double Take sits between Frigate and HA. When Frigate detects a person:
1. Frigate sends a snapshot webhook to Double Take
2. Double Take runs the snapshot through a face recognizer (CompreFace, DeepStack, etc.)
3. Double Take publishes the result to MQTT
4. HA automation fires on the `double_take/match` MQTT topic

## Prerequisites
- Frigate running with person detection working
- MQTT broker running

## 1. Install Double Take Add-on

Add community repo if needed, then install Double Take.

## 2. Deploy Config

```bash
./scripts/sync-config.sh
```

Config lives at `config/double-take/config.yml` in this repo → `/config/double-take/config.yml` on host.

## 3. Configure Frigate Webhook

In `config/frigate/config.yml`, add:

```yaml
frigate:
  url: http://localhost:5000

mqtt:
  host: localhost

cameras:
  front_door:
    ...  # existing camera config
```

Double Take auto-discovers Frigate cameras when `frigate.url` is set.

## 4. Choose a Recognizer

| Recognizer | Notes |
|---|---|
| CompreFace | Open source, self-hosted, recommended |
| DeepStack | Easy Docker setup, good accuracy |
| AWS Rekognition | Cloud, paid, high accuracy |
| CodeProject.AI | Windows-friendly, local |

For a fully local setup, CompreFace or CodeProject.AI are best choices.

## 5. Train Known Faces

1. Open Double Take UI at `http://<ha-ip>:3000`
2. Navigate to **Train**
3. Upload labeled images per person
4. Confirm recognition is working against live snapshots

## 6. HA Automation on Match

```yaml
trigger:
  - platform: mqtt
    topic: double_take/match
    value_template: "{{ value_json.name }}"
condition: []
action:
  - service: notify.mobile_app
    data:
      message: "{{ trigger.payload_json.name }} identified at {{ trigger.payload_json.camera }}"
```
