"""Tests for scripts/event_normalizer.py handlers."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from event_store import make_summary


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


class TestHandleDoubleTake:
    def test_attaches_identity(self, normalizer, store):
        with patch("event_normalizer._download_snapshot", return_value=False):
            normalizer.handle_frigate_event(FRIGATE_END_PERSON)

        normalizer.handle_double_take({
            "camera": "front",
            "match": {"name": "thomas", "confidence": 92},
        })
        event = json.loads(store.timeline_jsonl.read_text().strip())
        assert event["identity"]["name"] == "Thomas"
        assert event["identity"]["confidence"] == pytest.approx(0.92)

    def test_ignores_missing_match(self, normalizer, store):
        normalizer.handle_double_take({"camera": "front"})
        assert not store.timeline_jsonl.exists()

    def test_handles_list_payload(self, normalizer, store):
        with patch("event_normalizer._download_snapshot", return_value=False):
            normalizer.handle_frigate_event(FRIGATE_END_PERSON)

        msg = MagicMock()
        msg.topic = "double_take/matches"
        msg.payload = json.dumps([
            {"camera": "front", "match": {"name": "anna", "confidence": 88}},
        ]).encode()
        normalizer.on_message(None, None, msg)
        event = json.loads(store.timeline_jsonl.read_text().strip())
        assert event["identity"]["name"] == "Anna"


class TestHandleEnvMetric:
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
    def test_aoa_occupancy_start_end(self, normalizer, store):
        topic = "axis/front/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active"
        normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": True}}))
        normalizer.handle_aoa_occupancy(topic, json.dumps({"Data": {"active": False}}))
        lines = store.timeline_jsonl.read_text().strip().splitlines()
        assert len(lines) == 2
        start = json.loads(lines[0])
        end = json.loads(lines[1])
        assert start["type"] == "occupancy"
        assert start["metadata"]["phase"] == "start"
        assert end["metadata"]["phase"] == "end"

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
