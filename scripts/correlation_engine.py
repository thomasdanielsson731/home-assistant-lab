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
BICYCLE_ZONES = frozenset({"front", "driveway", "driveway_id"})

ARRIVAL_COOLDOWN = timedelta(minutes=30)
DELIVERY_COOLDOWN = timedelta(minutes=20)
BICYCLE_COOLDOWN = timedelta(minutes=20)

ARRIVAL_LOOKBACK = timedelta(minutes=15)
DELIVERY_LOOKBACK = timedelta(minutes=10)
VEHICLE_PERSON_WINDOW = timedelta(minutes=2)
DOOR_ARRIVAL_LOOKBACK = timedelta(minutes=5)
DOOR_UNLOCK_WINDOW = timedelta(seconds=60)
BICYCLE_LOOKBACK = timedelta(minutes=5)

_COOLDOWNS = {
    "arrival": ARRIVAL_COOLDOWN,
    "delivery": DELIVERY_COOLDOWN,
    "bicycle": BICYCLE_COOLDOWN,
}

BIKE_SCENE_TYPES = frozenset({"Bike", "bike", "Bicycle", "bicycle"})


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
        for rule in (
            self._try_delivery,
            self._try_arrival,
            self._try_arrival_from_door,
            self._try_bicycle,
        ):
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
        since = _parse_ts(timestamp) - _COOLDOWNS.get(etype, DELIVERY_COOLDOWN)
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

    def _door_unlock_near(self, ts: datetime, *, before: bool = True) -> dict | None:
        """Return nearest door unlock within DOOR_UNLOCK_WINDOW (before or after ts)."""
        window_start = ts - DOOR_UNLOCK_WINDOW if before else ts
        window_end = ts if before else ts + DOOR_UNLOCK_WINDOW
        doors = self._recent(
            since=window_start,
            until=window_end,
            types=frozenset({"door"}),
        )
        unlocks = [
            d for d in doors
            if (d.get("metadata") or {}).get("action") == "unlocked"
        ]
        if not unlocks:
            return None
        return unlocks[-1] if before else unlocks[0]

    def _try_arrival(self, trigger: dict) -> str | None:
        ts = _parse_ts(trigger["timestamp"])
        zone = trigger.get("location", {}).get("zone", "")

        # Identified person at entrance → arrival
        if trigger.get("type") == "person" and zone in ENTRANCE_ZONES:
            name = (trigger.get("identity") or {}).get("name")
            if name:
                if self._arrival_recent_for_person(name, ts - ARRIVAL_COOLDOWN):
                    return None
                door = self._door_unlock_near(ts, before=False)
                extra: dict = {"rule": "identified_person", "direction": "arriving"}
                related: list[dict] = []
                if door:
                    extra["door_corroborated"] = True
                    related = [door]
                return self._write_enriched(
                    etype="arrival",
                    timestamp=trigger["timestamp"],
                    zone=zone,
                    camera=trigger.get("location", {}).get("camera"),
                    trigger=trigger,
                    related=related,
                    identity=dict(trigger.get("identity") or {}),
                    extra_meta=extra,
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

        door = self._door_unlock_near(ts, before=False)
        extra_meta: dict = {"rule": "vehicle_then_person", "direction": "arriving"}
        if door:
            extra_meta["door_corroborated"] = True
            related = [*related, door]

        eid = self._write_enriched(
            etype="arrival",
            timestamp=trigger["timestamp"],
            zone=zone,
            camera=trigger.get("location", {}).get("camera"),
            trigger=trigger,
            related=related,
            identity=identity,
            extra_meta=extra_meta,
        )
        if eid:
            log.info("Correlated arrival: %s", eid)
        return eid

    def _try_arrival_from_door(self, trigger: dict) -> str | None:
        if trigger.get("type") != "door":
            return None
        if (trigger.get("metadata") or {}).get("action") != "unlocked":
            return None

        ts = _parse_ts(trigger["timestamp"])
        zone = trigger.get("location", {}).get("zone", "front")
        recent = self._recent(
            since=ts - DOOR_ARRIVAL_LOOKBACK,
            until=ts,
            zones=ENTRANCE_ZONES,
            types=frozenset({"person", "vehicle"}),
        )
        persons = [e for e in recent if e["type"] == "person"]
        vehicles = [e for e in recent if e["type"] == "vehicle"]
        if not persons:
            return None

        last_person = persons[-1]
        identity = dict(last_person.get("identity") or {})
        rule = "door_unlock"
        related = [last_person]

        if vehicles:
            last_vehicle = vehicles[-1]
            if ts - _parse_ts(last_vehicle["timestamp"]) <= VEHICLE_PERSON_WINDOW:
                related = [last_vehicle, last_person]
                rule = "door_unlock_vehicle_person"
                if not identity.get("name"):
                    identity = {
                        "type": "person",
                        "name": "Someone",
                        "source": "correlation",
                        "confidence": 0.55,
                    }
        elif not identity.get("name"):
            identity = {
                "type": "person",
                "name": "Someone",
                "source": "correlation",
                "confidence": 0.45,
            }

        name = identity.get("name")
        if name and name != "Someone" and self._arrival_recent_for_person(name, ts - ARRIVAL_COOLDOWN):
            return None

        eid = self._write_enriched(
            etype="arrival",
            timestamp=trigger["timestamp"],
            zone=zone,
            camera=last_person.get("location", {}).get("camera"),
            trigger=trigger,
            related=related,
            identity=identity,
            extra_meta={"rule": rule, "direction": "arriving", "door_corroborated": True},
        )
        if eid:
            log.info("Correlated arrival from door: %s", eid)
        return eid

    def _scene_has_bicycle(self, event: dict) -> bool:
        meta = event.get("metadata") or {}
        if meta.get("bicycles", 0) >= 1:
            return True
        return any(
            d.get("type") in BIKE_SCENE_TYPES
            for d in meta.get("detection_types") or []
        )

    def _try_bicycle(self, trigger: dict) -> str | None:
        ts = _parse_ts(trigger["timestamp"])
        ttype = trigger.get("type")

        if ttype == "door":
            if (trigger.get("metadata") or {}).get("action") != "unlocked":
                return None
            zone = trigger.get("location", {}).get("zone", "front")
            recent = self._recent(
                since=ts - BICYCLE_LOOKBACK,
                until=ts,
                zones=BICYCLE_ZONES,
                types=frozenset({"person", "bicycle", "scene"}),
            )
            persons = [e for e in recent if e["type"] == "person"]
            bikes = [e for e in recent if e["type"] == "bicycle"]
            scenes = [e for e in recent if e["type"] == "scene" and self._scene_has_bicycle(e)]
            if not persons or not (bikes or scenes):
                return None
            person_ev = persons[-1]
            zone = person_ev.get("location", {}).get("zone", zone)
            related = [e for e in recent if e["event_id"] != trigger["event_id"]]
            extra: dict = {
                "rule": "person_and_bicycle",
                "correlated_door_unlock": True,
                "time_to_door_seconds": 0,
            }
            return self._write_bicycle_enriched(
                trigger=trigger,
                person_ev=person_ev,
                zone=zone,
                related=related,
                extra=extra,
            )

        zone = trigger.get("location", {}).get("zone", "")
        if zone not in BICYCLE_ZONES:
            return None

        if ttype == "scene" and not self._scene_has_bicycle(trigger):
            return None
        if ttype not in ("person", "bicycle", "scene"):
            return None

        recent = self._recent(
            since=ts - BICYCLE_LOOKBACK,
            until=ts,
            zones=BICYCLE_ZONES,
            types=frozenset({"person", "bicycle", "scene"}),
        )

        persons = [e for e in recent if e["type"] == "person"]
        bikes = [e for e in recent if e["type"] == "bicycle"]
        scenes = [e for e in recent if e["type"] == "scene" and self._scene_has_bicycle(e)]

        has_person = bool(persons) or ttype == "person"
        has_bike = bool(bikes) or (ttype == "bicycle") or (
            ttype == "scene" and self._scene_has_bicycle(trigger)
        ) or bool(scenes)

        if not has_person or not has_bike:
            return None

        person_ev = trigger if ttype == "person" else persons[-1]
        related = [e for e in recent if e["event_id"] != trigger["event_id"]]
        extra = {"rule": "person_and_bicycle"}
        return self._write_bicycle_enriched(
            trigger=trigger,
            person_ev=person_ev,
            zone=zone,
            related=related,
            extra=extra,
        )

    def _write_bicycle_enriched(
        self,
        *,
        trigger: dict,
        person_ev: dict,
        zone: str,
        related: list[dict],
        extra: dict,
    ) -> str | None:
        identity_src = person_ev.get("identity") or {}
        person_name = identity_src.get("name") or "Someone"
        identity = {
            "type": "person",
            "person": person_name,
            "name": person_name,
            "source": identity_src.get("source", "correlation"),
            "confidence": identity_src.get("confidence", 0.5),
        }
        eid = self._write_enriched(
            etype="bicycle",
            timestamp=trigger["timestamp"],
            zone=zone,
            camera=trigger.get("location", {}).get("camera") or person_ev.get("location", {}).get("camera"),
            trigger=trigger,
            related=related,
            identity=identity,
            extra_meta=extra,
        )
        if eid:
            log.info("Correlated bicycle: %s", eid)
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
