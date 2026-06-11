#!/usr/bin/env python3
"""Assign HA Areas to smoke detectors, reconfigure incomplete ZHA interviews, sync .env."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ha_client import ws_call, ws_fire_and_forget, zha_end_devices, zha_network_devices  # noqa: E402
from smoke_zones import (  # noqa: E402
    PLANNED_ROOM_ASSIGNMENTS,
    SMOKE_ROOMS,
    ZONE_DEVICE_LABELS,
    zone_for_area,
)

ENV_PATH = Path(__file__).parent.parent / ".env"
PLANNED_AREA_IDS = {area_id for _, area_id in PLANNED_ROOM_ASSIGNMENTS}


def smoke_network_devices() -> list[dict]:
    return sorted(
        [d for d in zha_network_devices() if d.get("device_type") != "Coordinator"],
        key=lambda d: d["ieee"].lower(),
    )


def registry_id_for_ieee(ieee: str, entities: list[dict]) -> str | None:
    ieee_l = ieee.lower()
    for ent in entities:
        uid = (ent.get("unique_id") or "").split("-")[0].lower()
        if uid == ieee_l:
            return ent.get("device_id")
    return None


def assign_areas(dry_run: bool) -> None:
    """Ensure exactly one detector per planned HA Area (logical placement)."""
    entities = ws_call("config/entity_registry/list")
    devices = zha_end_devices()
    print(f"Logical placement: one detector per room ({', '.join(SMOKE_ROOMS)})")
    print("Physical swap later: move unit, then change its HA Area only.\n")

    covered = {d.get("area_id") for d in devices if d.get("area_id") in PLANNED_AREA_IDS}
    unassigned = [d for d in devices if d.get("area_id") not in PLANNED_AREA_IDS]

    for zone, area_id in PLANNED_ROOM_ASSIGNMENTS:
        if area_id in covered:
            dev = next(d for d in devices if d.get("area_id") == area_id)
            ieee = _device_ieee(dev["id"], entities) or dev["id"][:8]
            print(f"  {zone}: {ieee} already in {area_id}")
            continue
        if not unassigned:
            print(f"  {zone}: no unassigned device left for {area_id}")
            continue
        dev = unassigned.pop(0)
        ieee = _device_ieee(dev["id"], entities) or dev["id"][:8]
        print(f"  {zone}: {ieee} -> area {area_id}")
        if not dry_run:
            ws_call("config/device_registry/update", device_id=dev["id"], area_id=area_id)
        covered.add(area_id)


def _device_ieee(device_id: str, entities: list[dict]) -> str | None:
    for ent in entities:
        if ent.get("device_id") != device_id:
            continue
        uid = (ent.get("unique_id") or "").split("-")[0]
        if uid.count(":") >= 7:
            return uid.lower()
    return None


def label_devices(dry_run: bool) -> None:
    devices = zha_end_devices()
    print("\nDevice labels:")
    for dev in devices:
        zone = zone_for_area(dev.get("area_id"))
        if zone not in ZONE_DEVICE_LABELS:
            continue
        label = ZONE_DEVICE_LABELS[zone]
        if dev.get("name_by_user") == label:
            print(f"  {zone}: already '{label}'")
            continue
        print(f"  {zone}: -> '{label}'")
        if not dry_run:
            ws_call(
                "config/device_registry/update",
                device_id=dev["id"],
                name_by_user=label,
            )


def reconfigure_all(dry_run: bool, ieee_filter: str | None = None) -> None:
    network = smoke_network_devices()
    if ieee_filter:
        network = [d for d in network if ieee_filter.lower() in d["ieee"].lower()]
    print(f"Reconfiguring {len(network)} end device(s)...")
    for d in network:
        ieee = d["ieee"]
        print(f"  reconfigure {ieee}")
        if dry_run:
            continue
        ws_fire_and_forget("zha/devices/reconfigure", ieee=ieee)
        time.sleep(2)


def build_env_lines() -> tuple[str, str]:
    entities = ws_call("config/entity_registry/list")
    devices = {d["id"]: d for d in zha_end_devices()}
    smoke_parts: list[str] = []
    temp_parts: list[str] = []

    for ent in sorted(entities, key=lambda e: e["entity_id"]):
        dev = devices.get(ent.get("device_id"))
        if not dev:
            continue
        zone = zone_for_area(dev.get("area_id"), device_name=dev.get("name_by_user") or dev.get("name"))
        eid = ent["entity_id"]
        if eid.startswith("binary_sensor.") and "ias" in eid:
            smoke_parts.append(f"{eid.replace('binary_sensor.', '')}:{zone}")
        if eid.startswith("sensor.") and "temperatur" in eid and "heiman" in eid:
            temp_parts.append(f"{eid.replace('sensor.', '')}:{zone}")

    return ",".join(smoke_parts), ",".join(temp_parts)


def update_env_file(smoke: str, temp: str, dry_run: bool) -> None:
    if not ENV_PATH.exists():
        print("No .env file — skip update")
        return
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    seen_smoke = seen_temp = False
    for line in lines:
        if line.startswith("SMOKE_ENTITIES="):
            out.append(f"SMOKE_ENTITIES={smoke}" if smoke else line)
            seen_smoke = True
        elif line.startswith("INDOOR_TEMP_ENTITIES="):
            out.append(f"INDOOR_TEMP_ENTITIES={temp}" if temp else line)
            seen_temp = True
        else:
            out.append(line)
    if smoke and not seen_smoke:
        out.append(f"SMOKE_ENTITIES={smoke}")
    if temp and not seen_temp:
        out.append(f"INDOOR_TEMP_ENTITIES={temp}")
    if dry_run:
        print(f"Would write SMOKE_ENTITIES={smoke}")
        print(f"Would write INDOOR_TEMP_ENTITIES={temp}")
        return
    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("Updated .env")


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure HEIMAN smoke detectors in HA")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--assign-areas", action="store_true", default=True)
    parser.add_argument("--no-assign-areas", action="store_false", dest="assign_areas")
    parser.add_argument("--label", action="store_true", default=True, help="Set friendly device names")
    parser.add_argument("--no-label", action="store_false", dest="label")
    parser.add_argument("--reconfigure", action="store_true", help="ZHA re-interview end devices")
    parser.add_argument("--ieee", help="Reconfigure only devices matching this IEEE fragment")
    parser.add_argument("--wait", type=int, default=0, help="Seconds to wait after reconfigure")
    parser.add_argument("--update-env", action="store_true", help="Write SMOKE/INDOOR_TEMP to .env")
    args = parser.parse_args()

    if args.assign_areas:
        assign_areas(args.dry_run)
    if args.label:
        label_devices(args.dry_run)
    if args.reconfigure:
        print()
        reconfigure_all(args.dry_run, args.ieee)
        if args.wait and not args.dry_run:
            print(f"Waiting {args.wait}s for interviews...")
            time.sleep(args.wait)

    smoke, temp = build_env_lines()
    if smoke or temp:
        print("\nEntity map (zones follow HA Area, not physical location):")
        if smoke:
            print(f"  SMOKE_ENTITIES={smoke}")
        if temp:
            print(f"  INDOOR_TEMP_ENTITIES={temp}")
    if args.update_env:
        update_env_file(smoke, temp, args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
