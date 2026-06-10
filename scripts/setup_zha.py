#!/usr/bin/env python3
"""Set up ZHA via the HA config-flow REST API.

Sonoff ZBDongle-P (CC2652P) on the HAOS host — ZNP, 115200, no flow control.
Safe to re-run: exits if ZHA is already configured.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

HOST = os.environ.get("HA_HOST", "192.168.68.175")
TOKEN = os.environ.get("HA_TOKEN")
if not TOKEN:
    sys.exit("HA_TOKEN not set in .env")

BASE = f"http://{HOST}:8123/api"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

DONGLE_PATH = (
    "/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_"
    "7631e2baf4a2ef1181bd966661ce3355-if00-port0"
)
RADIO_TYPE = "ZNP = Texas Instruments Z-Stack ZNP protocol: CC253x, CC26x2, CC13x2"


def wait_for_ha(timeout: int = 300) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE}/", headers=HEADERS, timeout=5)
            if r.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(5)
    sys.exit("HA did not come back within timeout")


def zha_entry() -> dict | None:
    r = requests.get(f"{BASE}/config/config_entries/entry", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return next((e for e in r.json() if e["domain"] == "zha"), None)


def step(flow_id: str | None, payload: dict) -> dict:
    url = f"{BASE}/config/config_entries/flow" + (f"/{flow_id}" if flow_id else "")
    r = requests.post(url, headers=HEADERS, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()


def main() -> int:
    wait_for_ha()
    existing = zha_entry()
    if existing:
        print(f"ZHA already configured: {existing['title']} ({existing['state']})")
        return 0

    res = step(None, {"handler": "zha", "show_advanced_options": True})
    print("step:", res["step_id"])
    fid = res["flow_id"]

    res = step(fid, {"path": DONGLE_PATH})
    print("step:", res.get("step_id"), res.get("type"))

    if res.get("step_id") == "manual_pick_radio_type":
        res = step(fid, {"radio_type": RADIO_TYPE})
        print("step:", res.get("step_id"), res.get("type"))

    if res.get("step_id") == "manual_port_config":
        res = step(fid, {"path": DONGLE_PATH, "baudrate": 115200, "flow_control": "none"})
        print("step:", res.get("step_id"), res.get("type"), "errors:", res.get("errors"))

    # Newer ZHA versions add a network-formation choice step
    if res.get("step_id") in ("choose_formation_strategy", "verify_radio"):
        res = step(fid, {"next_step_id": "form_new_network"})
        print("step:", res.get("step_id"), res.get("type"))

    if res.get("type") == "create_entry":
        print(f"SUCCESS — ZHA entry created: {res.get('title')}")
        return 0

    print("Flow did not complete:", res.get("type"), res.get("errors"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
