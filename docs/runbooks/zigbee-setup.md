# Zigbee (ZHA) Setup Runbook

ZHA on the HAOS host with a SONOFF ZigBee 3.0 USB Dongle Plus (CC2652P, "ZBDongle-P").

## Hardware

| Item | Value |
|---|---|
| Coordinator | SONOFF ZBDongle-P (TI CC2652P) |
| Connection | USB extension cable → HA host (Dell Latitude 3120) — extension reduces USB3/SSD interference |
| Device path | `/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_<serial>-if00-port0` |
| Radio type | ZNP · 115200 baud · no flow control |

## Setup (done 2026-06-10)

1. Plug dongle into HA host via the extension cable.
2. Verify detection: `ssh root@192.168.68.175 -p 22222 "ls /dev/serial/by-id/"`
3. If HA was running when the dongle was plugged in: `ha core restart`
   (the Core container does not always see hot-plugged USB devices).
4. HA auto-discovers the dongle and creates the ZHA entry — or run:

```bash
python scripts/setup_zha.py   # idempotent — exits if ZHA already configured
```

## Pairing devices

Settings → Devices & Services → ZHA → **Add device** — puts the network in
permit-join for 60 s. Pair near the coordinator first, then relocate.

Planned devices: Zigbee smoke detectors → `smoke` events in the timeline
(`event_normalizer.py` listens once entities exist).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `cannot_connect` in config flow | `ha core restart` — container lacks the hot-plugged device |
| Dongle missing from `/dev/serial/by-id/` | Re-seat USB; check `dmesg \| grep cp210x` on host |
| Port held by another process | `fuser /dev/ttyUSB0` — stop conflicting add-on (e.g. Z2M) |
| Weak mesh | Add mains-powered Zigbee devices as routers; keep dongle on extension away from USB3 ports |
