---
name: Camera issue
about: Problem with a specific camera stream, detection, or recording
labels: camera
---

## Camera

- Zone ID: <!-- front / driveway_wide / driveway_id / backyard / storage_ext / storage_int -->
- Model:
- IP:

## Issue type

- [ ] Stream not connecting (RTSP error)
- [ ] Detection not working (no events)
- [ ] Recording not writing to SSD
- [ ] Face recognition not triggering
- [ ] Wrong zone / incorrect detection area

## Description

<!-- What is happening? When did it start? -->

## Frigate logs

```
Paste Frigate add-on log output here
```

## RTSP test result

```bash
# Run from HA host SSH:
ffprobe rtsp://user:pass@<ip>/axis-media/media.amp
# Paste output:
```
