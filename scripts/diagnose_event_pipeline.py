#!/usr/bin/env python3
"""Compare Frigate API events vs Insights timeline — find pipeline gaps."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from event_store import TZ  # noqa: E402
from timeline_api import event_summary_stats, load_events  # noqa: E402

HA_HOST = os.environ.get("HA_HOST", "192.168.68.175")
FRIGATE_URL = os.environ.get("FRIGATE_URL", f"http://{HA_HOST}:5000")
INSIGHTS_URL = os.environ.get("INSIGHTS_API", f"http://{HA_HOST}:8765/api/v1/events?hours=24")
EVENTS_PATH = Path(os.environ.get("EVENTS_PATH", Path(__file__).parent.parent / "events"))
TIMELINE_JSONL = EVENTS_PATH / "timeline.jsonl"


def frigate_counts(hours: int = 24) -> dict[str, int] | None:
    after = int((datetime.now(TZ) - timedelta(hours=hours)).timestamp())
    try:
        resp = requests.get(
            f"{FRIGATE_URL}/api/events",
            params={"after": after, "limit": 1000},
            timeout=15,
        )
        resp.raise_for_status()
        events = resp.json()
    except requests.RequestException as exc:
        print(f"Frigate API unreachable ({FRIGATE_URL}): {exc}")
        return None
    labels: dict[str, int] = {}
    for ev in events:
        label = ev.get("label") or "unknown"
        labels[label] = labels.get(label, 0) + 1
    return {"total": len(events), **labels}


def timeline_counts(hours: int = 24) -> dict[str, int]:
    try:
        resp = requests.get(INSIGHTS_URL, timeout=15)
        if resp.status_code == 200 and isinstance(resp.json(), list):
            events = resp.json()
        else:
            raise ValueError("API not list")
    except (requests.RequestException, ValueError, TypeError):
        events = load_events(hours=hours, timeline_path=TIMELINE_JSONL)
    stats = event_summary_stats(events)
    return {
        "total": len(events),
        "person": stats.get("person", 0),
        "vehicle": stats.get("vehicle", 0),
        "occupancy": stats.get("occupancy", 0),
        "environment": stats.get("environment", 0),
    }


def main() -> int:
    print("=== Event pipeline diagnosis ===\n")
    fg = frigate_counts()
    tl = timeline_counts()
    print("Insights timeline (24 h):")
    for k, v in tl.items():
        print(f"  {k}: {v}")
    if fg:
        print("\nFrigate API (24 h):")
        for k, v in fg.items():
            print(f"  {k}: {v}")
        person_fg = fg.get("person", 0)
        person_tl = tl.get("person", 0)
        if person_fg > 0 and person_tl == 0:
            print(
                "\nWARN  Frigate has person events but timeline has none — "
                "check event_normalizer MQTT (frigate/events) and add-on mqtt_host."
            )
            return 1
        if person_fg == 0 and person_tl == 0:
            print("\nOK    Quiet period — no Frigate person tracks in 24 h.")
    else:
        print("\nSKIP  Frigate API check failed.")
    print("\nTips:")
    print("  - Normalizer subscribes frigate/events on MQTT_HOST (add-on: mqtt_host option)")
    print("  - AOA PersonOccupancy end also writes person events (axis_aoa source)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
