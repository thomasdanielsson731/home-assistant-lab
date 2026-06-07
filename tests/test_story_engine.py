"""Tests for scripts/story_engine.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from event_store import TZ
from story_engine import (
    BEAT_WINDOW_SEC,
    _categorize,
    _duration_str,
    _generate_beat_text,
    _group_events_into_windows,
    _zone_label,
    generate_story,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _ev(etype: str, zone: str = "front", ts_offset_s: int = 0, **kwargs) -> dict:
    now = datetime(2026, 6, 6, 12, 0, 0, tzinfo=TZ)
    ts = (now + timedelta(seconds=ts_offset_s)).isoformat()
    ev: dict = {
        "timestamp": ts,
        "type": etype,
        "location": {"zone": zone, "camera": zone},
        "event_id": f"{etype}_{zone}_{ts_offset_s}",
    }
    ev.update(kwargs)
    return ev


# ── _duration_str ──────────────────────────────────────────────────────────

class TestDurationStr:
    def test_under_one_minute(self):
        assert _duration_str(30) == "30 seconds"

    def test_exactly_sixty_seconds(self):
        assert _duration_str(60) == "1 minutes"

    def test_minutes(self):
        assert _duration_str(90) == "1 minutes"

    def test_hours(self):
        assert "hours" in _duration_str(7200)

    def test_partial_hours(self):
        result = _duration_str(5400)
        assert "hours" in result
        assert "1.5" in result


# ── _zone_label ────────────────────────────────────────────────────────────

class TestZoneLabel:
    def test_known_zones(self):
        assert _zone_label("front") == "the front entrance"
        assert _zone_label("driveway_wide") == "the driveway"
        assert _zone_label("driveway_id") == "the driveway"
        assert _zone_label("backyard") == "the backyard"
        assert _zone_label("storage_ext") == "the storage building"
        assert _zone_label("storage_int") == "the storage building"
        assert _zone_label("driveway_env") == "outside"

    def test_unknown_zone_snake_to_space(self):
        assert _zone_label("my_custom_zone") == "my custom zone"


# ── _generate_beat_text ────────────────────────────────────────────────────

class TestGenerateBeatText:
    def test_empty_window_returns_none(self):
        assert _generate_beat_text([]) is None

    def test_arrival_named(self):
        ev = _ev("arrival", identity={"name": "Thomas"})
        assert _generate_beat_text([ev]) == "Thomas arrived home."

    def test_arrival_unknown(self):
        ev = _ev("arrival", identity={"name": "Someone"})
        assert _generate_beat_text([ev]) == "Someone arrived home."

    def test_arrival_no_identity(self):
        ev = _ev("arrival")
        assert _generate_beat_text([ev]) == "Someone arrived home."

    def test_delivery(self):
        ev = _ev("delivery", zone="front")
        result = _generate_beat_text([ev])
        assert "delivery" in result.lower()
        assert "front entrance" in result

    def test_bicycle_named(self):
        ev = _ev("bicycle", zone="driveway_wide", identity={"name": "Nils"})
        result = _generate_beat_text([ev])
        assert "Nils" in result
        assert "bicycle" in result.lower()

    def test_bicycle_unknown(self):
        ev = _ev("bicycle", zone="front")
        result = _generate_beat_text([ev])
        assert "bicycle" in result.lower()

    def test_door_event(self):
        ev = _ev("door", metadata={"action": "unlocked"})
        result = _generate_beat_text([ev])
        assert "unlocked" in result

    def test_door_event_default_action(self):
        ev = _ev("door", metadata={})
        result = _generate_beat_text([ev])
        assert "opened" in result

    def test_behavior_loitering_person(self):
        ev = _ev("behavior", zone="front", metadata={"behavior": "loitering", "duration_seconds": 120, "obj_type": "Human"})
        result = _generate_beat_text([ev])
        assert "stationary" in result or "loitering" in result.lower()

    def test_behavior_parked_vehicle(self):
        ev = _ev("behavior", zone="driveway_wide", metadata={"behavior": "parked", "duration_seconds": 300, "obj_type": "Car"})
        result = _generate_beat_text([ev])
        assert "parked" in result.lower()

    def test_behavior_approach_person(self):
        ev = _ev("behavior", zone="front", metadata={"behavior": "approach", "duration_seconds": 20, "obj_type": "Human"})
        result = _generate_beat_text([ev])
        assert "approached" in result

    def test_behavior_departure_person(self):
        ev = _ev("behavior", zone="front", metadata={"behavior": "departure", "duration_seconds": 15, "obj_type": "Human"})
        result = _generate_beat_text([ev])
        assert "left" in result

    def test_behavior_fallback(self):
        ev = _ev("behavior", zone="front", metadata={"behavior": "unknown", "duration_seconds": 10, "obj_type": "Human"})
        result = _generate_beat_text([ev])
        assert result is not None

    def test_environment_with_values(self):
        ev = _ev("environment", zone="driveway_env", metadata={"co2": 550, "temperature": 19.5, "aqi": 25})
        result = _generate_beat_text([ev])
        assert "CO" in result
        assert "19.5" in result

    def test_environment_high_aqi(self):
        ev = _ev("environment", metadata={"aqi": 50})
        result = _generate_beat_text([ev])
        assert "AQI 50" in result

    def test_environment_low_aqi_omitted(self):
        ev = _ev("environment", metadata={"aqi": 10})
        # aqi <= 20 is omitted
        result = _generate_beat_text([ev])
        # no parts at all → None
        assert result is None or "AQI" not in result

    def test_person_named(self):
        ev = _ev("person", zone="front", identity={"name": "Anna"})
        result = _generate_beat_text([ev])
        assert "Anna" in result

    def test_person_unnamed(self):
        ev = _ev("person", zone="front")
        result = _generate_beat_text([ev])
        assert "Someone" in result or "people" in result

    def test_multiple_persons(self):
        evs = [_ev("person", zone="front", ts_offset_s=i) for i in range(3)]
        result = _generate_beat_text(evs)
        assert "3 people" in result

    def test_vehicle_only(self):
        ev = _ev("vehicle", zone="driveway_wide")
        result = _generate_beat_text([ev])
        assert "Vehicle" in result or "vehicle" in result.lower()

    def test_person_and_vehicle(self):
        evs = [_ev("person", zone="front"), _ev("vehicle", zone="front")]
        result = _generate_beat_text(evs)
        assert "Person" in result and "vehicle" in result.lower()

    def test_occupancy_start(self):
        ev = _ev("occupancy", zone="front", metadata={"scenario": "PersonOccupancy", "phase": "start"})
        result = _generate_beat_text([ev])
        assert "started" in result

    def test_occupancy_end_with_duration(self):
        ev = _ev("occupancy", zone="front", metadata={"scenario": "VehicleOcc", "phase": "end", "duration_seconds": 300})
        result = _generate_beat_text([ev])
        assert "ended" in result
        assert "5 minutes" in result

    def test_occupancy_end_without_duration(self):
        ev = _ev("occupancy", zone="front", metadata={"scenario": "PersonOccupancy", "phase": "end"})
        result = _generate_beat_text([ev])
        assert "ended" in result

    def test_arrival_beats_delivery(self):
        evs = [_ev("arrival", identity={"name": "Thomas"}), _ev("delivery")]
        result = _generate_beat_text(evs)
        assert "Thomas arrived home" in result

    def test_unknown_type_only_returns_none(self):
        ev = _ev("scene")  # scene is filtered before this call normally
        result = _generate_beat_text([ev])
        assert result is None


# ── _categorize ────────────────────────────────────────────────────────────

class TestCategorize:
    def test_arrival(self):
        assert _categorize([_ev("arrival")]) == "arrival"

    def test_delivery(self):
        assert _categorize([_ev("delivery")]) == "delivery"

    def test_door(self):
        assert _categorize([_ev("door")]) == "access"

    def test_loitering_behavior(self):
        ev = _ev("behavior", metadata={"behavior": "loitering"})
        assert _categorize([ev]) == "security"

    def test_environment(self):
        assert _categorize([_ev("environment")]) == "environment"

    def test_person(self):
        assert _categorize([_ev("person")]) == "activity"

    def test_vehicle(self):
        assert _categorize([_ev("vehicle")]) == "activity"

    def test_arrival_beats_environment(self):
        assert _categorize([_ev("arrival"), _ev("environment")]) == "arrival"

    def test_other_types_fallback_to_activity(self):
        assert _categorize([_ev("scene")]) == "activity"


# ── _group_events_into_windows ─────────────────────────────────────────────

class TestGroupEventsIntoWindows:
    def test_empty_returns_empty(self):
        assert _group_events_into_windows([]) == []

    def test_single_event(self):
        windows = _group_events_into_windows([_ev("person")])
        assert len(windows) == 1
        assert len(windows[0]) == 1

    def test_events_within_window_grouped(self):
        evs = [_ev("person", ts_offset_s=0), _ev("vehicle", ts_offset_s=60)]
        windows = _group_events_into_windows(evs)
        assert len(windows) == 1
        assert len(windows[0]) == 2

    def test_events_beyond_window_split(self):
        evs = [
            _ev("person", ts_offset_s=0),
            _ev("vehicle", ts_offset_s=BEAT_WINDOW_SEC + 10),
        ]
        windows = _group_events_into_windows(evs)
        assert len(windows) == 2

    def test_sorts_by_timestamp(self):
        evs = [
            _ev("vehicle", ts_offset_s=100),
            _ev("person", ts_offset_s=0),
        ]
        windows = _group_events_into_windows(evs)
        assert len(windows) == 1
        assert windows[0][0]["type"] == "person"

    def test_naive_timestamps_handled(self):
        now = datetime(2026, 6, 6, 12, 0, 0)  # naive
        ev = {"timestamp": now.isoformat(), "type": "person", "location": {"zone": "front"}, "event_id": "t"}
        windows = _group_events_into_windows([ev])
        assert len(windows) == 1


# ── generate_story ─────────────────────────────────────────────────────────

class TestGenerateStory:
    @pytest.fixture
    def stories_dir(self, tmp_path: Path, monkeypatch) -> Path:
        d = tmp_path / "stories"
        import story_engine
        monkeypatch.setattr(story_engine, "STORIES_DIR", d)
        return d

    @pytest.fixture
    def timeline_with_events(self, tmp_path: Path, monkeypatch) -> Path:
        import timeline_api

        path = tmp_path / "timeline.jsonl"
        date = datetime(2026, 6, 6, tzinfo=TZ)
        evs = [
            {
                "timestamp": date.replace(hour=8, minute=0).isoformat(),
                "type": "arrival",
                "location": {"zone": "front", "camera": "front"},
                "identity": {"name": "Thomas"},
                "event_id": "arr_1",
            },
            {
                "timestamp": date.replace(hour=10, minute=0).isoformat(),
                "type": "delivery",
                "location": {"zone": "front", "camera": "front"},
                "event_id": "del_1",
            },
            {
                "timestamp": date.replace(hour=12, minute=0).isoformat(),
                "type": "person",
                "location": {"zone": "backyard", "camera": "backyard"},
                "event_id": "per_1",
            },
        ]
        path.write_text("\n".join(json.dumps(e) for e in evs) + "\n", encoding="utf-8")
        monkeypatch.setattr(timeline_api, "DEFAULT_TIMELINE", path)
        return path

    def test_generate_story_structure(self, stories_dir, timeline_with_events):
        story = generate_story("2026-06-06")
        assert story["date"] == "2026-06-06"
        assert "title" in story
        assert "summary" in story
        assert "beats" in story
        assert "stats" in story
        assert "generated_at" in story

    def test_generate_story_beats_not_empty(self, stories_dir, timeline_with_events):
        story = generate_story("2026-06-06")
        assert len(story["beats"]) > 0

    def test_generate_story_arrival_in_beats(self, stories_dir, timeline_with_events):
        story = generate_story("2026-06-06")
        texts = [b["text"] for b in story["beats"]]
        assert any("Thomas" in t for t in texts)

    def test_generate_story_writes_file(self, stories_dir, timeline_with_events):
        generate_story("2026-06-06")
        out = stories_dir / "2026-06-06.json"
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["date"] == "2026-06-06"

    def test_generate_story_quiet_day(self, tmp_path, stories_dir, monkeypatch):
        import timeline_api

        empty_path = tmp_path / "empty.jsonl"
        empty_path.write_text("", encoding="utf-8")
        monkeypatch.setattr(timeline_api, "DEFAULT_TIMELINE", empty_path)

        story = generate_story("2026-06-06")
        assert story["beats"] == []
        assert "quiet" in story["summary"].lower()

    def test_generate_story_skips_scene_only_windows(self, tmp_path, stories_dir, monkeypatch):
        import timeline_api

        path = tmp_path / "timeline.jsonl"
        date = datetime(2026, 6, 6, tzinfo=TZ)
        evs = [
            {
                "timestamp": date.replace(hour=9).isoformat(),
                "type": "scene",
                "location": {"zone": "front", "camera": "front"},
                "event_id": "scene_1",
            },
            {
                "timestamp": date.replace(hour=9, minute=1).isoformat(),
                "type": "occupancy",
                "location": {"zone": "front", "camera": "front"},
                "metadata": {"scenario": "PersonOccupancy", "phase": "start"},
                "event_id": "occ_1",
            },
        ]
        path.write_text("\n".join(json.dumps(e) for e in evs) + "\n", encoding="utf-8")
        monkeypatch.setattr(timeline_api, "DEFAULT_TIMELINE", path)

        story = generate_story("2026-06-06")
        assert story["beats"] == []

    def test_beat_has_required_fields(self, stories_dir, timeline_with_events):
        story = generate_story("2026-06-06")
        for beat in story["beats"]:
            assert "time" in beat
            assert "timestamp" in beat
            assert "text" in beat
            assert "category" in beat
            assert "event_ids" in beat

    def test_summary_mentions_arrivals(self, stories_dir, timeline_with_events):
        story = generate_story("2026-06-06")
        assert "arrival" in story["summary"].lower()

    def test_summary_persons_without_arrival(self, tmp_path, stories_dir, monkeypatch):
        import timeline_api

        path = tmp_path / "timeline.jsonl"
        date = datetime(2026, 6, 6, tzinfo=TZ)
        evs = [
            {
                "timestamp": date.replace(hour=8).isoformat(),
                "type": "person",
                "location": {"zone": "front", "camera": "front"},
                "event_id": "per_1",
            },
            {
                "timestamp": date.replace(hour=9).isoformat(),
                "type": "vehicle",
                "location": {"zone": "driveway_wide", "camera": "driveway_wide"},
                "event_id": "veh_1",
            },
        ]
        path.write_text("\n".join(json.dumps(e) for e in evs) + "\n", encoding="utf-8")
        monkeypatch.setattr(timeline_api, "DEFAULT_TIMELINE", path)

        story = generate_story("2026-06-06")
        assert "person detection" in story["summary"]
        assert "vehicle detection" in story["summary"]
