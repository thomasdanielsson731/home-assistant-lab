"""Tests for scripts/event_store.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from event_store import EventStore, make_summary, TZ


class TestMakeSummary:
    def test_person_without_identity(self):
        event = {"type": "person", "location": {"zone": "front"}, "identity": {}}
        assert make_summary(event) == "Person detected at front"

    def test_person_with_identity(self):
        event = {
            "type": "person",
            "location": {"zone": "driveway"},
            "identity": {"name": "Thomas"},
        }
        assert make_summary(event) == "Thomas at driveway"

    def test_vehicle(self):
        event = {"type": "vehicle", "location": {"zone": "front"}, "identity": {}}
        assert make_summary(event) == "Vehicle at front"

    def test_environment(self):
        event = {
            "type": "environment",
            "location": {"zone": "driveway_env"},
            "metadata": {"temperature": 18.5, "co2": 431},
        }
        assert make_summary(event) == "Air · 18.5°C CO₂ 431"

    def test_door(self):
        event = {
            "type": "door",
            "location": {"zone": "front"},
            "identity": {"person": "Anna"},
            "metadata": {"action": "unlocked"},
        }
        assert make_summary(event) == "Door unlocked by Anna"

    def test_occupancy_start_and_end(self):
        start = {
            "type": "occupancy",
            "location": {"zone": "driveway"},
            "metadata": {"scenario": "PersonOccupancy", "phase": "start"},
        }
        end = {
            "type": "occupancy",
            "location": {"zone": "driveway"},
            "metadata": {"scenario": "VehicleOcc", "phase": "end", "duration_seconds": 120},
        }
        assert make_summary(start) == "Person occupancy started · driveway"
        assert make_summary(end) == "Vehicle occupancy ended · driveway (120s)"

    def test_scene_and_behavior(self):
        scene = {
            "type": "scene",
            "location": {"zone": "front"},
            "metadata": {"persons": 2, "vehicles": 1},
        }
        behavior = {
            "type": "behavior",
            "location": {"zone": "backyard"},
            "metadata": {"behavior": "loitering", "obj_type": "Human", "duration_seconds": 90},
        }
        assert make_summary(scene) == "Scene · 2 person(s), 1 vehicle(s) at front"
        assert make_summary(behavior) == "Loitering · Human at backyard (90s)"


class TestEventStoreWrite:
    def test_writes_json_and_timeline(self, store: EventStore, person_event: dict):
        person_event["summary"] = make_summary(person_event)
        event_id = store.write(person_event)

        assert event_id == "evt_20260606_140000_front_person"
        json_path = store.events_root / "person/2026/06/06" / f"{event_id}.json"
        assert json_path.exists()

        saved = json.loads(json_path.read_text(encoding="utf-8"))
        assert saved["type"] == "person"
        assert saved["event_id"] == event_id

        lines = store.timeline_jsonl.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["event_id"] == event_id

    def test_deduplicates_within_window(self, store: EventStore, person_event: dict):
        person_event["summary"] = make_summary(person_event)
        assert store.write(person_event) is not None
        assert store.write(person_event) is None

        lines = store.timeline_jsonl.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

    def test_allows_same_camera_different_type(self, store: EventStore):
        ts = datetime(2026, 6, 6, 15, 0, 0, tzinfo=TZ).isoformat()
        person = {
            "timestamp": ts,
            "type": "person",
            "location": {"zone": "front", "camera": "front"},
            "identity": {},
            "metadata": {},
            "source": "test",
        }
        vehicle = {**person, "type": "vehicle"}
        assert store.write(person) is not None
        assert store.write(vehicle) is not None

    def test_updates_daily_aggregate(self, store: EventStore, person_event: dict):
        person_event["summary"] = make_summary(person_event)
        store.write(person_event)

        agg_path = store.aggregates_dir / "2026-06-06.json"
        assert agg_path.exists()
        agg = json.loads(agg_path.read_text(encoding="utf-8"))
        assert agg["counts"]["person"] == 1
        assert agg["counts"]["vehicle"] == 0

    def test_environment_aggregate_metadata(self, store: EventStore):
        event = {
            "timestamp": datetime(2026, 6, 6, 16, 0, 0, tzinfo=TZ).isoformat(),
            "type": "environment",
            "location": {"zone": "driveway_env", "camera": None},
            "metadata": {"temperature": 17.2, "co2": 400, "note": "ignored"},
            "source": "d6210",
            "identity": {},
            "summary": "Air · 17.2°C CO₂ 400",
        }
        store.write(event)
        agg = json.loads((store.aggregates_dir / "2026-06-06.json").read_text())
        assert agg["counts"]["environment"] == 1
        assert agg["environment"]["temperature"] == 17.2
        assert agg["environment"]["co2"] == 400
        assert "note" not in agg["environment"]

    def test_make_event_id_format(self, store: EventStore):
        ts = datetime(2026, 12, 25, 9, 30, 45, tzinfo=TZ)
        assert store.make_event_id(ts, "front", "person") == "evt_20261225_093045_front_person"
