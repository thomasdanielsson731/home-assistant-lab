"""Tests for scripts/event_normalizer.py handlers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from event_store import TZ, make_summary


FRIGATE_END_PERSON = {
    "type": "end",
    "after": {
        "id": "abc-123",
        "camera": "front",
        "label": "person",
        "top_score": 0.87,
        "start_time": 1000.0,
        "end_time": 1008.5,
    },
}

FRIGATE_END_CAR = {
    "type": "end",
    "after": {
        "id": "car-456",
        "camera": "driveway_wide",
        "label": "car",
        "top_score": 0.75,
    },
}


class TestHandleFrigateEvent:
    def test_ignores_non_end_events(self, normalizer, store):
        normalizer.handle_frigate_event({"type": "new", "after": {"label": "person"}})
        assert not store.timeline_jsonl.exists()

    def test_ignores_unknown_labels(self, normalizer, store):
        payload = {"type": "end", "after": {"camera": "front", "label": "dog"}}
        normalizer.handle_frigate_event(payload)
        assert not store.timeline_jsonl.exists()

    @patch("event_normalizer._download_snapshot", return_value=False)
    def test_writes_person_event(self, mock_snap, normalizer, store):
        normalizer.handle_frigate_event(FRIGATE_END_PERSON)
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["type"] == "person"
        assert event["location"] == {"zone": "front", "camera": "front"}
        assert event["confidence"] == 0.87
        assert event["metadata"]["frigate_id"] == "abc-123"
        assert event["source"] == "frigate"

    @patch("event_normalizer._download_snapshot", return_value=True)
    def test_includes_snapshot_path(self, mock_snap, normalizer, store):
        normalizer.handle_frigate_event(FRIGATE_END_PERSON)
        event = json.loads(store.timeline_jsonl.read_text().strip())
        assert "snapshot" in event
        assert event["snapshot"]["best_picture"].endswith(".jpg")

    def test_maps_car_to_vehicle(self, normalizer, store):
        with patch("event_normalizer._download_snapshot", return_value=False):
            normalizer.handle_frigate_event(FRIGATE_END_CAR)
        event = json.loads(store.timeline_jsonl.read_text().strip())
        assert event["type"] == "vehicle"
        assert event["location"]["zone"] == "driveway"


    def test_ignores_until_aqi_metric(self, normalizer, store):
        normalizer.handle_env_metric("axis/driveway_env/air/temperature", "18.5")
        normalizer.handle_env_metric("axis/driveway_env/air/co2", "431")
        assert not store.timeline_jsonl.exists()

    def test_emits_on_aqi_after_interval(self, normalizer, store):
        normalizer._last_env_event = 0
        normalizer.handle_env_metric("axis/driveway_env/air/temperature", "18.5")
        normalizer.handle_env_metric("axis/driveway_env/air/humidity", "55")
        normalizer.handle_env_metric("axis/driveway_env/air/co2", "431")
        normalizer.handle_env_metric("axis/driveway_env/air/aqi", "17")

        lines = store.timeline_jsonl.read_text().strip().splitlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["type"] == "environment"
        assert event["metadata"]["temperature"] == 18.5
        assert event["metadata"]["co2"] == 431
        assert event["metadata"]["aqi"] == 17

    def test_respects_env_interval(self, normalizer, store):
        import time

        normalizer._last_env_event = time.time()
        normalizer._env_cache = {"temperature": 18.0, "aqi": 10}
        normalizer.handle_env_metric("axis/driveway_env/air/aqi", "10")
        assert not store.timeline_jsonl.exists()

    def test_ignores_invalid_values(self, normalizer, store):
        normalizer.handle_env_metric("axis/driveway_env/air/temperature", "not-a-number")
        normalizer.handle_env_metric("axis/driveway_env/air/aqi", "17")
        assert not store.timeline_jsonl.exists()


class TestOnMessage:
    def test_routes_frigate_topic(self, normalizer, store):
        with patch("event_normalizer._download_snapshot", return_value=False):
            msg = MagicMock()
            msg.topic = "frigate/events"
            msg.payload = json.dumps(FRIGATE_END_PERSON).encode()
            normalizer.on_message(None, None, msg)
        assert store.timeline_jsonl.exists()

    def test_handles_bad_json_gracefully(self, normalizer, store, caplog):
        msg = MagicMock()
        msg.topic = "frigate/events"
        msg.payload = b"{not json"
        normalizer.on_message(None, None, msg)
        assert not store.timeline_jsonl.exists()


class TestDownloadSnapshot:
    def test_tries_ha_proxy_first(self, normalizer, tmp_path, monkeypatch):
        monkeypatch.setattr(normalizer, "HA_TOKEN", "token123")
        dest = tmp_path / "snap.jpg"
        response = MagicMock()
        response.status_code = 200
        response.headers = {"content-type": "image/jpeg"}
        response.content = b"fake-jpeg"

        with patch("event_normalizer.requests.get", return_value=response) as mock_get:
            assert normalizer._download_snapshot("evt-id", dest) is True
            assert dest.read_bytes() == b"fake-jpeg"
            mock_get.assert_called_once()
            assert "8123/api/frigate" in mock_get.call_args[0][0]

    def test_returns_false_on_failure(self, normalizer, tmp_path):
        import requests

        with patch(
            "event_normalizer.requests.get",
            side_effect=requests.RequestException("network"),
        ):
            assert normalizer._download_snapshot("evt-id", tmp_path / "x.jpg") is False


class TestAoaAndScene:
    def test_aoa_occupancy_ignores_short_duration(self, normalizer, store):
        topic = "axis/front/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active"
        t0 = datetime(2026, 6, 7, 10, 0, 0, tzinfo=TZ)
        t1 = t0 + timedelta(seconds=30)
        with patch("event_normalizer.datetime") as mock_dt:
            mock_dt.now.side_effect = [t0, t1]
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": True}}))
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": False}}))
        assert not store.timeline_jsonl.exists()

    def test_aoa_occupancy_writes_when_duration_ge_120s(self, normalizer, store):
        topic = "axis/front/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active"
        t0 = datetime(2026, 6, 7, 10, 0, 0, tzinfo=TZ)
        t1 = t0 + timedelta(seconds=150)
        with patch("event_normalizer.datetime") as mock_dt:
            mock_dt.now.side_effect = [t0, t1]
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": True}}))
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": False}}))
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        assert len(lines) == 2
        start = json.loads(lines[0])
        end = json.loads(lines[1])
        assert start["metadata"]["phase"] == "start"
        assert end["metadata"]["phase"] == "end"
        assert end["metadata"]["duration_seconds"] == 150

    def test_aoa_occupancy_skips_vehicle_scenario(self, normalizer, store):
        topic = "axis/front/event/ObjectAnalytics/ScenarioOccupancy/VehicleOcc/Active"
        t0 = datetime(2026, 6, 7, 10, 0, 0, tzinfo=TZ)
        t1 = t0 + timedelta(seconds=150)
        with patch("event_normalizer.datetime") as mock_dt:
            mock_dt.now.side_effect = [t0, t1]
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": True}}))
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": False}}))
        assert not store.timeline_jsonl.exists()

    def test_aoa_occupancy_cooldown_blocks_quick_retrigger(self, normalizer, store):
        topic = "axis/front/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active"
        t0 = datetime(2026, 6, 7, 10, 0, 0, tzinfo=TZ)
        t_end = t0 + timedelta(seconds=150)
        t_retrigger = t0 + timedelta(seconds=180)  # 30s after end — within 90s cooldown
        with patch("event_normalizer.datetime") as mock_dt:
            mock_dt.now.side_effect = [t0, t_end, t_retrigger]
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": True}}))
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": False}}))
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": True}}))
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_aoa_occupancy_confirms_start_while_still_active(self, normalizer, store):
        topic = "axis/storage_ext/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active"
        t0 = datetime(2026, 6, 7, 10, 0, 0, tzinfo=TZ)
        t60 = t0 + timedelta(seconds=120)
        t150 = t0 + timedelta(seconds=150)
        with patch("event_normalizer.datetime") as mock_dt:
            mock_dt.now.side_effect = [t0, t60, t150]
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": True}}))
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": True}}))
            normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": False}}))
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        assert len(lines) == 2
        start = json.loads(lines[0])
        end = json.loads(lines[1])
        assert start["timestamp"] == t0.isoformat(timespec="seconds")
        assert end["metadata"]["duration_seconds"] == 150

    def test_scene_frame_emits_on_change(self, normalizer, store):
        topic = "axis/front/scene/frame"
        payload = json.dumps({"detections": [{"type": "Human", "score": 0.9}]})
        normalizer.handle_scene_frame(topic, payload)
        normalizer.handle_scene_frame(topic, payload)
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["type"] == "scene"

    def test_audio_spl_writes_metric(self, normalizer, store):
        topic = "axis/front/audio/spl"
        normalizer.handle_audio_spl(topic, json.dumps({"max_spl": 55.2}))
        assert store.metrics_jsonl.exists()
        row = json.loads(store.metrics_jsonl.read_text().strip())
        assert row["values"]["spl"] == 55.2

    def test_scene_frame_counts_bicycles(self, normalizer, store):
        topic = "axis/driveway_id/scene/frame"
        payload = json.dumps({"detections": [{"type": "Human"}, {"type": "Bike"}]})
        normalizer.handle_scene_frame(topic, payload)
        row = json.loads(store.timeline_jsonl.read_text().strip())
        assert row["metadata"]["bicycles"] == 1

    def test_door_lock_unlock_emits_event(self, normalizer, store):
        topic = "homeassistant/lock/front_door/state"
        normalizer.handle_door_lock(topic, "unlocked")
        normalizer.handle_door_lock(topic, "unlocked")
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["type"] == "door"
        assert row["metadata"]["action"] == "unlocked"
        assert row["location"]["zone"] == "front"

    def test_smoke_sensor_on_emits_event(self, normalizer, store, monkeypatch):
        monkeypatch.setattr(normalizer, "SMOKE_ZONE_BY_ENTITY", {"heiman_hs1sa_e_plus_ias_zon_2": "kok"})
        topic = "homeassistant/binary_sensor/heiman_hs1sa_e_plus_ias_zon_2/state"
        normalizer.handle_smoke_sensor(topic, "off")
        normalizer.handle_smoke_sensor(topic, "on")
        normalizer.handle_smoke_sensor(topic, "on")
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["type"] == "smoke"
        assert row["location"]["zone"] == "kok"
        assert row["metadata"]["entity_id"] == "binary_sensor.heiman_hs1sa_e_plus_ias_zon_2"

    def test_smoke_sensor_ignores_unmapped_entity(self, normalizer, store):
        normalizer.handle_smoke_sensor("homeassistant/binary_sensor/other/state", "on")
        assert not store.timeline_jsonl.exists()


class TestIndoorTemp:
    def test_writes_metric_for_mapped_entity(self, normalizer, store, monkeypatch):
        monkeypatch.setattr(
            normalizer,
            "INDOOR_TEMP_BY_ENTITY",
            {"heiman_hs1sa_e_plus_temperatur_3": "kok"},
        )
        topic = "homeassistant/sensor/heiman_hs1sa_e_plus_temperatur_3/state"
        normalizer.handle_indoor_temp(topic, "21.5")
        lines = store.metrics_jsonl.read_text().strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["zone"] == "kok"
        assert row["values"]["temperature"] == 21.5

    def test_throttles_small_changes(self, normalizer, store, monkeypatch):
        monkeypatch.setattr(
            normalizer,
            "INDOOR_TEMP_BY_ENTITY",
            {"heiman_hs1sa_e_plus_temperatur_3": "kok"},
        )
        topic = "homeassistant/sensor/heiman_hs1sa_e_plus_temperatur_3/state"
        normalizer.handle_indoor_temp(topic, "21.0")
        normalizer.handle_indoor_temp(topic, "21.1")
        lines = store.metrics_jsonl.read_text().strip().splitlines()
        assert len(lines) == 1


class TestSceneTrack:
    def test_classify_behavior_passthrough_human(self, normalizer):
        assert normalizer._classify_behavior("Human", 3.0) == "passthrough"

    def test_classify_behavior_approach_human(self, normalizer):
        assert normalizer._classify_behavior("Human", 20.0) == "approach"

    def test_classify_behavior_loitering_human(self, normalizer):
        assert normalizer._classify_behavior("Human", 60.0) == "loitering"

    def test_classify_behavior_stopped_car(self, normalizer):
        assert normalizer._classify_behavior("Car", 30.0) == "stopped"

    def test_classify_behavior_parked_car(self, normalizer):
        assert normalizer._classify_behavior("Car", 200.0) == "parked"

    def test_classify_behavior_unknown_type_short(self, normalizer):
        assert normalizer._classify_behavior("Bicycle", 3.0) == "passthrough"

    def test_scene_track_new_stores_and_lost_writes_events(self, normalizer, store):
        topic_new = "axis/front/scene/track"
        normalizer.handle_scene_track(
            topic_new,
            json.dumps({"track_id": "t1", "event": "NEW", "type": "Human"}),
        )
        # No events written yet on NEW
        assert not store.timeline_jsonl.exists()

        normalizer.handle_scene_track(
            topic_new,
            json.dumps({"track_id": "t1", "event": "LOST", "type": "Human", "duration_sec": 20.0}),
        )
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        # Approach (20s Human) → person event + behavior event
        assert len(lines) == 2
        person_ev = json.loads(lines[0])
        behavior_ev = json.loads(lines[1])
        assert person_ev["type"] == "person"
        assert behavior_ev["type"] == "behavior"
        assert behavior_ev["metadata"]["behavior"] == "approach"

    def test_scene_track_skips_passthrough_behavior_event(self, normalizer, store):
        topic = "axis/front/scene/track"
        normalizer.handle_scene_track(
            topic,
            json.dumps({"track_id": "t2", "event": "LOST", "type": "Human", "duration_sec": 3.0}),
        )
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        # Passthrough → only the raw person event, no behavior event
        assert len(lines) == 1
        assert json.loads(lines[0])["type"] == "person"

    def test_scene_track_lost_without_prior_new_uses_zero_duration(self, normalizer, store):
        topic = "axis/driveway_wide/scene/track"
        normalizer.handle_scene_track(
            topic,
            json.dumps({"track_id": "orphan", "event": "LOST", "type": "Car"}),
        )
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        ev = json.loads(lines[0])
        assert ev["type"] == "vehicle"
        # 0s Car → stopped behavior, so behavior event also written
        assert any(json.loads(l)["type"] == "behavior" for l in lines)

    def test_scene_track_ignores_missing_track_id(self, normalizer, store):
        normalizer.handle_scene_track(
            "axis/front/scene/track",
            json.dumps({"event": "NEW", "type": "Human"}),
        )
        assert not store.timeline_jsonl.exists()

    def test_scene_track_ignores_bad_json(self, normalizer, store):
        normalizer.handle_scene_track("axis/front/scene/track", "{not json}")
        assert not store.timeline_jsonl.exists()
