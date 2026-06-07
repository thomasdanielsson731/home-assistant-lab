"""Timeline API v1 — query helpers for House Intelligence Timeline."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from event_store import MIN_OCCUPANCY_SECONDS, TZ

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_TIMELINE = REPO_ROOT / "events" / "timeline.jsonl"
DEFAULT_METRICS = REPO_ROOT / "events" / "metrics.jsonl"


def _parse_ts(value: str) -> datetime:
    # Query strings decode '+' in timezone offsets to space
    ts = datetime.fromisoformat(value.replace(" ", "+"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=TZ)
    return ts


def load_events(
    *,
    hours: int | None = 168,
    event_type: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    timeline_path: Path | None = None,
    newest_first: bool = True,
) -> list[dict]:
    path = timeline_path or DEFAULT_TIMELINE
    if not path.exists():
        return []

    now = datetime.now(TZ)
    if since is None and hours is not None:
        since = now - timedelta(hours=hours)
    if until is None:
        until = now

    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(e["timestamp"])
        if since and ts < since:
            continue
        if until and ts > until:
            continue
        if event_type and e.get("type") != event_type:
            continue
        events.append(e)

    events.sort(key=lambda x: x["timestamp"], reverse=newest_first)
    return events


def parse_time_range(
    qs: dict,
    *,
    default_hours: int = 24,
) -> tuple[datetime, datetime, int | None]:
    """Return (since, until, hours) from query string. Custom from/to overrides hours."""
    from_raw = qs.get("from", [None])[0]
    to_raw = qs.get("to", [None])[0]
    now = datetime.now(TZ)
    if from_raw and to_raw:
        return _parse_ts(from_raw), _parse_ts(to_raw), None
    hours = float(qs.get("hours", [str(default_hours)])[0])
    return now - timedelta(hours=hours), now, hours


def load_metrics(
    *,
    hours: int | None = 24,
    since: datetime | None = None,
    until: datetime | None = None,
    metrics: list[str] | None = None,
    zones: list[str] | None = None,
    metrics_path: Path | None = None,
) -> list[dict]:
    path = metrics_path or DEFAULT_METRICS
    if not path.exists():
        return []

    now = datetime.now(TZ)
    if since is None and hours is not None:
        since = now - timedelta(hours=hours)
    if until is None:
        until = now
    allowed = {m.lower() for m in metrics} if metrics else None
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(row["timestamp"])
        if since and ts < since:
            continue
        if until and ts > until:
            continue
        zone = row.get("zone", "")
        if zones and zone not in zones:
            continue
        for key, val in row.get("values", {}).items():
            if allowed and key.lower() not in allowed:
                continue
            out.append(
                {
                    "timestamp": row["timestamp"],
                    "zone": zone,
                    "metric": key,
                    "value": val,
                }
            )
    out.sort(key=lambda x: x["timestamp"])
    return out


def build_occupancy_blocks(
    events: list[dict],
    *,
    hours: int | None = 24,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[dict]:
    """Merge occupancy start/end events into duration blocks.

    Handles overlapping blocks from multiple sources (AOA + Frigate) by merging
    blocks within the same zone+scenario that overlap or are within 30 s of each other.
    """
    if since is None and hours is not None:
        since = datetime.now(TZ) - timedelta(hours=hours)
    open_blocks: dict[str, dict] = {}
    raw_blocks: list[dict] = []

    sorted_events = sorted(events, key=lambda e: e["timestamp"])
    for e in sorted_events:
        if e.get("type") != "occupancy":
            continue
        ts = _parse_ts(e["timestamp"])
        if since and ts < since:
            continue
        if until and ts > until:
            continue
        meta = e.get("metadata") or {}
        zone = e.get("location", {}).get("zone", "?")
        scenario = meta.get("scenario", "PersonOccupancy")
        key = f"{zone}:{scenario}"
        phase = meta.get("phase")

        if phase == "start":
            open_blocks[key] = {
                "zone": zone,
                "scenario": scenario,
                "camera": e.get("location", {}).get("camera"),
                "start": e["timestamp"],
                "source": e.get("source", "axis_aoa"),
            }
        elif phase == "end" and key in open_blocks:
            start = open_blocks.pop(key)
            raw_blocks.append(
                {
                    "zone": start["zone"],
                    "scenario": start["scenario"],
                    "camera": start.get("camera"),
                    "start": start["start"],
                    "end": e["timestamp"],
                    "duration_seconds": meta.get("duration_seconds"),
                    "source": start.get("source"),
                }
            )

    # Close any still-open blocks at `until`
    end_ts = (until or datetime.now(TZ)).isoformat(timespec="seconds")
    for key, start in open_blocks.items():
        raw_blocks.append(
            {
                "zone": start["zone"],
                "scenario": start["scenario"],
                "camera": start.get("camera"),
                "start": start["start"],
                "end": end_ts,
                "duration_seconds": None,
                "source": start.get("source"),
                "open": True,
            }
        )

    # Merge overlapping/adjacent blocks (within 30 s) per zone+scenario
    merge_gap = timedelta(seconds=30)
    by_key: dict[str, list[dict]] = {}
    for b in raw_blocks:
        k = f"{b['zone']}:{b['scenario']}"
        by_key.setdefault(k, []).append(b)

    merged: list[dict] = []
    for group in by_key.values():
        group.sort(key=lambda b: b["start"])
        cur = dict(group[0])
        for nxt in group[1:]:
            cur_end = _parse_ts(cur["end"])
            nxt_start = _parse_ts(nxt["start"])
            if nxt_start <= cur_end + merge_gap:
                # Extend current block to cover nxt
                if _parse_ts(nxt["end"]) > cur_end:
                    cur["end"] = nxt["end"]
                    start_ts = _parse_ts(cur["start"])
                    end_ts_dt = _parse_ts(cur["end"])
                    cur["duration_seconds"] = int((end_ts_dt - start_ts).total_seconds())
            else:
                merged.append(cur)
                cur = dict(nxt)
        merged.append(cur)

    merged.sort(key=lambda b: b["start"], reverse=True)
    return [b for b in merged if _block_duration_seconds(b) >= MIN_OCCUPANCY_SECONDS]


def _block_duration_seconds(block: dict) -> int:
    if block.get("duration_seconds") is not None:
        return int(block["duration_seconds"])
    return int((_parse_ts(block["end"]) - _parse_ts(block["start"])).total_seconds())


def latest_occupancy_by_zone(blocks: list[dict]) -> dict[str, dict]:
    """Return the most recent occupancy block per zone (for dashboard presence cards)."""
    out: dict[str, dict] = {}
    for b in blocks:
        zone = b["zone"]
        if zone not in out:
            out[zone] = b
    return out


def event_summary_stats(events: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in events:
        t = e.get("type", "?")
        counts[t] = counts.get(t, 0) + 1
    return counts
