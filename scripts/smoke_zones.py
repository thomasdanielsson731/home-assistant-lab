#!/usr/bin/env python3
"""Canonical zone IDs and HA Area → zone mapping for smoke detectors."""

from __future__ import annotations

# Timeline / metrics zone IDs (snake_case, Swedish room names)
SMOKE_ROOMS = ("kok", "vardagsrum", "hall")

# Default placement when areas not yet assigned (sorted IEEE → zone, HA area_id)
PLANNED_ROOM_ASSIGNMENTS: tuple[tuple[str, str], ...] = (
    ("kok", "kok"),
    ("vardagsrum", "living_room"),
    ("hall", "hall_ground_floor"),
)

# Friendly names in HA device registry (logical room, not physical location)
ZONE_DEVICE_LABELS: dict[str, str] = {
    "kok": "Brandvarnare kök",
    "vardagsrum": "Brandvarnare vardagsrum",
    "hall": "Brandvarnare hall",
}

# HA area_id or name fragment → canonical zone
AREA_TO_ZONE: dict[str, str] = {
    "kok": "kok",
    "kök": "kok",
    "kitchen": "kok",
    "kitchen_living_room": "kok",
    "kitchen___living_room": "kok",
    "matplats": "kok",
    "vardagsrum": "vardagsrum",
    "living_room": "vardagsrum",
    "living": "vardagsrum",
    "hall": "hall",
    "hall_ground_floor": "hall",
    "hall_nere": "hall",
    "hall_ground": "hall",
    "entré": "hall",
    "entre": "hall",
}


def is_heiman_smoke_device(dev_entities: list[dict]) -> bool:
    """True for HEIMAN HS1SA-E smoke detectors, not e.g. SONOFF water sensors."""
    ids = [e.get("entity_id", "") for e in dev_entities]
    if any("snzb" in e for e in ids):
        return False
    return any("heiman" in e for e in ids)


def find_smoke_alarm_entity(dev_entities: list[dict]) -> dict | None:
    """Primary smoke binary_sensor — ias_zon or heiman_hs1sa_e_plus (kök variant)."""
    for ent in dev_entities:
        eid = ent.get("entity_id", "")
        if eid.startswith("binary_sensor.") and "heiman" in eid and "ias" in eid:
            return ent
    for ent in dev_entities:
        if ent.get("entity_id") == "binary_sensor.heiman_hs1sa_e_plus":
            return ent
    return None


def zone_for_area(area_id: str | None, *, device_name: str | None = None) -> str:
    """Map HA area_id (or device name hint) to canonical smoke zone."""
    for raw in (area_id, device_name):
        if not raw:
            continue
        key = raw.strip().lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
        if key in AREA_TO_ZONE:
            return AREA_TO_ZONE[key]
        for fragment, zone in AREA_TO_ZONE.items():
            if fragment in key:
                return zone
    return "room"
