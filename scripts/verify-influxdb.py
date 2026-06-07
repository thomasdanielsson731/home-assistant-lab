#!/usr/bin/env python3
"""Probe InfluxDB ping, auth, and write access (Phase 7-10)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

URL = os.environ.get("INFLUX_URL", "").rstrip("/")
USER = os.environ.get("INFLUX_USER", "")
PASSWORD = os.environ.get("INFLUX_PASSWORD", "")
DB = os.environ.get("INFLUX_DB", "home_lab")
MEASUREMENT = os.environ.get("INFLUX_MEASUREMENT", "home_metrics")
V2 = os.environ.get("INFLUX_V2", "false").lower() in ("1", "true", "yes")


def main() -> int:
    if not URL:
        print("SKIP  INFLUX_URL not set in .env")
        return 0

    print(f"InfluxDB at {URL}")

    try:
        ping = requests.get(f"{URL}/ping", timeout=5)
        print(f"  ping: {ping.status_code}")
    except requests.RequestException as exc:
        print(f"  FAIL  not reachable: {exc}")
        return 1

    if V2:
        print("  INFO  INFLUX_V2=true — use token write test (not implemented here)")
        return 0

    auth = (USER, PASSWORD) if USER else None
    try:
        r = requests.get(
            f"{URL}/query",
            params={"q": "SHOW DATABASES"},
            auth=auth,
            timeout=10,
        )
        print(f"  query SHOW DATABASES: {r.status_code}")
        if r.ok:
            print(f"    {r.text.strip()[:200]}")
        else:
            print(f"    {r.text[:200]}")
    except requests.RequestException as exc:
        print(f"  FAIL  query: {exc}")
        return 1

    probe = f"{MEASUREMENT},zone=verify_probe spl=0.0"
    try:
        w = requests.post(
            f"{URL}/write",
            params={"db": DB, "precision": "s"},
            data=probe,
            auth=auth,
            timeout=10,
        )
        print(f"  write probe: {w.status_code}")
        if w.status_code in (204, 200):
            print("  OK    auth + write working")
            return 0
        print(f"    {w.text[:200]}")
    except requests.RequestException as exc:
        print(f"  FAIL  write: {exc}")
        return 1

    print("\n  WARN  writes blocked — fix auth:")
    print("    HA → Add-ons → InfluxDB → disable Authentication, restart")
    print("    OR Chronograf → create user/database → .\\scripts\\setup-influxdb.ps1")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
