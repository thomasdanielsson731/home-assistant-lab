#!/usr/bin/env python3
"""Install and start Danielsson Insights add-on on HAOS (reads secrets from .env)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

ADDON_SLUG = "25d01a20_danielsson_insights"
HOST = os.environ.get("HA_HOST", "192.168.68.175")
SSH_PORT = os.environ.get("HA_SSH_PORT", "22222")
SSH_USER = os.environ.get("HA_USER", "root")


def ssh(cmd: str, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    target = f"{SSH_USER}@{HOST}"
    return subprocess.run(
        ["ssh", target, "-p", SSH_PORT, "-o", "StrictHostKeyChecking=no", cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def addon_state() -> str:
    r = ssh(f"ha apps info {ADDON_SLUG} 2>/dev/null | grep '^state:' | awk '{{print $2}}'", timeout=30)
    return (r.stdout or "").strip()


def main() -> int:
    required = ("MQTT_PASS", "CAM_PASS", "AXIS_ROOT_PASSWORD", "HA_TOKEN")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"Missing in .env: {', '.join(missing)}")
        return 1

    state = addon_state()
    print(f"Add-on state: {state or 'not installed'}")

    if state in ("", "unknown") or "installed: false" in ssh(
        f"ha apps info {ADDON_SLUG} 2>/dev/null"
    ).stdout:
        print(f"Installing {ADDON_SLUG} (may take several minutes)...")
        r = ssh(f"ha apps install {ADDON_SLUG}", timeout=900)
        if r.returncode != 0:
            print(r.stderr or r.stdout)
            return 1
        print(r.stdout[-500:] if len(r.stdout) > 500 else r.stdout)

    options = {
        "mqtt_host": HOST,
        "mqtt_user": os.environ.get("MQTT_USER", "frigate"),
        "mqtt_password": os.environ["MQTT_PASS"],
        "cam_user": os.environ.get("CAM_USER", "homeassistant"),
        "cam_password": os.environ["CAM_PASS"],
        "axis_root_password": os.environ["AXIS_ROOT_PASSWORD"],
        "ha_token": os.environ["HA_TOKEN"],
        "events_path": "/share/danielsson-insights/events",
        "scripts_path": "/share/danielsson-insights/scripts",
        "enable_bridges": True,
    }
    opt_json = json.dumps(options)
    print("Applying add-on options…")
    r = ssh(f"ha apps options {ADDON_SLUG} --options '{opt_json}'", timeout=60)
    if r.returncode != 0:
        print(r.stderr or r.stdout)
        return 1

    print("Starting add-on…")
    r = ssh(f"ha apps start {ADDON_SLUG}", timeout=120)
    print(r.stdout or r.stderr)

    for _ in range(12):
        time.sleep(5)
        state = addon_state()
        print(f"  state: {state}")
        if state == "started":
            print("Danielsson Insights is running on HAOS.")
            return 0
    print("Add-on did not reach 'started' — check Supervisor logs.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
