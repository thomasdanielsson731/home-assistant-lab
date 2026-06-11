#!/usr/bin/env python3
"""ZHA helpers — setup, list devices, permit join, reset network.

Sonoff ZBDongle-P (CC2652P) on the HAOS host — ZNP, 115200, no flow control.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from websocket import create_connection

load_dotenv(Path(__file__).parent.parent / ".env")

HOST = os.environ.get("HA_HOST", "192.168.68.175")
SSH_PORT = os.environ.get("HA_SSH_PORT", "22222")
SSH_USER = os.environ.get("HA_USER", "root")
TOKEN = os.environ.get("HA_TOKEN")
if not TOKEN:
    sys.exit("HA_TOKEN not set in .env")

BASE = f"http://{HOST}:8123/api"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
WS_URI = f"ws://{HOST}:8123/api/websocket"

DONGLE_PATH = (
    "/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_"
    "7631e2baf4a2ef1181bd966661ce3355-if00-port0"
)
RADIO_TYPE = "ZNP = Texas Instruments Z-Stack ZNP protocol: CC253x, CC26x2, CC13x2"

# Failed interviews from repeated pairing attempts — safe to remove if canonical device exists.
GHOST_IEEE = (
    "cc:36:bb:ff:fe:d9:0e:76",
    "cc:36:bb:ff:fe:d9:0e:99",
)


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


def ws_call(payload: dict):
    ws = create_connection(WS_URI, timeout=30)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    ws.recv()
    ws.send(json.dumps({"id": 1, **payload}))
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == 1:
            if not data.get("success", True):
                raise RuntimeError(data.get("error"))
            ws.close()
            return data.get("result")


def zha_entry() -> dict | None:
    r = requests.get(f"{BASE}/config/config_entries/entry", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return next((e for e in r.json() if e["domain"] == "zha"), None)


def step(flow_id: str | None, payload: dict) -> dict:
    url = f"{BASE}/config/config_entries/flow" + (f"/{flow_id}" if flow_id else "")
    r = requests.post(url, headers=HEADERS, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()


def list_devices() -> int:
    devices = ws_call({"type": "zha/devices"}) or []
    print(f"ZHA network devices: {len(devices)}")
    for d in devices:
        print(
            f"- {d.get('user_given_name') or d.get('name')} | {d.get('manufacturer')} {d.get('model')}"
            f" | ieee {d.get('ieee')} | lqi {d.get('lqi')} | type {d.get('device_type')}"
        )
    return 0


def permit_join(duration: int = 254) -> int:
    ws_call({"type": "zha/devices/permit", "duration": duration})
    print(f"Permit join OPEN for {duration} s")
    return list_devices()


def remove_ghosts() -> int:
    for ieee in GHOST_IEEE:
        r = requests.post(
            f"{BASE}/services/zha/remove",
            headers=HEADERS,
            json={"ieee": ieee},
            timeout=60,
        )
        ok = r.status_code == 200
        print(f"remove {ieee}: {'OK' if ok else r.status_code} {r.text[:120]}")
    return list_devices()


def ssh(cmd: str) -> None:
    target = f"{SSH_USER}@{HOST}"
    r = subprocess.run(
        ["ssh", target, "-p", SSH_PORT, cmd],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout)
        sys.exit(f"SSH failed ({r.returncode}): {cmd}")


def reset_zha() -> int:
    """Remove ZHA integration, delete zigbee.db, restart core, recreate network."""
    entry = zha_entry()
    if entry:
        eid = entry["entry_id"]
        r = requests.delete(
            f"{BASE}/config/config_entries/entry/{eid}",
            headers=HEADERS,
            timeout=60,
        )
        if r.status_code not in (200, 204):
            sys.exit(f"Failed to remove ZHA integration: {r.status_code} {r.text[:200]}")
        print(f"Removed ZHA integration ({eid})")
    else:
        print("No ZHA integration found — will only clear zigbee.db")

    ssh("rm -f /config/zigbee.db /config/zigbee.db-shm /config/zigbee.db-wal")
    print("Deleted /config/zigbee.db*")
    ssh("ha core restart")
    print("HA core restarting — waiting…")
    time.sleep(15)
    wait_for_ha()
    print("Recreating ZHA network…")
    return setup_zha()


def flow_get(flow_id: str) -> dict:
    r = requests.get(f"{BASE}/config/config_entries/flow/{flow_id}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def wait_for_flow(flow_id: str, timeout: int = 120) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        res = flow_get(flow_id)
        if res.get("type") in ("create_entry", "abort", "form", "menu"):
            return res
        if res.get("type") == "progress":
            time.sleep(3)
            continue
        return res
    sys.exit("ZHA config flow timed out")


def setup_zha() -> int:
    existing = zha_entry()
    if existing:
        print(f"ZHA already configured: {existing['title']} ({existing['state']})")
        return 0

    res = step(None, {"handler": "zha", "show_advanced_options": True})
    print("step:", res["step_id"])
    fid = res["flow_id"]

    res = step(fid, {"path": DONGLE_PATH})
    print("step:", res.get("step_id"), res.get("type"))

    if res.get("step_id") == "choose_setup_strategy":
        res = step(fid, {"next_step_id": "setup_strategy_advanced"})
        print("step:", res.get("step_id"), res.get("type"))

    if res.get("step_id") == "manual_pick_radio_type":
        res = step(fid, {"radio_type": RADIO_TYPE})
        print("step:", res.get("step_id"), res.get("type"))

    if res.get("step_id") == "manual_port_config":
        res = step(fid, {"path": DONGLE_PATH, "baudrate": 115200, "flow_control": "none"})
        print("step:", res.get("step_id"), res.get("type"), "errors:", res.get("errors"))

    if res.get("step_id") == "choose_formation_strategy":
        res = step(fid, {"next_step_id": "form_new_network"})
        print("step:", res.get("step_id"), res.get("type"))

    if res.get("type") == "progress":
        print("progress:", res.get("progress_action"), "— waiting…")
        res = wait_for_flow(fid)

    if res.get("type") == "create_entry":
        print("SUCCESS — ZHA entry created")
        return 0

    print("Flow did not complete:", res.get("type"), res.get("step_id"), res.get("errors"))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="ZHA setup and maintenance")
    parser.add_argument("--list", action="store_true", help="List ZHA network devices")
    parser.add_argument("--permit", action="store_true", help="Open permit join for 254 s")
    parser.add_argument("--remove-ghosts", action="store_true", help="Remove failed interview duplicates")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete ZHA + zigbee.db and create a fresh network (requires --yes)",
    )
    parser.add_argument("--yes", action="store_true", help="Confirm destructive --reset")
    args = parser.parse_args()

    wait_for_ha()
    if args.reset:
        if not args.yes:
            print("Add --yes to confirm: removes all Zigbee devices from HA and zigbee.db")
            return 1
        return reset_zha()
    if args.list:
        return list_devices()
    if args.permit:
        return permit_join()
    if args.remove_ghosts:
        return remove_ghosts()
    return setup_zha()


if __name__ == "__main__":
    sys.exit(main())
