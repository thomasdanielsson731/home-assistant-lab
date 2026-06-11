#!/usr/bin/env python3
"""Canonical zone IDs and HA Area → zone mapping for smoke detectors."""

from __future__ import annotations

# Timeline / metrics zone IDs (snake_case, Swedish room names)
SMOKE_ROOMS = ("kok", "vardagsrum", "hall")

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
    "hall_ground": "hall",
    "entré": "hall",
    "entre": "hall",
}


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
