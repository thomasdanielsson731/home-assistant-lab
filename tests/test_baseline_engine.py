"""Tests for scripts/baseline_engine.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from event_store import TZ
from baseline_engine import (
    build_event_baselines,
    build_metric_baselines,
    run_pass,
    _is_anomaly,
)


def _metric_row(zone: str, metric: str, value: float, hour: int, day_offset: int = 0) -> dict:
    ts = datetime(2026, 6, 1, hour, 0, tzinfo=TZ) + timedelta(days=day_offset)
    return {"timestamp": ts.isoformat(), "zone": zone, "values": {metric: value}}


def _person_event(zone: str, hour: int, day_offset: int = 0) -> dict:
    ts = datetime(2026, 6, 1, hour, 0, tzinfo=TZ) + timedelta(days=day_offset)
    return {
        "timestamp": ts.isoformat(),
        "type": "person",
        "location": {"zone": zone},
        "event_id": f"p_{zone}_{day_offset}_{hour}",
    }


class TestMetricBaselines:
    def test_builds_mean_and_std(self):
        rows = [_metric_row("front", "spl", 50.0 + i, 12, d) for d in range(10) for i in range(3)]
        baselines = build_metric_baselines(rows)
        key = "front:spl:12"
        assert key in baselines
        assert baselines[key]["n"] >= 5
        assert baselines[key]["mean"] > 0

    def test_insufficient_samples_skipped(self):
        rows = [_metric_row("front", "spl", 55.0, 12, 0)]
        assert "front:spl:12" not in build_metric_baselines(rows)


class TestEventBaselines:
    def test_counts_per_hour(self):
        rows = [_person_event("front", 8, d) for d in range(7)]
        baselines = build_event_baselines(rows)
        assert "front:person:8" in baselines


class TestIsAnomaly:
    def test_above_two_sigma(self):
        assert _is_anomaly(100.0, {"mean": 50.0, "std": 10.0})

    def test_within_normal(self):
        assert not _is_anomaly(55.0, {"mean": 50.0, "std": 10.0})


class TestRunPass:
    @pytest.fixture
    def store(self, tmp_path: Path, monkeypatch):
        import baseline_engine as be

        events = tmp_path / "events"
        events.mkdir()
        metrics = events / "metrics.jsonl"
        timeline = events / "timeline.jsonl"

        base_rows = [_metric_row("front", "spl", 50.0, 12, d) for d in range(14)]
        spike = _metric_row("front", "spl", 120.0, 12, 14)
        metrics.write_text(
            "\n".join(json.dumps(r) for r in base_rows + [spike]) + "\n",
            encoding="utf-8",
        )
        timeline.write_text("", encoding="utf-8")

        from event_store import EventStore

        s = EventStore(events_root=events)
        monkeypatch.setattr(be, "BASELINE_DAYS", 14)
        monkeypatch.setattr(be, "MIN_SAMPLES", 5)
        return s

    def test_writes_baselines_file(self, store):
        result = run_pass(store)
        out = store.aggregates_dir / "baselines.json"
        assert out.exists()
        assert result["metric_baselines"] >= 1
