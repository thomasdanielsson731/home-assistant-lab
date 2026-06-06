"""Tests for scripts/timeline_api.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from event_store import TZ
from timeline_api import build_occupancy_blocks, load_events, load_metrics, parse_time_range


@pytest.fixture
def timeline_file(tmp_path: Path) -> Path:
    path = tmp_path / "timeline.jsonl"
    now = datetime.now(TZ)
    events = [
        {
            "timestamp": (now - timedelta(minutes=10)).isoformat(),
            "type": "occupancy",
            "location": {"zone": "front", "camera": "front"},
            "metadata": {"scenario": "PersonOccupancy", "phase": "start"},
            "event_id": "occ_start",
        },
        {
            "timestamp": (now - timedelta(minutes=5)).isoformat(),
            "type": "occupancy",
            "location": {"zone": "front", "camera": "front"},
            "metadata": {"scenario": "PersonOccupancy", "phase": "end", "duration_seconds": 300},
            "event_id": "occ_end",
        },
        {
            "timestamp": now.isoformat(),
            "type": "person",
            "location": {"zone": "front", "camera": "front"},
            "event_id": "p1",
        },
    ]
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return path


def test_build_occupancy_blocks(timeline_file: Path):
    events = load_events(hours=24, timeline_path=timeline_file, newest_first=False)
    blocks = build_occupancy_blocks(events, hours=None)
    assert len(blocks) == 1
    assert blocks[0]["zone"] == "front"
    assert blocks[0]["duration_seconds"] == 300


def test_load_metrics(tmp_path: Path):
    path = tmp_path / "metrics.jsonl"
    now = datetime.now(TZ)
    old = now - timedelta(days=2)
    rows = [
        {"timestamp": now.isoformat(), "zone": "driveway_env", "values": {"co2": 400}},
        {"timestamp": old.isoformat(), "zone": "front", "values": {"spl": 55.0}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    metrics = load_metrics(hours=24, metrics_path=path)
    assert len(metrics) == 1
    assert metrics[0]["metric"] == "co2"


def test_load_events_custom_range(timeline_file: Path):
    now = datetime.now(TZ)
    since = now - timedelta(minutes=15)
    until = now + timedelta(minutes=1)
    events = load_events(
        hours=None,
        since=since,
        until=until,
        timeline_path=timeline_file,
        newest_first=False,
    )
    assert len(events) == 3


def test_load_metrics_custom_range(tmp_path: Path):
    path = tmp_path / "metrics.jsonl"
    now = datetime.now(TZ)
    rows = [
        {"timestamp": (now - timedelta(hours=1)).isoformat(), "zone": "front", "values": {"spl": 50}},
        {"timestamp": now.isoformat(), "zone": "front", "values": {"spl": 55}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    since = now - timedelta(minutes=30)
    metrics = load_metrics(hours=None, since=since, until=now + timedelta(seconds=1), metrics_path=path)
    assert len(metrics) == 1


def test_parse_time_range_custom():
    now = datetime.now(TZ)
    since = now - timedelta(hours=2)
    qs = {"from": [since.isoformat()], "to": [now.isoformat()]}
    s, u, hours = parse_time_range(qs)
    assert hours is None
    assert s <= u


def test_parse_time_range_hours_fallback():
    s, u, hours = parse_time_range({})
    assert hours == 24
    assert s < u
