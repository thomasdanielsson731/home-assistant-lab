#!/usr/bin/env python3
"""List ZHA smoke detector entities and IEEE addresses from HA registries."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from websocket import create_connection

sys.path.insert(0, str(Path(__file__).parent))
from smoke_zones import SMOKE_ROOMS, zone_for_area  # noqa: E402

load_dotenv(Path(__file__).parent.parent / ".env")

HOST = os.environ.get("HA_HOST", "192.168.68.175")
TOKEN = os.environ.get("HA_TOKEN")
if not TOKEN:
    sys.exit("HA_TOKEN not set in .env")

BASE = f"http://{HOST}:8123/api"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
WS_URI = f"ws://{HOST}:8123/api/websocket"


def ws_call(msg_type: str, **extra):
    ws = create_connection(WS_URI, timeout=30)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    ws.recv()
    ws.send(json.dumps({"id": 1, "type": msg_type, **extra}))
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == 1:
            if not data.get("success", True):
                raise RuntimeError(data.get("error"))
            ws.close()
            return data.get("result")


def main() -> int:
    devices = ws_call("config/device_registry/list")
    entities = ws_call("config/entity_registry/list")

    zha_entry = next(
        (e["entry_id"] for e in requests.get(f"{BASE}/config/config_entries/entry", headers=HEADERS, timeout=15).json()
         if e["domain"] == "zha"),
        None,
    )
    zha_devices = [
        d for d in devices
        if d.get("config_entries") and zha_entry in d.get("config_entries", [])
        and (d.get("name") or "").lower() != "texas instruments cc2652"
        and "coordinator" not in (d.get("name") or "").lower()
    ]

    print(f"ZHA end devices: {len(zha_devices)}\n")
    for dev in zha_devices:
        name = dev.get("name_by_user") or dev.get("name") or "?"
        area = dev.get("area_id") or "unassigned"
        dev_id = dev["id"]
        print(f"Device: {name}  area={area}  id={dev_id[:8]}…")

        dev_entities = [e for e in entities if e.get("device_id") == dev_id]
        alarm = next(
            (e for e in dev_entities if e["entity_id"].startswith("binary_sensor.") and "ias" in e["entity_id"]),
            None,
        )
        battery = next(
            (e for e in dev_entities if e["entity_id"].startswith("sensor.") and "batteri" in e["entity_id"]),
            None,
        )
        temp = next(
            (e for e in dev_entities if e["entity_id"].startswith("sensor.") and "temperatur" in e["entity_id"]),
            None,
        )
        if alarm:
            uid = alarm.get("unique_id") or ""
            ieee = uid.split("-")[0] if uid else "?"
            suffix = alarm["entity_id"].replace("binary_sensor.", "")
            print(f"  alarm:   {alarm['entity_id']}  ieee={ieee}")
            print(f"  map key: {suffix}")
        else:
            print("  alarm:   (missing — still configuring?)")
        if battery:
            print(f"  battery: {battery['entity_id']}")
        if temp:
            print(f"  temp:    {temp['entity_id']}")
        print(f"  zone:    {zone_for_area(dev.get('area_id'), device_name=name)}")
        print()

    smoke_parts: list[str] = []
    temp_parts: list[str] = []
    for dev in zha_devices:
        dev_entities = [e for e in entities if e.get("device_id") == dev["id"]]
        alarm = next(
            (e for e in dev_entities if e["entity_id"].startswith("binary_sensor.") and "ias" in e["entity_id"]),
            None,
        )
        temp = next(
            (e for e in dev_entities if e["entity_id"].startswith("sensor.") and "temperatur" in e["entity_id"]),
            None,
        )
        zone = zone_for_area(dev.get("area_id"), device_name=dev.get("name_by_user") or dev.get("name"))
        if alarm:
            suffix = alarm["entity_id"].replace("binary_sensor.", "")
            smoke_parts.append(f"{suffix}:{zone}")
        if temp:
            temp_suffix = temp["entity_id"].replace("sensor.", "")
            temp_parts.append(f"{temp_suffix}:{zone}")

    if smoke_parts:
        print(f"Canonical zones: {', '.join(SMOKE_ROOMS)} (kök, vardagsrum, hall)")
        print("Zones follow HA Area. Swap detectors physically anytime — just update Area.\n")
        print("Suggested SMOKE_ENTITIES:")
        print("SMOKE_ENTITIES=" + ",".join(smoke_parts))
    if temp_parts:
        print("INDOOR_TEMP_ENTITIES=" + ",".join(temp_parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
