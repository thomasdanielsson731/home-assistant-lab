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

## Recommended: CompreFace

Run alongside HAOS via a separate Docker host or VM, or as a HAOS add-on if a community image is available.

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
