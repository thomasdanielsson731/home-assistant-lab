#!/usr/bin/env python3
"""Bridge heartbeat metrics — written to metrics.jsonl for health-check."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from event_store import EventStore, TZ

BRIDGE_PREFIX = "_bridge"
DEFAULT_MAX_AGE_SECONDS = 300


def bridge_zone(service: str) -> str:
    return f"{BRIDGE_PREFIX}/{service}"


def write_heartbeat(service: str, store: EventStore | None = None) -> None:
    store = store or EventStore()
    ts = datetime.now(TZ).isoformat()
    store.write_metric(ts, bridge_zone(service), {"alive": 1})


def parse_metric_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt


def read_bridge_heartbeats(
    metrics_path: Path,
    *,
    max_lines: int = 5000,
) -> dict[str, datetime]:
    """Return latest heartbeat timestamp per service (zone ``_bridge/<name>``)."""
    latest: dict[str, datetime] = {}
    if not metrics_path.exists():
        return latest
    lines = metrics_path.read_text(encoding="utf-8").splitlines()
    for line in lines[-max_lines:]:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        zone = row.get("zone", "")
        prefix = f"{BRIDGE_PREFIX}/"
        if not zone.startswith(prefix):
            continue
        service = zone[len(prefix):]
        if not service:
            continue
        try:
            latest[service] = parse_metric_ts(row["timestamp"])
        except (KeyError, ValueError):
            continue
    return latest


def is_stale(ts: datetime, max_age_seconds: int, *, now: datetime | None = None) -> bool:
    now = now or datetime.now(TZ)
    return (now - ts).total_seconds() > max_age_seconds


def last_metric_ts_for_zone(
    metrics_path: Path,
    zone: str,
    *,
    max_lines: int = 2000,
) -> datetime | None:
    """Return timestamp of the most recent metric row for *zone*."""
    if not metrics_path.exists():
        return None
    lines = metrics_path.read_text(encoding="utf-8").splitlines()
    for line in reversed(lines[-max_lines:]):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("zone") != zone:
            continue
        try:
            return parse_metric_ts(row["timestamp"])
        except (KeyError, ValueError):
            continue
    return None
