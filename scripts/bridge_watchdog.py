#!/usr/bin/env python3
"""
Bridge watchdog — polls dev PC bridge processes and writes heartbeat metrics.

Run via start-bridges.ps1 alongside other bridges. Heartbeats land in
events/metrics.jsonl (zone ``_bridge/<service>``) for health-check.py.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from event_store import EventStore  # noqa: E402
from lab_heartbeat import write_heartbeat  # noqa: E402

POLL_INTERVAL = 60

SERVICES: list[tuple[str, str]] = [
    ("air_quality_bridge", "air_quality_bridge.py"),
    ("audio_bridge", "audio_bridge.py"),
    ("aoa_bridge", "aoa_bridge.py"),
    ("energy_bridge", "energy_bridge.py"),
    ("event_normalizer", "event_normalizer.py"),
    ("timeline_server", "timeline_server.py"),
    ("influx_metrics_bridge", "influx_metrics_bridge.py"),
]

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("bridge_watchdog")


def is_script_running(script: str) -> bool:
    if sys.platform == "win32":
        ps = (
            f"Get-CimInstance Win32_Process | "
            f"Where-Object {{ $_.CommandLine -like '*{script}*' }} | "
            f"Select-Object -First 1 | ConvertTo-Json"
        )
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps],
                text=True,
                timeout=15,
            ).strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
        return bool(out and out != "null")

    if script == "timeline_server.py":
        return _http_ok("http://127.0.0.1:8765/timeline") or _http_ok(
            f"http://{_probe_host()}:8765/timeline"
        )
    return _pgrep(script)


def _probe_host() -> str:
    import os

    return os.environ.get("HA_HOST") or os.environ.get("MQTT_HOST") or "127.0.0.1"


def _http_ok(url: str, timeout: float = 5.0) -> bool:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _pgrep(script: str) -> bool:
    try:
        out = subprocess.check_output(["pgrep", "-f", script], text=True, timeout=5).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
    return bool(out)


def tick(store: EventStore) -> int:
    alive = 0
    for service, script in SERVICES:
        if is_script_running(script):
            write_heartbeat(service, store)
            alive += 1
        else:
            log.warning("%s not running (%s)", service, script)
    return alive


def main() -> None:
    store = EventStore()
    log.info("Bridge watchdog — heartbeat every %ds", POLL_INTERVAL)
    while True:
        n = tick(store)
        log.info("Heartbeats written: %d/%d", n, len(SERVICES))
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
