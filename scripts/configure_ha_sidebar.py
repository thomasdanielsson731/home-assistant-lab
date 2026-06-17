#!/usr/bin/env python3
"""Configure HA sidebar: hide extra panels, set Danielsson Home as default."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from websocket import create_connection

load_dotenv(Path(__file__).parent.parent / ".env")

HOST = os.environ.get("HA_HOST", "192.168.68.175")
SSH_PORT = os.environ.get("HA_SSH_PORT", "22222")
SSH_USER = os.environ.get("HA_USER", "root")
TOKEN = os.environ.get("HA_TOKEN")
if not TOKEN:
    sys.exit("HA_TOKEN not set in .env")

URI = os.environ.get("HA_WS_URL", f"ws://{HOST}:8123/api/websocket")
DEFAULT_PANEL = "home-hem"
HEM_PANEL = "home-hem"
CAMERAS_PANEL = "home-cameras"
SECURITY_PANEL = "home-security"
EVENTS_PANEL = "home-events"
ROOMS_PANEL = "home-rooms"
TECH_PANEL = "home-tech"
TIMELINE_PANEL = "house-timeline"
GRAPHS_PANEL = "house-graphs"
KEEP_VISIBLE = {
    HEM_PANEL,
    CAMERAS_PANEL,
    SECURITY_PANEL,
    EVENTS_PANEL,
    ROOMS_PANEL,
    TECH_PANEL,
    TIMELINE_PANEL,
    GRAPHS_PANEL,
    "config",
}

# Panels to hide (built-in + integration add-ons not in KEEP_VISIBLE)
HIDE_PANELS = [
    "home",  # built-in "Overview" / Översikt
    "home-lab",
    "light",
    "climate",
    "security",
    "maintenance",
    "media-browser",
    "energy",
    "history",
    "logbook",
    "todo",
    "map",
    "lovelace",
    "hacs",
    "ccab4aaf_frigate-fa",
    "09e60fb6_scrypted",
    "c7657554_double-take",
]


def ws_call(ws, msg: dict) -> dict | list:
    ws.send(json.dumps(msg))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == msg.get("id"):
            if "error" in data:
                raise RuntimeError(data["error"])
            return data.get("result") or {}


def build_sidebar_config(panels: dict) -> dict:
    hide = sorted(pid for pid in panels if pid not in KEEP_VISIBLE and pid in HIDE_PANELS)
    for pid in panels:
        if pid in KEEP_VISIBLE or pid in hide:
            continue
        if pid.startswith("_") or pid in ("profile", "app", "notfound"):
            continue
        hide.append(pid)
    hide = sorted(set(hide))
    return {
        "panelOrder": [
            HEM_PANEL,
            CAMERAS_PANEL,
            SECURITY_PANEL,
            EVENTS_PANEL,
            ROOMS_PANEL,
            TIMELINE_PANEL,
            GRAPHS_PANEL,
            TECH_PANEL,
        ],
        "hiddenPanels": hide,
        "defaultPanel": DEFAULT_PANEL,
    }


def ssh_run(cmd: str) -> str:
    target = f"{SSH_USER}@{HOST}"
    result = subprocess.run(
        ["ssh", "-p", SSH_PORT, "-o", "StrictHostKeyChecking=no", target, cmd],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or cmd)
    return result.stdout


def apply_sidebar_for_all_users(sidebar: dict, user_ids: list[str]) -> None:
    """Write frontend.user_data_* on HAOS so family accounts hide Overview too."""
    for uid in user_ids:
        key = f"frontend.user_data_{uid}"
        path = f"/config/.storage/{key}"
        try:
            raw = ssh_run(f"cat {path}")
            doc = json.loads(raw)
        except Exception:
            doc = {"version": 1, "minor_version": 1, "key": key, "data": {}}
        doc.setdefault("data", {})["sidebar"] = sidebar
        payload = json.dumps(doc, ensure_ascii=False)
        escaped = payload.replace("'", "'\\''")
        ssh_run(f"printf '%s' '{escaped}' > {path}")


def main() -> int:
    ws = create_connection(URI, timeout=30)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    auth = json.loads(ws.recv())
    if auth.get("type") != "auth_ok":
        print("Auth failed:", auth)
        return 1

    panels = ws_call(ws, {"id": 1, "type": "get_panels"})
    users = ws_call(ws, {"id": 2, "type": "config/auth/list"})
    sidebar = build_sidebar_config(panels)

    ws_call(
        ws,
        {
            "id": 3,
            "type": "frontend/set_user_data",
            "key": "sidebar",
            "value": sidebar,
        },
    )
    ws.close()

    human_ids = [
        u["id"]
        for u in users
        if isinstance(u, dict) and not u.get("system_generated") and u.get("username")
    ]
    apply_sidebar_for_all_users(sidebar, human_ids)

    print(f"Sidebar updated: default={DEFAULT_PANEL}, hidden={len(sidebar['hiddenPanels'])} panels")
    print(f"Applied to {len(human_ids)} user(s) via SSH storage")
    for pid in sidebar["hiddenPanels"]:
        title = panels.get(pid, {}).get("title") or pid
        print(f"  hidden: {title} ({pid})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
