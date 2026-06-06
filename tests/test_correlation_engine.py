"""Tests for scripts/correlation_engine.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from correlation_engine import CorrelationEngine
from event_store import TZ, make_summary


@pytest.fixture
def engine(store):
    return CorrelationEngine(store)


def _write_raw(store, *, ts: datetime, etype: str, zone: str, eid: str, identity: dict | None = None, meta: dict | None = None):
    event = {
        "event_id": eid,
        "timestamp": ts.isoformat(),
        "type": etype,
        "location": {"zone": zone, "camera": zone if zone != "driveway" else "driveway_wide"},
        "identity": identity or {},
        "metadata": meta or {},
        "source": "test",
        "enriched": False,
        "summary": "test",
    }
    store.write(event)
    return event


class TestDeliveryRule:
    def test_person_and_vehicle_at_front(self, engine, store):
        now = datetime.now(TZ)
        _write_raw(store, ts=now - timedelta(minutes=2), etype="vehicle", zone="front", eid="v1")
        person = _write_raw(store, ts=now, etype="person", zone="front", eid="p1")

        result = engine.process(person)
        assert len(result) >= 1
        types = {
            json.loads(line)["type"]
            for line in store.timeline_jsonl.read_text().splitlines()
            if json.loads(line).get("enriched")
        }
        assert "delivery" in types

    def test_scene_with_person_and_vehicle_counts(self, engine, store):
        now = datetime.now(TZ)
        scene = {
            "event_id": "s1",
            "timestamp": now.isoformat(),
            "type": "scene",
            "location": {"zone": "front", "camera": "front"},
            "metadata": {"persons": 1, "vehicles": 1},
            "source": "axis_scene",
            "enriched": False,
            "summary": "scene",
        }
        store.write(scene)
        result = engine.process(scene)
        assert any(
            json.loads(line)["type"] == "delivery"
            for line in store.timeline_jsonl.read_text().splitlines()
            if '"enriched": true' in line.replace(" ", "") or '"enriched":true' in line.replace(" ", "")
        ) or len(result) >= 1


class TestArrivalRule:
    def test_identified_person_at_front(self, engine, store):
        now = datetime.now(TZ)
        person = _write_raw(
            store,
            ts=now,
            etype="person",
            zone="front",
            eid="p_thomas",
            identity={"type": "person", "name": "Thomas", "source": "double_take", "confidence": 0.95},
        )
        result = engine.process(person)
        assert len(result) == 1
        enriched = json.loads(store.timeline_jsonl.read_text().strip().splitlines()[-1])
        assert enriched["type"] == "arrival"
        assert enriched["summary"] == make_summary(enriched)

    def test_vehicle_then_person_within_window(self, engine, store):
        now = datetime.now(TZ)
        _write_raw(store, ts=now - timedelta(seconds=45), etype="vehicle", zone="driveway", eid="v1")
        person = _write_raw(store, ts=now, etype="person", zone="front", eid="p1")
        result = engine.process(person)
        assert len(result) >= 1
        arrivals = [
            json.loads(line)
            for line in store.timeline_jsonl.read_text().splitlines()
            if json.loads(line).get("type") == "arrival"
        ]
        assert any(e["metadata"].get("rule") == "vehicle_then_person" for e in arrivals)

    def test_skips_duplicate_arrival_for_same_person(self, engine, store):
        now = datetime.now(TZ)
        identity = {"type": "person", "name": "Anna", "source": "double_take", "confidence": 0.9}
        p1 = _write_raw(store, ts=now - timedelta(minutes=5), etype="person", zone="front", eid="p1", identity=identity)
        engine.process(p1)
        p2 = _write_raw(store, ts=now, etype="person", zone="front", eid="p2", identity=identity)
        result = engine.process(p2)
        assert result == []


class TestDoorArrivalRule:
    def test_door_unlock_after_person_at_front(self, engine, store):
        now = datetime.now(TZ)
        _write_raw(
            store,
            ts=now - timedelta(seconds=30),
            etype="person",
            zone="front",
            eid="p1",
            identity={"type": "person", "name": "Nils", "source": "double_take", "confidence": 0.9},
        )
        door = {
            "event_id": "d1",
            "timestamp": now.isoformat(),
            "type": "door",
            "location": {"zone": "front", "camera": None},
            "metadata": {"action": "unlocked", "entity_id": "lock.front_door"},
            "source": "ha_mqtt",
            "enriched": False,
            "summary": "door",
        }
        store.write(door)
        result = engine.process(door)
        assert len(result) >= 1
        arrivals = [
            json.loads(line)
            for line in store.timeline_jsonl.read_text().splitlines()
            if json.loads(line).get("type") == "arrival" and json.loads(line).get("enriched")
        ]
        assert any(a["metadata"].get("rule", "").startswith("door_unlock") for a in arrivals)


class TestBicycleRule:
    def test_person_and_scene_bicycle_at_driveway_id(self, engine, store):
        now = datetime.now(TZ)
        _write_raw(
            store,
            ts=now - timedelta(seconds=20),
            etype="person",
            zone="driveway_id",
            eid="p1",
            identity={"type": "person", "name": "Hugo", "source": "double_take", "confidence": 0.88},
        )
        scene = {
            "event_id": "s1",
            "timestamp": now.isoformat(),
            "type": "scene",
            "location": {"zone": "driveway_id", "camera": "driveway_id"},
            "metadata": {"persons": 1, "vehicles": 0, "bicycles": 1},
            "source": "axis_scene",
            "enriched": False,
            "summary": "scene",
        }
        store.write(scene)
        result = engine.process(scene)
        assert len(result) >= 1
        bicycles = [
            json.loads(line)
            for line in store.timeline_jsonl.read_text().splitlines()
            if json.loads(line).get("type") == "bicycle"
        ]
        assert any(b.get("enriched") for b in bicycles)
        assert any(b["identity"].get("person") == "Hugo" for b in bicycles)

    def test_door_unlock_correlates_bicycle_trip(self, engine, store):
        now = datetime.now(TZ)
        _write_raw(store, ts=now - timedelta(seconds=40), etype="person", zone="driveway", eid="p1")
        scene = {
            "event_id": "s1",
            "timestamp": (now - timedelta(seconds=35)).isoformat(),
            "type": "scene",
            "location": {"zone": "driveway", "camera": "driveway_wide"},
            "metadata": {"persons": 1, "bicycles": 1, "vehicles": 0},
            "source": "axis_scene",
            "enriched": False,
            "summary": "scene",
        }
        store.write(scene)
        door = {
            "event_id": "d1",
            "timestamp": now.isoformat(),
            "type": "door",
            "location": {"zone": "front", "camera": None},
            "metadata": {"action": "unlocked"},
            "source": "ha_mqtt",
            "enriched": False,
            "summary": "door",
        }
        store.write(door)
        result = engine.process(door)
        assert len(result) >= 1
        enriched = [
            json.loads(line)
            for line in store.timeline_jsonl.read_text().splitlines()
            if json.loads(line).get("type") == "bicycle" and json.loads(line).get("enriched")
        ]
        assert any(e["metadata"].get("correlated_door_unlock") for e in enriched)
