# Face Recognition Integration

## Pipeline

```
Frigate (person snapshot) → Double Take → Recognizer → MQTT → HA Automation
```

## Recognizer Options

| Option | Hosting | Accuracy | Notes |
|---|---|---|---|
| CompreFace | Self-hosted | High | Open source, REST API |
| DeepStack | Self-hosted | Medium-High | Easy Docker setup |
| CodeProject.AI | Self-hosted | Medium-High | Windows-friendly |
| AWS Rekognition | Cloud | Very High | Paid, privacy tradeoff |

## Selected: CodeProject.AI (Phase 4)

**Decision:** [ADR-003](../../docs/decisions/003-face-recognizer.md) — CodeProject.AI on Windows dev PC.

`config/double-take/config.yml` already points to `http://192.168.68.118:32168`.

Install: https://www.codeproject.com/AI/docs/why/installing_on_windows.html

## Alternative: CompreFace

Use if CodeProject.AI accuracy is insufficient. Run via Docker on dev PC or separate host.

```bash
docker run -d \
  -p 8000:8000 \
  --name compreface \
  exadel/compreface:latest
```

## Training Data Guidelines

- Minimum 10 images per person, varied lighting and angles
- Use images at similar resolution to camera output
- Avoid heavily obscured faces (hats, sunglasses) in training set
- Retrain when accuracy degrades

## HA Entities Created by Double Take

After setup, Double Take exposes MQTT-based sensors in HA:
- `sensor.double_take_<name>` — last match confidence
- `binary_sensor.double_take_<name>` — whether person is currently detected

## Privacy Considerations

- All processing is local by default (no cloud)
- Training images are stored on the HA host under `/config/double-take/.storage/`
- GDPR: document what data is stored and for how long
