#!/usr/bin/env python3
"""Configure HA sidebar: hide extra panels, set Danielsson Home as default."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from websocket import create_connection

load_dotenv(Path(__file__).parent.parent / ".env")

HOST = os.environ.get("HA_HOST", "192.168.68.175")
TOKEN = os.environ.get("HA_TOKEN")
if not TOKEN:
    sys.exit("HA_TOKEN not set in .env")

URI = f"ws://{HOST}:8123/api/websocket"
DEFAULT_PANEL = "home-hem"
HEM_PANEL = "home-hem"
CAMERAS_PANEL = "home-cameras"
SECURITY_PANEL = "home-security"
ROOMS_PANEL = "home-rooms"
TECH_PANEL = "home-tech"
TIMELINE_PANEL = "house-timeline"
GRAPHS_PANEL = "house-graphs"
KEEP_VISIBLE = {
    HEM_PANEL,
    CAMERAS_PANEL,
    SECURITY_PANEL,
    ROOMS_PANEL,
    TECH_PANEL,
    TIMELINE_PANEL,
    GRAPHS_PANEL,
    "config",
}

# Panels to hide (built-in + integration add-ons not in KEEP_VISIBLE)
HIDE_PANELS = [
    "home",
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


def ws_call(ws, msg: dict) -> dict:
    ws.send(json.dumps(msg))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == msg.get("id"):
            if "error" in data:
                raise RuntimeError(data["error"])
            return data.get("result", {})


def main() -> int:
    ws = create_connection(URI, timeout=30)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    auth = json.loads(ws.recv())
    if auth.get("type") != "auth_ok":
        print("Auth failed:", auth)
        return 1

    panels = ws_call(ws, {"id": 1, "type": "get_panels"})
    hide = sorted(
        pid for pid in panels if pid not in KEEP_VISIBLE and pid in HIDE_PANELS
    )
    # Also hide any integration panel not in keep list
    for pid in panels:
        if pid in KEEP_VISIBLE or pid in hide:
            continue
        if pid.startswith("_") or pid in ("profile", "app", "notfound"):
            continue
        hide.append(pid)
    hide = sorted(set(hide))

    sidebar = {
        "panelOrder": [
            HEM_PANEL,
            CAMERAS_PANEL,
            SECURITY_PANEL,
            ROOMS_PANEL,
            TIMELINE_PANEL,
            GRAPHS_PANEL,
            TECH_PANEL,
        ],
        "hiddenPanels": hide,
        "defaultPanel": DEFAULT_PANEL,
    }
    ws_call(
        ws,
        {
            "id": 2,
            "type": "frontend/set_user_data",
            "key": "sidebar",
            "value": sidebar,
        },
    )
    ws.close()

    print(f"Sidebar updated: default={DEFAULT_PANEL}, hidden={len(hide)} panels")
    for pid in hide:
        title = panels.get(pid, {}).get("title") or pid
        print(f"  hidden: {title} ({pid})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
