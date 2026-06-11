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

Or from dev PC:

```powershell
python scripts/setup_zha.py --permit   # open join for 254 s
python scripts/setup_zha.py --list     # show network devices
```

### Live device (2026-06-10)

| Item | Value |
|---|---|
| Model | HEIMAN HS1SA-E-PLUS (smoke + siren) |
| IEEE | `cc:36:bb:ff:fe:d9:0b:c5` |
| Alarm entity | `binary_sensor.heiman_hs1sa_e_plus` |
| Battery | `sensor.heiman_hs1sa_e_plus_batteri` |
| Timeline zone | `kitchen` (via `SMOKE_ENTITIES` in `.env`) |

Failed duplicate interviews (`…0e:76`, `…0e:99`) can be removed:

```powershell
python scripts/setup_zha.py --remove-ghosts
```

Assign an **Area** in HA (e.g. Kitchen) for clearer dashboard labels.

Planned: more smoke detectors → extend `SMOKE_ENTITIES=entity_suffix:zone,...`

## Troubleshooting

| Symptom | Fix |
|---|---|
| `cannot_connect` in config flow | `ha core restart` — container lacks the hot-plugged device |
| `NWK_NO_ROUTE` on Identify/button | Battery device asleep — wake with short button press; often no visible response on HEIMAN |
| Dongle missing from `/dev/serial/by-id/` | Re-seat USB; check `dmesg \| grep cp210x` on host |
| Port held by another process | `fuser /dev/ttyUSB0` — stop conflicting add-on (e.g. Z2M) |
| Weak mesh | Add mains-powered Zigbee devices as routers; keep dongle on extension away from USB3 ports |
| Messy pairing / ghosts / start over | Full reset below |

## Full reset (clean slate)

Wipes the Zigbee network and all paired devices in HA. **Physical detectors must also be factory-reset** or they will not re-join cleanly.

### 1. Factory-reset each HEIMAN (all three)

Hold the button **~10 seconds** until the LED pattern changes (see manual). Do all three before re-pairing.

### 2. Reset ZHA on the host

```powershell
python scripts/setup_zha.py --reset --yes
```

This removes the ZHA integration, deletes `/config/zigbee.db*`, restarts HA core, and creates a new network.

### 3. Pair one detector at a time

Place **one** detector next to the dongle (same room as the HA PC):

```powershell
python scripts/setup_zha.py --permit
```

Hold pairing button **~5 s** on detector #1 → wait until it appears in ZHA → assign Area → mount in ceiling.

Repeat for #2 and #3 (permit → pair → wait → next).

### 4. Update smoke entity map

After all three are in HA, set in `.env`:

```
SMOKE_ENTITIES=heiman_hs1sa_e_plus:kitchen,heiman_hs1sa_e_plus_2:hall,heiman_hs1sa_e_plus_3:sovrum
```

Adjust entity suffixes and zones to match what HA created. Restart bridges: `.\scripts\start-bridges.ps1`
