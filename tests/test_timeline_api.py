"""Tests for scripts/timeline_api.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from event_store import TZ
from timeline_api import build_occupancy_blocks, latest_occupancy_by_zone, load_events, load_metrics, parse_time_range


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


def _occ_event(tmp_path: Path, ts_iso: str, phase: str, duration: int | None = None, zone: str = "front") -> dict:
    ev: dict = {
        "timestamp": ts_iso,
        "type": "occupancy",
        "location": {"zone": zone, "camera": zone},
        "metadata": {"scenario": "PersonOccupancy", "phase": phase},
        "event_id": f"{zone}_{phase}_{ts_iso[:16]}",
    }
    if duration is not None:
        ev["metadata"]["duration_seconds"] = duration
    return ev


def test_build_occupancy_blocks_merges_adjacent_close_gap(tmp_path: Path):
    now = datetime.now(TZ)
    # Block A: -600s → -300s (10→5 min ago)
    # Block B: -280s → -60s (starts 20s after A ends, within 30s gap → merged)
    events = [
        _occ_event(tmp_path, (now - timedelta(seconds=600)).isoformat(), "start"),
        _occ_event(tmp_path, (now - timedelta(seconds=300)).isoformat(), "end", duration=300),
        _occ_event(tmp_path, (now - timedelta(seconds=280)).isoformat(), "start"),
        _occ_event(tmp_path, (now - timedelta(seconds=60)).isoformat(), "end", duration=220),
    ]
    path = tmp_path / "timeline.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    all_events = load_events(hours=1, timeline_path=path, newest_first=False)
    blocks = build_occupancy_blocks(all_events, hours=None)
    assert len(blocks) == 1
    assert blocks[0]["zone"] == "front"
    # Merged block spans -600s to -60s = 540s
    assert blocks[0]["duration_seconds"] >= 540


def test_build_occupancy_blocks_gap_over_30s_not_merged(tmp_path: Path):
    now = datetime.now(TZ)
    # Block A ends at -300s; Block B starts at -260s (40s gap > 30s → NOT merged)
    events = [
        _occ_event(tmp_path, (now - timedelta(seconds=600)).isoformat(), "start"),
        _occ_event(tmp_path, (now - timedelta(seconds=300)).isoformat(), "end", duration=300),
        _occ_event(tmp_path, (now - timedelta(seconds=260)).isoformat(), "start"),
        _occ_event(tmp_path, (now - timedelta(seconds=60)).isoformat(), "end", duration=200),
    ]
    path = tmp_path / "timeline.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    all_events = load_events(hours=1, timeline_path=path, newest_first=False)
    blocks = build_occupancy_blocks(all_events, hours=None)
    assert len(blocks) == 2


def test_build_occupancy_blocks_filters_short_blocks(tmp_path: Path):
    now = datetime.now(TZ)
    events = [
        _occ_event(tmp_path, (now - timedelta(seconds=90)).isoformat(), "start"),
        _occ_event(tmp_path, (now - timedelta(seconds=70)).isoformat(), "end", duration=20),
        _occ_event(tmp_path, (now - timedelta(minutes=10)).isoformat(), "start"),
        _occ_event(tmp_path, (now - timedelta(minutes=5)).isoformat(), "end", duration=300),
    ]
    path = tmp_path / "timeline.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    all_events = load_events(hours=1, timeline_path=path, newest_first=False)
    blocks = build_occupancy_blocks(all_events, hours=None)
    assert len(blocks) == 1
    assert blocks[0]["duration_seconds"] == 300


def test_build_occupancy_blocks_separate_zones_not_merged(tmp_path: Path):
    now = datetime.now(TZ)
    events = [
        _occ_event(tmp_path, (now - timedelta(minutes=10)).isoformat(), "start", zone="front"),
        _occ_event(tmp_path, (now - timedelta(minutes=5)).isoformat(), "end", duration=300, zone="front"),
        _occ_event(tmp_path, (now - timedelta(minutes=8)).isoformat(), "start", zone="driveway_wide"),
        _occ_event(tmp_path, (now - timedelta(minutes=3)).isoformat(), "end", duration=300, zone="driveway_wide"),
    ]
    path = tmp_path / "timeline.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    all_events = load_events(hours=1, timeline_path=path, newest_first=False)
    blocks = build_occupancy_blocks(all_events, hours=None)
    assert len(blocks) == 2
    zones = {b["zone"] for b in blocks}
    assert zones == {"front", "driveway_wide"}


def test_latest_occupancy_by_zone(tmp_path: Path):
    now = datetime.now(TZ)
    blocks = [
        {
            "zone": "front",
            "scenario": "PersonOccupancy",
            "start": (now - timedelta(hours=2)).isoformat(),
            "end": (now - timedelta(hours=1)).isoformat(),
            "duration_seconds": 3600,
        },
        {
            "zone": "front",
            "scenario": "PersonOccupancy",
            "start": (now - timedelta(minutes=30)).isoformat(),
            "end": (now - timedelta(minutes=20)).isoformat(),
            "duration_seconds": 600,
        },
        {
            "zone": "driveway_wide",
            "scenario": "VehicleOcc",
            "start": (now - timedelta(minutes=10)).isoformat(),
            "end": now.isoformat(),
            "duration_seconds": 600,
        },
    ]
    # build_occupancy_blocks returns newest first; simulate that ordering
    blocks_sorted = sorted(blocks, key=lambda b: b["start"], reverse=True)
    latest = latest_occupancy_by_zone(blocks_sorted)
    assert set(latest.keys()) == {"front", "driveway_wide"}
    # front: the most recent block (30-min ago) should win
    assert latest["front"]["duration_seconds"] == 600
