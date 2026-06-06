#!/usr/bin/env python3
"""Danielsson Insights event store — write, deduplicate, aggregate."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

log = logging.getLogger("event_store")

REPO_ROOT = Path(__file__).parent.parent
EVENTS_ROOT = REPO_ROOT / "events"
TIMELINE_JSONL = EVENTS_ROOT / "timeline.jsonl"
METRICS_JSONL = EVENTS_ROOT / "metrics.jsonl"
AGGREGATES_DIR = EVENTS_ROOT / "aggregates"


def local_tz():
    """Europe/Stockholm; falls back to system TZ on Windows without tzdata."""
    try:
        return ZoneInfo("Europe/Stockholm")
    except Exception:
        return datetime.now().astimezone().tzinfo or timezone.utc


TZ = local_tz()

# Frigate camera zone_id → logical zone (event-model.md)
CAMERA_ZONE = {
    "front": "front",
    "driveway_wide": "driveway",
    "driveway_id": "driveway",
    "backyard": "backyard",
    "storage_ext": "storage_ext",
    "storage_int": "storage_int",
}

FRIGATE_LABEL_TYPE = {
    "person": "person",
    "car": "vehicle",
    "bicycle": "bicycle",
}


@dataclass
class EventStore:
    events_root: Path = EVENTS_ROOT
    dedup_seconds: int = 30
    _recent: list[tuple[datetime, tuple[str, str, str], str]] = field(default_factory=list)

    @property
    def timeline_jsonl(self) -> Path:
        return self.events_root / "timeline.jsonl"

    @property
    def aggregates_dir(self) -> Path:
        return self.events_root / "aggregates"

    @property
    def metrics_jsonl(self) -> Path:
        return self.events_root / "metrics.jsonl"

    def __post_init__(self) -> None:
        for sub in (
            "person", "vehicle", "bicycle", "cat", "delivery", "arrival",
            "environment", "occupancy", "scene", "door", "smoke",
        ):
            (self.events_root / sub).mkdir(parents=True, exist_ok=True)
        self.aggregates_dir.mkdir(parents=True, exist_ok=True)

    def _now(self) -> datetime:
        return datetime.now(TZ)

    def _dedup_key(self, event: dict) -> tuple[str, str, str]:
        loc = event.get("location", {})
        camera = loc.get("camera") or loc.get("zone", "")
        event_type = event["type"]
        extra = ""
        if event_type == "occupancy":
            meta = event.get("metadata") or {}
            extra = f"{meta.get('scenario', '')}:{meta.get('phase', '')}"
        elif event_type == "scene":
            meta = event.get("metadata") or {}
            extra = f"{meta.get('persons', 0)}:{meta.get('vehicles', 0)}"
        return (camera, event_type, extra)

    def _is_duplicate(self, ts: datetime, dedup_key: tuple[str, str, str]) -> bool:
        cutoff = ts - timedelta(seconds=self.dedup_seconds)
        self._recent = [
            (t, k, _) for t, k, _ in self._recent if t >= cutoff
        ]
        camera, event_type, extra = dedup_key
        for t, k, _ in self._recent:
            if k == dedup_key and abs((ts - t).total_seconds()) < self.dedup_seconds:
                return True
        return False

    def _remember(self, ts: datetime, dedup_key: tuple[str, str, str], event_id: str) -> None:
        self._recent.append((ts, dedup_key, event_id))
        if len(self._recent) > 500:
            self._recent = self._recent[-200:]

    def make_event_id(self, ts: datetime, camera: str, event_type: str) -> str:
        return f"evt_{ts.strftime('%Y%m%d_%H%M%S')}_{camera}_{event_type}"

    def write(self, event: dict) -> str | None:
        """Persist event. Returns event_id or None if deduplicated."""
        ts = datetime.fromisoformat(event["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=TZ)

        dedup_key = self._dedup_key(event)

        if self._is_duplicate(ts, dedup_key):
            log.debug("Dedup skip %s", dedup_key)
            return None

        loc = event.get("location", {})
        camera = loc.get("camera") or loc.get("zone", "unknown")
        event_type = event["type"]
        event_id = event.get("event_id") or self.make_event_id(ts, camera, event_type)
        event["event_id"] = event_id

        day_dir = (
            self.events_root / event_type
            / ts.strftime("%Y") / ts.strftime("%m") / ts.strftime("%d")
        )
        day_dir.mkdir(parents=True, exist_ok=True)

        path = day_dir / f"{event_id}.json"
        path.write_text(json.dumps(event, indent=2, ensure_ascii=False), encoding="utf-8")

        with self.timeline_jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        self._remember(ts, dedup_key, event_id)
        self._update_aggregate(event)
        log.info("Event stored: %s (%s)", event_id, event.get("summary", event_type))
        return event_id

    def write_metric(self, timestamp: str, zone: str, values: dict) -> None:
        """Append a continuous metric sample (timeline metrics layer)."""
        row = {"timestamp": timestamp, "zone": zone, "values": values}
        with self.metrics_jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _update_aggregate(self, event: dict) -> None:
        ts = datetime.fromisoformat(event["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=TZ)
        date_key = ts.strftime("%Y-%m-%d")
        agg_path = self.aggregates_dir / f"{date_key}.json"

        if agg_path.exists():
            agg = json.loads(agg_path.read_text(encoding="utf-8"))
        else:
            agg = {
                "date": date_key,
                "counts": {t: 0 for t in (
                    "person", "vehicle", "bicycle", "cat", "delivery",
                    "environment", "occupancy", "scene", "door", "smoke",
                )},
                "environment": {},
            }

        etype = event["type"]
        if etype in agg["counts"]:
            agg["counts"][etype] += 1

        if etype == "environment":
            for k, v in event.get("metadata", {}).items():
                if isinstance(v, (int, float)):
                    agg["environment"][k] = v

        agg_path.write_text(json.dumps(agg, indent=2), encoding="utf-8")

    def attach_identity(self, camera: str, name: str, confidence: float, source: str = "double_take") -> str | None:
        """Attach identity to most recent person event at camera (within 2 min)."""
        if not self.timeline_jsonl.exists():
            return None

        cutoff = self._now() - timedelta(minutes=2)
        lines = self.timeline_jsonl.read_text(encoding="utf-8").strip().splitlines()
        for line in reversed(lines[-100:]):
            event = json.loads(line)
            if event.get("type") != "person":
                continue
            if event.get("location", {}).get("camera") != camera:
                continue
            ts = datetime.fromisoformat(event["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=TZ)
            if ts < cutoff:
                break
            event["identity"] = {
                "type": "person",
                "name": name.title(),
                "source": source,
                "confidence": confidence,
            }
            event["summary"] = f"{name.title()} at {event['location'].get('zone', camera)}"
            event_id = event["event_id"]
            encoded = json.dumps(event, ensure_ascii=False)
            # Rewrite JSON file
            for path in (self.events_root / "person").rglob(f"{event_id}.json"):
                path.write_text(json.dumps(event, indent=2, ensure_ascii=False), encoding="utf-8")
            # Update matching line in timeline log
            all_lines = self.timeline_jsonl.read_text(encoding="utf-8").splitlines()
            self.timeline_jsonl.write_text(
                "\n".join(
                    encoded if json.loads(line).get("event_id") == event_id else line
                    for line in all_lines
                ) + ("\n" if all_lines else ""),
                encoding="utf-8",
            )
            log.info("Identity attached: %s → %s", event_id, name)
            return event_id
        return None


def make_summary(event: dict) -> str:
    """Template-based timeline summary (v1)."""
    etype = event["type"]
    zone = event.get("location", {}).get("zone", "?")
    identity = event.get("identity", {})

    if etype == "person":
        name = identity.get("name")
        if name:
            return f"{name} at {zone}"
        return f"Person detected at {zone}"
    if etype == "vehicle":
        return f"Vehicle at {zone}"
    if etype == "bicycle":
        person = identity.get("person", "?")
        return f"{person} arrived by bicycle at {zone}"
    if etype == "cat":
        cat = identity.get("cat", "Cat")
        return f"{cat} visited {zone}"
    if etype == "delivery":
        return f"Delivery detected at {zone}"
    if etype == "arrival":
        name = identity.get("name", "Someone")
        if event.get("metadata", {}).get("direction") == "arriving":
            return f"{name} arrived home"
        return f"{name} arrived at {zone}"
    if etype == "door":
        person = identity.get("person", "Someone")
        action = event.get("metadata", {}).get("action", "unlocked")
        return f"Door {action} by {person}"
    if etype == "environment":
        meta = event.get("metadata", {})
        temp = meta.get("temperature", "?")
        co2 = meta.get("co2", "?")
        return f"Air · {temp}°C CO₂ {co2}"
    if etype == "occupancy":
        meta = event.get("metadata", {})
        scenario = meta.get("scenario", "occupancy")
        phase = meta.get("phase", "")
        label = "Vehicle" if "Vehicle" in scenario else "Person"
        if phase == "start":
            return f"{label} occupancy started · {zone}"
        if phase == "end":
            dur = meta.get("duration_seconds")
            if dur:
                return f"{label} occupancy ended · {zone} ({dur}s)"
            return f"{label} occupancy ended · {zone}"
        return f"{label} occupancy · {zone}"
    if etype == "scene":
        meta = event.get("metadata", {})
        humans = meta.get("persons", 0)
        vehicles = meta.get("vehicles", 0)
        parts = []
        if humans:
            parts.append(f"{humans} person(s)")
        if vehicles:
            parts.append(f"{vehicles} vehicle(s)")
        detail = ", ".join(parts) if parts else "object(s)"
        return f"Scene · {detail} at {zone}"
    return f"{etype} at {zone}"
