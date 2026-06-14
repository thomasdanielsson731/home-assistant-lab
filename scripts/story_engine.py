#!/usr/bin/env python3
"""
Danielsson Home Intelligence — House Story Engine (Phase 6).

Converts raw timeline events into a human-readable daily narrative.

Usage:
  python scripts/story_engine.py               # generate today's story
  python scripts/story_engine.py 2026-06-06    # generate for a specific date

Stories are written to events/stories/<date>.json and served via
timeline_server.py at /api/v1/story/today and /api/v1/story/<date>.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from event_store import TZ  # noqa: E402
from timeline_api import load_events  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent
STORIES_DIR = REPO_ROOT / "events" / "stories"

log = logging.getLogger("story_engine")

# ── Beat grouping window ───────────────────────────────────────────────────
BEAT_WINDOW_SEC = 300  # 5-minute windows


# ── Prose templates ────────────────────────────────────────────────────────

def _duration_str(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)} seconds"
    if seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    return f"{seconds / 3600:.1f} hours"


def _zone_label(zone: str) -> str:
    return {
        "front": "the front entrance",
        "driveway": "the driveway",
        "driveway_wide": "the driveway",
        "driveway_id": "the driveway",
        "backyard": "the backyard",
        "storage_ext": "the storage building",
        "storage_int": "the storage building",
        "driveway_env": "outside",
    }.get(zone, zone.replace("_", " "))


def _generate_beat_text(events_in_window: list[dict]) -> str | None:
    """Generate a single prose sentence for a group of events."""
    if not events_in_window:
        return None

    types = [e["type"] for e in events_in_window]
    first = events_in_window[0]
    zone = first.get("location", {}).get("zone", "")
    zone_label = _zone_label(zone)

    # Arrival (enriched) — highest priority
    arrivals = [e for e in events_in_window if e["type"] == "arrival"]
    if arrivals:
        ev = arrivals[0]
        name = (ev.get("identity") or {}).get("name", "Someone")
        if name and name != "Someone":
            return f"{name} arrived home."
        return "Someone arrived home."

    # Delivery
    deliveries = [e for e in events_in_window if e["type"] == "delivery"]
    if deliveries:
        return f"A delivery was detected at {zone_label}."

    # Bicycle arrival
    bicycles = [e for e in events_in_window if e["type"] == "bicycle"]
    if bicycles:
        ev = bicycles[0]
        name = (ev.get("identity") or {}).get("name", "Someone")
        return f"{name} arrived by bicycle at {zone_label}."

    # Door event
    doors = [e for e in events_in_window if e["type"] == "door"]
    if doors:
        ev = doors[0]
        action = (ev.get("metadata") or {}).get("action", "opened")
        return f"Front door {action}."

    # Behavior (scene track classification)
    behaviors = [e for e in events_in_window if e["type"] == "behavior"]
    if behaviors:
        ev = behaviors[0]
        meta = ev.get("metadata") or {}
        behavior = meta.get("behavior", "present")
        dur = meta.get("duration_seconds", 0)
        obj = meta.get("obj_type", "object")
        is_vehicle = obj in ("Car", "car", "Vehicle", "Truck")
        is_person = not is_vehicle
        subject = "A vehicle" if is_vehicle else "Someone"
        if behavior == "loitering":
            return f"{subject} was stationary near {zone_label} for {_duration_str(dur)}."
        if behavior == "parked" and is_vehicle:
            return f"A vehicle parked at {zone_label}."
        if behavior == "approach" and is_person:
            return f"Someone approached {zone_label}."
        if behavior == "departure" and is_person:
            return f"Someone left via {zone_label}."
        return f"{subject} detected at {zone_label} ({_duration_str(dur)})."

    # Environment change
    environments = [e for e in events_in_window if e["type"] == "environment"]
    if environments:
        ev = environments[0]
        meta = ev.get("metadata") or {}
        parts = []
        co2 = meta.get("co2")
        temp = meta.get("temperature")
        aqi = meta.get("aqi")
        if co2:
            parts.append(f"CO₂ {co2} ppm")
        if temp:
            parts.append(f"{temp}°C")
        if aqi and aqi > 20:
            parts.append(f"AQI {aqi}")
        return "Outdoor conditions: " + " · ".join(parts) + "." if parts else None

    # Person detected
    persons = [e for e in events_in_window if e["type"] == "person"]
    vehicles = [e for e in events_in_window if e["type"] == "vehicle"]
    if persons and vehicles:
        return f"Person and vehicle detected at {zone_label}."
    if persons:
        name = (persons[0].get("identity") or {}).get("name")
        if name and name != "Someone":
            return f"{name} detected at {zone_label}."
        n = len(persons)
        return f"{'Someone' if n == 1 else str(n) + ' people'} at {zone_label}."
    if vehicles:
        return f"Vehicle detected at {zone_label}."

    # Occupancy
    occupancies = [e for e in events_in_window if e["type"] == "occupancy"]
    if occupancies:
        ev = occupancies[0]
        meta = ev.get("metadata") or {}
        phase = meta.get("phase", "")
        scenario = meta.get("scenario", "")
        label = "Vehicle" if "Vehicle" in scenario else "Person"
        if phase == "start":
            return f"{label} occupancy started at {zone_label}."
        if phase == "end":
            dur = meta.get("duration_seconds")
            if dur:
                return f"{label} occupancy at {zone_label} ended after {_duration_str(dur)}."
            return f"{label} occupancy ended at {zone_label}."

    return None


def _categorize(events_in_window: list[dict]) -> str:
    types = {e["type"] for e in events_in_window}
    if "arrival" in types:
        return "arrival"
    if "delivery" in types:
        return "delivery"
    if "door" in types:
        return "access"
    if "loitering" in types or any(
        (e.get("metadata") or {}).get("behavior") == "loitering" for e in events_in_window
    ):
        return "security"
    if "environment" in types:
        return "environment"
    if "person" in types or "vehicle" in types:
        return "activity"
    return "activity"


def _group_events_into_windows(events: list[dict]) -> list[list[dict]]:
    """Group chronologically sorted events into 5-minute windows."""
    if not events:
        return []
    events_sorted = sorted(events, key=lambda e: e["timestamp"])
    windows: list[list[dict]] = []
    current: list[dict] = [events_sorted[0]]
    window_start = datetime.fromisoformat(events_sorted[0]["timestamp"])
    if window_start.tzinfo is None:
        window_start = window_start.replace(tzinfo=TZ)

    for ev in events_sorted[1:]:
        ts = datetime.fromisoformat(ev["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=TZ)
        if (ts - window_start).total_seconds() <= BEAT_WINDOW_SEC:
            current.append(ev)
        else:
            windows.append(current)
            current = [ev]
            window_start = ts

    if current:
        windows.append(current)
    return windows


# Noisy types to skip when deciding if a window is "interesting"
_SKIP_TYPES = frozenset({"scene", "occupancy"})


def maybe_enrich_with_ollama(story: dict) -> dict:
    """Optional local LLM narrative when OLLAMA_URL is set."""
    base = os.environ.get("OLLAMA_URL", "").rstrip("/")
    if not base:
        return story

    model = os.environ.get("OLLAMA_MODEL", "qwen2.5")
    beat_lines = "\n".join(f"- {b['time']}: {b['text']}" for b in story.get("beats", [])[:20])
    prompt = (
        "Skriv en kort dagssammanfattning (2–4 meningar, svenska, familjevänlig ton) "
        "för ett smart hem baserat på fakta nedan. Hitta inte på händelser.\n\n"
        f"Datum: {story.get('date')}\n"
        f"Statistik: {json.dumps(story.get('stats', {}), ensure_ascii=False)}\n"
        f"Händelser:\n{beat_lines or '- Inga noterbara händelser.'}"
    )
    try:
        r = requests.post(
            f"{base}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        r.raise_for_status()
        text = (r.json().get("response") or "").strip()
        if text:
            story["ai_summary"] = text
            log.info("Ollama ai_summary generated (%d chars)", len(text))
    except requests.RequestException as err:
        log.warning("Ollama unavailable: %s", err)
    return story


def generate_story(date_str: str) -> dict:
    """Generate a StoryDocument for the given date (YYYY-MM-DD)."""
    STORIES_DIR.mkdir(parents=True, exist_ok=True)

    date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=TZ)
    since = date.replace(hour=0, minute=0, second=0)
    until = since + timedelta(days=1)

    events = load_events(hours=None, since=since, until=until, newest_first=False)

    windows = _group_events_into_windows(events)
    beats: list[dict] = []

    for window in windows:
        # Skip windows that are only scene/occupancy noise
        interesting = [e for e in window if e["type"] not in _SKIP_TYPES]
        if not interesting:
            continue

        text = _generate_beat_text(interesting)
        if not text:
            continue

        first_ev = window[0]
        ts = datetime.fromisoformat(first_ev["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=TZ)

        beats.append({
            "time": ts.strftime("%H:%M"),
            "timestamp": first_ev["timestamp"],
            "text": text,
            "category": _categorize(interesting),
            "event_ids": [e["event_id"] for e in window if "event_id" in e],
        })

    # Daily summary
    type_counts: dict[str, int] = {}
    for ev in events:
        t = ev["type"]
        if t not in _SKIP_TYPES:
            type_counts[t] = type_counts.get(t, 0) + 1

    arrivals = type_counts.get("arrival", 0)
    deliveries = type_counts.get("delivery", 0)
    persons = type_counts.get("person", 0)
    vehicles = type_counts.get("vehicle", 0)

    summary_parts = []
    if not beats:
        summary_parts.append("A quiet day with no notable activity.")
    else:
        if arrivals:
            summary_parts.append(f"{arrivals} arrival{'s' if arrivals > 1 else ''}")
        if deliveries:
            summary_parts.append(f"{deliveries} deliver{'ies' if deliveries > 1 else 'y'}")
        if persons and not arrivals:
            summary_parts.append(f"{persons} person detection{'s' if persons > 1 else ''}")
        if vehicles and not arrivals:
            summary_parts.append(f"{vehicles} vehicle detection{'s' if vehicles > 1 else ''}")

    summary = " · ".join(summary_parts) + "." if summary_parts else "No significant events."

    story = {
        "date": date_str,
        "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "title": f"{date.strftime('%A')} {date.day} {date.strftime('%B')}",
        "summary": summary,
        "beats": beats,
        "stats": type_counts,
    }
    story = maybe_enrich_with_ollama(story)

    out_path = STORIES_DIR / f"{date_str}.json"
    out_path.write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Story written: %s (%d beats)", out_path, len(beats))
    return story


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s  %(message)s")
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now(TZ).strftime("%Y-%m-%d")
    story = generate_story(date_str)
    print(f"Generated: {story['title']} — {len(story['beats'])} beats")
    print(f"Summary: {story['summary']}")


if __name__ == "__main__":
    main()
