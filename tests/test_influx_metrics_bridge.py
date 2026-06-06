"""Tests for scripts/influx_metrics_bridge.py."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

import influx_metrics_bridge as bridge


@pytest.fixture
def metrics_file(tmp_path: Path, monkeypatch):
    path = tmp_path / "metrics.jsonl"
    state = tmp_path / "state.json"
    monkeypatch.setattr(bridge, "METRICS_PATH", path)
    monkeypatch.setattr(bridge, "STATE_PATH", state)
    return path


def test_format_lines_line_protocol():
    rows = [
        {
            "timestamp": "2026-06-06T18:00:00+02:00",
            "zone": "driveway_env",
            "values": {"co2": 420, "temperature": 18.5},
        }
    ]
    payload = bridge.format_lines(rows)
    assert "home_metrics,zone=driveway_env" in payload
    assert "co2=420i" in payload
    assert "temperature=18.5" in payload


def test_read_new_rows_tracks_offset(metrics_file: Path):
    metrics_file.write_text(
        json.dumps({
            "timestamp": "2026-06-06T18:00:00+02:00",
            "zone": "front",
            "values": {"spl": 55.0},
        }) + "\n",
        encoding="utf-8",
    )
    rows, offset = bridge.read_new_rows()
    assert len(rows) == 1
    assert offset > 0
    bridge.save_state(offset)

    rows2, _ = bridge.read_new_rows()
    assert rows2 == []


def test_run_once_writes_and_advances(metrics_file: Path, monkeypatch):
    metrics_file.write_text(
        json.dumps({
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "zone": "driveway_env",
            "values": {"aqi": 3},
        }) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(bridge, "INFLUX_URL", "http://127.0.0.1:8086")
    monkeypatch.setattr(bridge, "INFLUX_TOKEN", "test-token")

    with patch.object(bridge, "write_to_influx", return_value=True) as mock_write:
        bridge.run_once()
        mock_write.assert_called_once()
    assert bridge.load_state()["offset"] > 0


def test_run_once_idle_without_influx_url(metrics_file: Path, monkeypatch):
    metrics_file.write_text(
        json.dumps({
            "timestamp": "2026-06-06T18:00:00+02:00",
            "zone": "front",
            "values": {"spl": 50},
        }) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(bridge, "INFLUX_URL", "")
    bridge.run_once()
    assert bridge.load_state()["offset"] == 0
