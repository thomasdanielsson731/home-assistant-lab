#!/usr/bin/env python3
"""
Danielsson Home Intelligence — metric baselines + anomaly insights (Phase 6/7).

Builds zone×hour baselines from metrics.jsonl and emits insight events when
current samples exceed 2σ above the rolling baseline.

Usage:
  python scripts/baseline_engine.py          # one pass
  python scripts/baseline_engine.py --loop   # hourly (add-on)
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import sys

sys.path.insert(0, str(Path(__file__).parent))
from event_store import EventStore, TZ  # noqa: E402

log = logging.getLogger("baseline_engine")

REPO_ROOT = Path(__file__).parent.parent
BASELINE_DAYS = int(os.environ.get("BASELINE_DAYS", "14"))
SIGMA_THRESHOLD = float(os.environ.get("BASELINE_SIGMA", "2.0"))
MIN_SAMPLES = int(os.environ.get("BASELINE_MIN_SAMPLES", "5"))
POLL_SECONDS = int(os.environ.get("BASELINE_POLL_SECONDS", "3600"))
METRICS_OF_INTEREST = ("spl", "co2", "temperature")
EVENT_TYPES_OF_INTEREST = frozenset({"person", "vehicle"})


def _parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def _hour_key(dt: datetime) -> int:
    return dt.hour


def load_metrics_rows(path: Path, since: datetime) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_ts(row["timestamp"])
            if ts >= since:
                rows.append(row)
    return rows


def load_timeline_rows(path: Path, since: datetime) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("type") not in EVENT_TYPES_OF_INTEREST:
                continue
            ts = _parse_ts(row["timestamp"])
            if ts >= since:
                rows.append(row)
    return rows


def build_metric_baselines(rows: list[dict]) -> dict:
    buckets: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        zone = row.get("zone", "unknown")
        ts = _parse_ts(row["timestamp"])
        hour = _hour_key(ts)
        for metric, value in (row.get("values") or {}).items():
            if metric not in METRICS_OF_INTEREST:
                continue
            try:
                v = float(value)
            except (TypeError, ValueError):
                continue
            buckets[f"{zone}:{metric}:{hour}"].append(v)

    baselines: dict[str, dict] = {}
    for key, values in buckets.items():
        if len(values) < MIN_SAMPLES:
            continue
        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / len(values)
        std = math.sqrt(var)
        baselines[key] = {"mean": round(mean, 3), "std": round(std, 3), "n": len(values)}
    return baselines


def build_event_baselines(rows: list[dict]) -> dict:
    buckets: dict[str, int] = defaultdict(int)
    for row in rows:
        zone = (row.get("location") or {}).get("zone") or "unknown"
        ts = _parse_ts(row["timestamp"])
        hour = _hour_key(ts)
        etype = row["type"]
        buckets[f"{zone}:{etype}:{hour}"] += 1

    baselines: dict[str, dict] = {}
    for key, total in buckets.items():
        zone, etype, hour_s = key.split(":")
        hour = int(hour_s)
        days = max(BASELINE_DAYS, 1)
        mean = total / days
        std = max(math.sqrt(mean), 0.5)
        if mean < 0.5:
            continue
        baselines[key] = {"mean": round(mean, 3), "std": round(std, 3), "n": total}
    return baselines


def _is_anomaly(value: float, baseline: dict) -> bool:
    threshold = baseline["mean"] + SIGMA_THRESHOLD * baseline["std"]
    return value > threshold


def check_metric_anomalies(
    store: EventStore,
    baselines: dict,
    recent_rows: list[dict],
    cooldown: dict[str, datetime],
) -> int:
    emitted = 0
    now = datetime.now(TZ)
    for row in recent_rows:
        zone = row.get("zone", "unknown")
        ts = _parse_ts(row["timestamp"])
        hour = _hour_key(ts)
        for metric, raw in (row.get("values") or {}).items():
            if metric not in METRICS_OF_INTEREST:
                continue
            key = f"{zone}:{metric}:{hour}"
            base = baselines.get(key)
            if not base:
                continue
            try:
                value = float(raw)
            except (TypeError, ValueError):
                continue
            if not _is_anomaly(value, base):
                continue
            cd_key = f"metric:{key}"
            if cd_key in cooldown and now - cooldown[cd_key] < timedelta(hours=1):
                continue
            event = {
                "timestamp": row["timestamp"],
                "type": "environment",
                "location": {"zone": zone},
                "metadata": {
                    "anomaly": True,
                    "metric": metric,
                    "value": value,
                    "baseline_mean": base["mean"],
                    "baseline_std": base["std"],
                    "sigma": SIGMA_THRESHOLD,
                },
                "source": "baseline_engine",
                "enriched": True,
            }
            event["summary"] = (
                f"Unusual {metric} at {zone}: {value} "
                f"(baseline {base['mean']}±{base['std']})"
            )
            if store.write(event):
                cooldown[cd_key] = now
                emitted += 1
                log.info("Metric anomaly: %s %s=%s", zone, metric, value)
    return emitted


def check_event_anomalies(
    store: EventStore,
    baselines: dict,
    recent_events: list[dict],
    cooldown: dict[str, datetime],
) -> int:
    emitted = 0
    now = datetime.now(TZ)
    counts: dict[str, int] = defaultdict(int)
    for row in recent_events:
        zone = (row.get("location") or {}).get("zone") or "unknown"
        ts = _parse_ts(row["timestamp"])
        hour = _hour_key(ts)
        etype = row["type"]
        counts[f"{zone}:{etype}:{hour}"] += 1

    for key, count in counts.items():
        base = baselines.get(key)
        if not base or not _is_anomaly(float(count), base):
            continue
        zone, etype, hour_s = key.split(":")
        cd_key = f"event:{key}"
        if cd_key in cooldown and now - cooldown[cd_key] < timedelta(hours=1):
            continue
        event = {
            "timestamp": now.isoformat(timespec="seconds"),
            "type": "environment",
            "location": {"zone": zone},
            "metadata": {
                "anomaly": True,
                "event_type": etype,
                "count": count,
                "hour": int(hour_s),
                "baseline_mean": base["mean"],
                "baseline_std": base["std"],
            },
            "source": "baseline_engine",
            "enriched": True,
        }
        event["summary"] = (
            f"Unusual {etype} activity at {zone} "
            f"({count} vs baseline {base['mean']}±{base['std']})"
        )
        if store.write(event):
            cooldown[cd_key] = now
            emitted += 1
            log.info("Event-rate anomaly: %s %s count=%s", zone, etype, count)
    return emitted


def run_pass(store: EventStore | None = None) -> dict:
    store = store or EventStore()
    since = datetime.now(TZ) - timedelta(days=BASELINE_DAYS)
    recent_since = datetime.now(TZ) - timedelta(hours=1)

    metric_rows = load_metrics_rows(store.metrics_jsonl, since)
    event_rows = load_timeline_rows(store.timeline_jsonl, since)
    recent_metrics = [r for r in metric_rows if _parse_ts(r["timestamp"]) >= recent_since]
    recent_events = [r for r in event_rows if _parse_ts(r["timestamp"]) >= recent_since]

    metric_baselines = build_metric_baselines(metric_rows)
    event_baselines = build_event_baselines(event_rows)

    out_path = store.aggregates_dir / "baselines.json"
    out_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
                "metrics": metric_baselines,
                "events": event_baselines,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    cooldown: dict[str, datetime] = {}
    n_metric = check_metric_anomalies(store, metric_baselines, recent_metrics, cooldown)
    n_event = check_event_anomalies(store, event_baselines, recent_events, cooldown)

    return {
        "metric_baselines": len(metric_baselines),
        "event_baselines": len(event_baselines),
        "anomalies_emitted": n_metric + n_event,
    }


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )
    parser = argparse.ArgumentParser(description="Baseline + anomaly engine")
    parser.add_argument("--loop", action="store_true", help="Run hourly")
    args = parser.parse_args()

    if args.loop:
        log.info("Baseline engine loop — every %ds", POLL_SECONDS)
        while True:
            result = run_pass()
            log.info("Pass complete: %s", result)
            time.sleep(POLL_SECONDS)
    else:
        result = run_pass()
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
