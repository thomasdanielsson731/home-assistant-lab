#!/usr/bin/env python3
"""
Danielsson Home Intelligence — Correlation Engine (Phase 7e).

Derives enriched events from recent raw events in the timeline window.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from event_store import TZ, make_summary

if TYPE_CHECKING:
    from event_store import EventStore

log = logging.getLogger("correlation")

# Property zones that count as "approach / entrance"
ENTRANCE_ZONES = frozenset({"front", "driveway"})

ARRIVAL_COOLDOWN = timedelta(minutes=30)
DELIVERY_COOLDOWN = timedelta(minutes=20)

ARRIVAL_LOOKBACK = timedelta(minutes=15)
DELIVERY_LOOKBACK = timedelta(minutes=10)
VEHICLE_PERSON_WINDOW = timedelta(minutes=2)


def _parse_ts(value: str) -> datetime:
    ts = datetime.fromisoformat(value)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=TZ)
    return ts


def _offset_seconds(a: datetime, b: datetime) -> int:
    return int((a - b).total_seconds())


def _correlation_refs(trigger: dict, others: list[dict]) -> list[dict]:
    t0 = _parse_ts(trigger["timestamp"])
    refs = [
        {
            "event_id": trigger["event_id"],
            "type": trigger["type"],
            "offset_seconds": 0,
        }
    ]
    for ev in others:
        if ev["event_id"] == trigger["event_id"]:
            continue
        refs.append(
            {
                "event_id": ev["event_id"],
                "type": ev["type"],
                "offset_seconds": _offset_seconds(_parse_ts(ev["timestamp"]), t0),
            }
        )
    return refs


def _best_snapshot(events: list[dict]) -> dict | None:
    for ev in events:
        snap = ev.get("snapshot")
        if snap and snap.get("best_picture"):
            return snap
    return None


class CorrelationEngine:
    """Rule-based correlation over recent timeline events."""

    def __init__(self, store: EventStore) -> None:
        self.store = store

    def process(self, trigger: dict) -> list[str]:
        """Evaluate rules after a raw event is stored. Returns new event_ids."""
        written: list[str] = []
        for rule in (self._try_delivery, self._try_arrival):
            eid = rule(trigger)
            if eid:
                written.append(eid)
        return written

    def _recent(
        self,
        *,
        since: datetime,
        until: datetime,
        zones: frozenset[str] | None = None,
        types: frozenset[str] | None = None,
    ) -> list[dict]:
        path = self.store.timeline_jsonl
        if not path.exists():
            return []
        out: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("enriched"):
                continue
            ts = _parse_ts(ev["timestamp"])
            if ts < since or ts > until:
                continue
            zone = ev.get("location", {}).get("zone", "")
            if zones and zone not in zones:
                continue
            if types and ev.get("type") not in types:
                continue
            out.append(ev)
        out.sort(key=lambda e: e["timestamp"])
        return out

    def _enriched_exists(self, parent_ids: list[str], etype: str, since: datetime) -> bool:
        path = self.store.timeline_jsonl
        if not path.exists():
            return False
        parent_set = set(parent_ids)
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != etype or not ev.get("enriched"):
                continue
            if _parse_ts(ev["timestamp"]) < since:
                continue
            existing = set(ev.get("parent_event_ids") or [])
            if parent_set & existing:
                return True
        return False

    def _write_enriched(
        self,
        *,
        etype: str,
        timestamp: str,
        zone: str,
        camera: str | None,
        trigger: dict,
        related: list[dict],
        identity: dict | None = None,
        extra_meta: dict | None = None,
    ) -> str | None:
        parents = [trigger["event_id"]] + [e["event_id"] for e in related if e["event_id"] != trigger["event_id"]]
        since = _parse_ts(timestamp) - (ARRIVAL_COOLDOWN if etype == "arrival" else DELIVERY_COOLDOWN)
        if self._enriched_exists(parents, etype, since):
            return None

        all_events = [trigger, *related]
        meta = {"correlations": _correlation_refs(trigger, related)}
        if extra_meta:
            meta.update(extra_meta)

        event = {
            "timestamp": timestamp,
            "type": etype,
            "location": {"zone": zone, "camera": camera},
            "identity": identity or {},
            "metadata": meta,
            "source": "correlation_engine",
            "enriched": True,
            "parent_event_ids": parents,
        }
        snap = _best_snapshot(all_events)
        if snap:
            event["snapshot"] = snap
        event["summary"] = make_summary(event)
        return self.store.write(event)

    def _try_delivery(self, trigger: dict) -> str | None:
        if trigger.get("type") not in ("person", "vehicle", "scene"):
            return None
        zone = trigger.get("location", {}).get("zone", "")
        if zone not in ENTRANCE_ZONES:
            return None

        ts = _parse_ts(trigger["timestamp"])
        recent = self._recent(
            since=ts - DELIVERY_LOOKBACK,
            until=ts,
            zones=ENTRANCE_ZONES,
            types=frozenset({"person", "vehicle", "scene"}),
        )

        persons = [e for e in recent if e["type"] == "person"]
        vehicles = [e for e in recent if e["type"] == "vehicle"]
        scenes = [e for e in recent if e["type"] == "scene"]

        scene_match = any(
            (e.get("metadata") or {}).get("persons", 0) >= 1
            and (e.get("metadata") or {}).get("vehicles", 0) >= 1
            for e in scenes
        )
        if not ((persons and vehicles) or scene_match):
            return None

        related = [e for e in recent if e["event_id"] != trigger["event_id"]]
        camera = trigger.get("location", {}).get("camera")
        eid = self._write_enriched(
            etype="delivery",
            timestamp=trigger["timestamp"],
            zone=zone,
            camera=camera,
            trigger=trigger,
            related=related,
            extra_meta={"rule": "person_and_vehicle", "scene_match": scene_match},
        )
        if eid:
            log.info("Correlated delivery: %s", eid)
        return eid

    def _try_arrival(self, trigger: dict) -> str | None:
        ts = _parse_ts(trigger["timestamp"])
        zone = trigger.get("location", {}).get("zone", "")

        # Identified person at entrance → arrival
        if trigger.get("type") == "person" and zone in ENTRANCE_ZONES:
            name = (trigger.get("identity") or {}).get("name")
            if name:
                if self._arrival_recent_for_person(name, ts - ARRIVAL_COOLDOWN):
                    return None
                return self._write_enriched(
                    etype="arrival",
                    timestamp=trigger["timestamp"],
                    zone=zone,
                    camera=trigger.get("location", {}).get("camera"),
                    trigger=trigger,
                    related=[],
                    identity=dict(trigger.get("identity") or {}),
                    extra_meta={"rule": "identified_person", "direction": "arriving"},
                )

        # Vehicle then person at entrance within 2 min → arrival (unknown or named)
        if trigger.get("type") not in ("person", "vehicle"):
            return None
        if zone not in ENTRANCE_ZONES:
            return None

        recent = self._recent(
            since=ts - ARRIVAL_LOOKBACK,
            until=ts,
            zones=ENTRANCE_ZONES,
            types=frozenset({"person", "vehicle"}),
        )
        persons = [e for e in recent if e["type"] == "person"]
        vehicles = [e for e in recent if e["type"] == "vehicle"]
        if not persons or not vehicles:
            return None

        # Require temporal proximity between last vehicle and this person (or vice versa)
        if trigger["type"] == "person":
            last_vehicle = vehicles[-1]
            if ts - _parse_ts(last_vehicle["timestamp"]) > VEHICLE_PERSON_WINDOW:
                return None
            identity = dict(trigger.get("identity") or {})
            related = [last_vehicle]
        else:
            last_person = persons[-1]
            if ts - _parse_ts(last_person["timestamp"]) > VEHICLE_PERSON_WINDOW:
                return None
            identity = dict(last_person.get("identity") or {})
            related = [last_person]

        name = identity.get("name")
        if not name:
            identity = {"type": "person", "name": "Someone", "source": "correlation", "confidence": 0.5}

        eid = self._write_enriched(
            etype="arrival",
            timestamp=trigger["timestamp"],
            zone=zone,
            camera=trigger.get("location", {}).get("camera"),
            trigger=trigger,
            related=related,
            identity=identity,
            extra_meta={"rule": "vehicle_then_person", "direction": "arriving"},
        )
        if eid:
            log.info("Correlated arrival: %s", eid)
        return eid

    def _arrival_recent_for_person(self, name: str, since: datetime) -> bool:
        path = self.store.timeline_jsonl
        if not path.exists():
            return False
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != "arrival" or not ev.get("enriched"):
                continue
            if _parse_ts(ev["timestamp"]) < since:
                continue
            if (ev.get("identity") or {}).get("name", "").lower() == name.lower():
                return True
        return False
