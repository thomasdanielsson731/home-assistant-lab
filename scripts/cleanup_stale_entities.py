#!/usr/bin/env python3
"""List stale HA entities to remove after ADR-006 / REST sensor migration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

HA_HOST = os.environ.get("HA_HOST", "192.168.68.175")
TOKEN = os.environ.get("HA_TOKEN")
if not TOKEN:
    sys.exit("HA_TOKEN not set in .env")

BASE = f"http://{HA_HOST}:8123/api"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

STALE_PREFIXES = (
    "sensor.dt_",
    "binary_sensor.dt_",
    "sensor.insights_events_24h_2",
    "sensor.insights_persons_24h_2",
    "sensor.insights_arrivals_24h_2",
    "sensor.insights_deliveries_24h_2",
    "sensor.insights_bicycles_24h_2",
)


def main() -> int:
    resp = requests.get(f"{BASE}/states", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    states = resp.json()
    stale = [
        s["entity_id"]
        for s in states
        if any(s["entity_id"].startswith(p) or s["entity_id"] == p for p in STALE_PREFIXES)
    ]
    if not stale:
        print("No stale entities found.")
        return 0
    print("Remove in Settings → Devices & services → Entities:\n")
    for eid in sorted(stale):
        print(f"  - {eid}")
    print(f"\nTotal: {len(stale)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
