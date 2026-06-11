# Zigbee (ZHA) Setup Runbook

> **Status (2026-06-11):** 3× HEIMAN — **en per rum** (kök, vardagsrum, hall) som logisk placering. Fysisk montering/swap senare: flytta enheten, ändra bara **Area** i HA, kör `configure_smoke_detectors.py --update-env`.

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

### Live devices (2026-06-11)

| # | IEEE | Alarm entity | Notes |
|---|---|---|---|
| 1 | `cc:36:bb:ff:fe:d9:0b:c5` | *(pending — reconfigure + wake button)* | Area: kök |
| 2 | `cc:36:bb:ff:fe:d9:0e:76` | `binary_sensor.heiman_hs1sa_e_plus_ias_zon_2` | Area: vardagsrum |
| 3 | `cc:36:bb:ff:fe:d9:0e:99` | `binary_sensor.heiman_hs1sa_e_plus_ias_zon` | Area: hall |

Battery: `sensor.heiman_hs1sa_e_plus_batteri_3` · Temp: `sensor.heiman_hs1sa_e_plus_temperatur_3`

**Temperature:** each HEIMAN reports room temp (~0.5°C resolution). Used for:
- HA `sensor.house_indoor_temperature` (average) + Security/Rooms dashboard
- `metrics.jsonl` → Environment chart (inne vs ute) via `INDOOR_TEMP_ENTITIES` in `.env`

```powershell
python scripts/probe_smoke_entities.py   # suggested SMOKE_ENTITIES + device status
python scripts/configure_smoke_detectors.py --reconfigure --wait 45 --update-env
```

`configure_smoke_detectors.py` ensures one detector per planned Area, sets friendly names (`Brandvarnare kök` …), re-interviews incomplete devices, and updates `.env`.

### Logical vs physical placement

| Zone | HA Area | Friendly name |
|---|---|---|
| `kok` | Kök | Brandvarnare kök |
| `vardagsrum` | Living room | Brandvarnare vardagsrum |
| `hall` | Hall (Ground Floor) | Brandvarnare hall |

**Montering behövs inte för att systemet ska fungera.** Enheterna kan ligga på bordet i “fel” rum tills hållare monteras — byt fysiskt när du vill, uppdatera Area i HA, kör `--update-env`.

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
SMOKE_ENTITIES=heiman_hs1sa_e_plus_ias_zon_2:kok,heiman_hs1sa_e_plus_ias_zon_3:vardagsrum,heiman_hs1sa_e_plus_ias_zon_4:hall
```

Adjust entity suffixes and zones to match what HA created. Restart bridges: `.\scripts\start-bridges.ps1`

Also set indoor temperature map (same zones):

```
INDOOR_TEMP_ENTITIES=heiman_hs1sa_e_plus_temperatur_3:kok,...
```
