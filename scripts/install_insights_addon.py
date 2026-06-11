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


def addon_info() -> dict[str, str]:
    r = ssh(f"ha apps info {ADDON_SLUG} 2>/dev/null", timeout=30)
    info: dict[str, str] = {}
    for line in (r.stdout or "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()
    return info


def supervisor_post(path: str, payload: dict, timeout: int = 120) -> tuple[int, str]:
    import base64

    body_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
    cmd = (
        'TOKEN="${SUPERVISOR_TOKEN:-}"; '
        'if [ -z "$TOKEN" ] && [ -f /run/supervisor/token ]; then TOKEN=$(cat /run/supervisor/token); fi; '
        f"echo '{body_b64}' | base64 -d | "
        "curl -s -w '\\n%{http_code}' -X POST "
        '-H "Authorization: Bearer ${TOKEN}" '
        '-H "Content-Type: application/json" '
        "-d @- "
        f"http://supervisor{path}"
    )
    r = ssh(cmd, timeout=timeout)
    lines = (r.stdout or "").strip().splitlines()
    if not lines:
        return r.returncode, r.stderr or ""
    code = int(lines[-1]) if lines[-1].isdigit() else 0
    return code, "\n".join(lines[:-1])


def ensure_dns() -> None:
    """Upstream DNS helps Docker buildkit resolve ghcr.io on HAOS."""
    r = ssh("ha dns info 2>/dev/null | grep 'dns://1.1.1.1'", timeout=15)
    if "1.1.1.1" in (r.stdout or ""):
        return
    print("Setting HA DNS upstream (1.1.1.1, 8.8.8.8)...")
    ssh("ha dns options --servers dns://1.1.1.1 --servers dns://8.8.8.8", timeout=30)


def main() -> int:
    required = ("MQTT_PASS", "CAM_PASS", "AXIS_ROOT_PASSWORD", "HA_TOKEN")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"Missing in .env: {', '.join(missing)}")
        return 1

    ensure_dns()
    info = addon_info()
    state = info.get("state", "unknown")
    print(f"Add-on state: {state} (version {info.get('version', '?')})")

    if state in ("unknown", "") or info.get("version") in (None, "", "null"):
        print(f"Installing {ADDON_SLUG} (may take several minutes)...")
        r = ssh(f"ha apps install {ADDON_SLUG}", timeout=900)
        if r.returncode != 0:
            print(r.stderr or r.stdout)
            return 1
        print("Install OK")

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
    print("Applying add-on options via Supervisor API...")
    code, body = supervisor_post(f"/addons/{ADDON_SLUG}/options", {"options": options})
    print(f"  options HTTP {code}")
    if code not in (200, 201):
        print(body)
        return 1

    print("Starting add-on...")
    r = ssh(f"ha apps start {ADDON_SLUG}", timeout=120)
    if r.returncode != 0:
        print(r.stderr or r.stdout)
        return 1

    for _ in range(18):
        time.sleep(5)
        state = addon_info().get("state", "")
        print(f"  state: {state}")
        if state == "started":
            print("Danielsson Insights is running on HAOS.")
            print("Next: .\\scripts\\deploy-insights-to-ha.ps1 -UseIngressSecrets")
            return 0

    print("Add-on did not reach 'started' — check: ha apps logs", ADDON_SLUG)
    r = ssh(f"ha apps logs {ADDON_SLUG} 2>/dev/null | tail -30", timeout=30)
    print(r.stdout or r.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
