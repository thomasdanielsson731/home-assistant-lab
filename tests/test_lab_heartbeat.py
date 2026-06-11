"""Tests for scripts/lab_heartbeat.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from event_store import EventStore, TZ
from lab_heartbeat import (
    bridge_zone,
    is_stale,
    last_metric_ts_for_zone,
    read_bridge_heartbeats,
    write_heartbeat,
)


class TestBridgeZone:
    def test_prefix(self):
        assert bridge_zone("timeline_server") == "_bridge/timeline_server"


class TestWriteHeartbeat:
    def test_appends_metric_row(self, tmp_path: Path):
        store = EventStore(events_root=tmp_path / "events")
        write_heartbeat("event_normalizer", store)
        lines = store.metrics_jsonl.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["zone"] == "_bridge/event_normalizer"
        assert row["values"]["alive"] == 1


class TestReadBridgeHeartbeats:
    def test_latest_per_service(self, tmp_path: Path):
        store = EventStore(events_root=tmp_path / "events")
        old = (datetime.now(TZ) - timedelta(minutes=10)).isoformat()
        new = datetime.now(TZ).isoformat()
        store.write_metric(old, "_bridge/audio_bridge", {"alive": 1})
        store.write_metric(new, "_bridge/audio_bridge", {"alive": 1})
        store.write_metric(new, "_bridge/aoa_bridge", {"alive": 1})

        heartbeats = read_bridge_heartbeats(store.metrics_jsonl)
        assert set(heartbeats) == {"audio_bridge", "aoa_bridge"}
        assert heartbeats["audio_bridge"] == datetime.fromisoformat(new)

    def test_ignores_non_bridge_zones(self, tmp_path: Path):
        store = EventStore(events_root=tmp_path / "events")
        store.write_metric(datetime.now(TZ).isoformat(), "driveway_env", {"temperature": 20})
        assert read_bridge_heartbeats(store.metrics_jsonl) == {}


class TestIsStale:
    def test_fresh_not_stale(self):
        ts = datetime.now(TZ) - timedelta(seconds=30)
        assert not is_stale(ts, 300)

    def test_old_is_stale(self):
        ts = datetime.now(TZ) - timedelta(minutes=10)
        assert is_stale(ts, 300)


class TestLastMetricForZone:
    def test_returns_latest(self, tmp_path: Path):
        store = EventStore(events_root=tmp_path / "events")
        old = (datetime.now(TZ) - timedelta(hours=1)).isoformat()
        new = datetime.now(TZ).isoformat()
        store.write_metric(old, "driveway_env", {"temperature": 10})
        store.write_metric(new, "driveway_env", {"temperature": 12})
        ts = last_metric_ts_for_zone(store.metrics_jsonl, "driveway_env")
        assert ts == datetime.fromisoformat(new)
