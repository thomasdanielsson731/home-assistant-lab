#!/usr/bin/env python3
"""Create Home Assistant local users via WebSocket API (owner token required)."""
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

URI = os.environ.get(
    "HA_WS_URL",
    f"ws://{HOST}:8123/api/websocket",
)

USERS = [
    ("Anna", "anna"),
    ("Hugo", "hugo"),
    ("Nils", "nils"),
]
PASSWORD = os.environ.get("HA_FAMILY_PASSWORD")
if not PASSWORD:
    sys.exit("Set HA_FAMILY_PASSWORD in .env (not committed) before running")


def ws_call(ws, msg: dict) -> dict | list:
    ws.send(json.dumps(msg))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == msg.get("id"):
            if not data.get("success", True):
                err = data.get("error", data)
                raise RuntimeError(f"{msg.get('type')}: {err}")
            return data.get("result") or {}


def has_login(user: dict) -> bool:
    return bool(user.get("username")) or any(
        c.get("type") == "homeassistant" for c in user.get("credentials", [])
    )


def main() -> int:
    ws = create_connection(URI, timeout=30)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    auth = json.loads(ws.recv())
    if auth.get("type") != "auth_ok":
        print("Auth failed:", auth)
        return 1

    users = ws_call(ws, {"id": 1, "type": "config/auth/list"})
    by_name = {
        (u.get("name") or "").lower(): u
        for u in users
        if isinstance(u, dict) and not u.get("system_generated")
    }

    msg_id = 2
    for display_name, username in USERS:
        existing = by_name.get(display_name.lower())
        if existing and has_login(existing):
            print(f"SKIP {username} — login already configured")
            continue

        if existing:
            user_id = existing["id"]
            print(f"LINK {username} — adding credentials to existing user")
        else:
            user = ws_call(
                ws,
                {
                    "id": msg_id,
                    "type": "config/auth/create",
                    "name": display_name,
                },
            )
            msg_id += 1
            user_id = user["id"]
            print(f"USER {username} — created account")

        ws_call(
            ws,
            {
                "id": msg_id,
                "type": "config/auth_provider/homeassistant/create",
                "user_id": user_id,
                "username": username,
                "password": PASSWORD,
            },
        )
        msg_id += 1
        print(f"OK   {username} ({display_name})")

    ws.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
