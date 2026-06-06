#!/usr/bin/env python3
"""
Danielsson Home Intelligence — InfluxDB metrics bridge (Phase 7-10).

Tails events/metrics.jsonl and writes samples to InfluxDB for long retention.
Optional: only active when INFLUX_URL is set in .env.

Supports InfluxDB 2.x (token + org + bucket) and 1.x (database query param).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

REPO_ROOT = Path(__file__).parent.parent
METRICS_PATH = REPO_ROOT / "events" / "metrics.jsonl"
STATE_PATH = REPO_ROOT / "events" / ".influx_bridge_state.json"
POLL_INTERVAL = int(os.environ.get("INFLUX_POLL_SECONDS", "30"))

INFLUX_URL = os.environ.get("INFLUX_URL", "").rstrip("/")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN", "")
INFLUX_ORG = os.environ.get("INFLUX_ORG", "home")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET", "home_lab")
INFLUX_DB = os.environ.get("INFLUX_DB", "home_lab")
INFLUX_MEASUREMENT = os.environ.get("INFLUX_MEASUREMENT", "home_metrics")
INFLUX_V2 = os.environ.get("INFLUX_V2", "true").lower() in ("1", "true", "yes")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("influx_bridge")

_ESCAPE_KEY = re.compile(r"[,= ]")


def _escape_tag(value: str) -> str:
    return _ESCAPE_KEY.sub(lambda m: f"\\{m.group(0)}", str(value))


def _escape_field_key(value: str) -> str:
    return _ESCAPE_KEY.sub(lambda m: f"\\{m.group(0)}", str(value))


def _to_epoch_seconds(ts: str) -> int:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return int(dt.timestamp())


def format_lines(rows: list[dict]) -> str:
    """Convert metrics.jsonl rows to Influx line protocol."""
    lines: list[str] = []
    for row in rows:
        zone = _escape_tag(row.get("zone", "unknown"))
        epoch = _to_epoch_seconds(row["timestamp"])
        for key, value in (row.get("values") or {}).items():
            if value is None:
                continue
            field = _escape_field_key(key)
            if isinstance(value, bool):
                field_val = "true" if value else "false"
            elif isinstance(value, int):
                field_val = f"{value}i"
            else:
                field_val = str(float(value))
            lines.append(
                f"{INFLUX_MEASUREMENT},zone={zone} {field}={field_val} {epoch}"
            )
    return "\n".join(lines)


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"offset": 0}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"offset": 0}


def save_state(offset: int) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"offset": offset}), encoding="utf-8")


def read_new_rows() -> tuple[list[dict], int]:
    if not METRICS_PATH.exists():
        return [], 0

    state = load_state()
    offset = int(state.get("offset", 0))
    rows: list[dict] = []

    with METRICS_PATH.open("r", encoding="utf-8") as f:
        f.seek(offset)
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                offset = f.tell()
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("Skipping malformed metrics line at offset %d", pos)
            offset = f.tell()

    return rows, offset


def write_to_influx(lines: str) -> bool:
    if not lines:
        return True

    headers = {"Content-Type": "text/plain; charset=utf-8"}
    if INFLUX_V2:
        if not INFLUX_TOKEN:
            log.error("INFLUX_TOKEN required for InfluxDB 2.x")
            return False
        url = f"{INFLUX_URL}/api/v2/write"
        params = {"org": INFLUX_ORG, "bucket": INFLUX_BUCKET, "precision": "s"}
        headers["Authorization"] = f"Token {INFLUX_TOKEN}"
    else:
        url = f"{INFLUX_URL}/write"
        params = {"db": INFLUX_DB, "precision": "s"}

    try:
        r = requests.post(url, params=params, data=lines, headers=headers, timeout=15)
    except requests.RequestException as exc:
        log.error("Influx write failed: %s", exc)
        return False

    if r.status_code not in (204, 200):
        log.error("Influx write HTTP %s: %s", r.status_code, r.text[:200])
        return False
    return True


def configured() -> bool:
    return bool(INFLUX_URL)


def ping() -> bool:
    if not configured():
        return False
    try:
        if INFLUX_V2:
            r = requests.get(
                f"{INFLUX_URL}/health",
                timeout=5,
            )
        else:
            r = requests.get(f"{INFLUX_URL}/ping", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def run_once() -> int:
    rows, offset = read_new_rows()
    if not rows:
        return offset
    if not configured():
        log.debug("INFLUX_URL not set — %d rows waiting at offset %d", len(rows), offset)
        return offset
    payload = format_lines(rows)
    if write_to_influx(payload):
        save_state(offset)
        line_count = payload.count("\n") + 1 if payload else 0
        log.info("Wrote %d metric rows (%d lines) to InfluxDB", len(rows), line_count)
    return offset


def main() -> None:
    if not configured():
        log.info(
            "INFLUX_URL not set — bridge idle (metrics remain in %s)",
            METRICS_PATH,
        )
    else:
        log.info(
            "Influx metrics bridge started  url=%s  measurement=%s",
            INFLUX_URL,
            INFLUX_MEASUREMENT,
        )
        if ping():
            log.info("InfluxDB health check OK")
        else:
            log.warning("InfluxDB not reachable yet — will retry on write")

    while True:
        run_once()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
