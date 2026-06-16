#!/usr/bin/env python3
"""Assign family HA users to system-users group (required for login/UI access)."""
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
URI = os.environ.get("HA_WS_URL", f"ws://{HOST}:8123/api/websocket")

FAMILY_USERNAMES = frozenset({"anna", "hugo", "nils"})
FAMILY_GROUP = "system-users"


def ws_call(ws, msg_id: int, msg: dict) -> dict | list:
    payload = {"id": msg_id, **msg}
    ws.send(json.dumps(payload))
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == msg_id:
            if not data.get("success", True):
                raise RuntimeError(data.get("error", data))
            return data.get("result") or {}


def main() -> int:
    if not TOKEN:
        sys.exit("HA_TOKEN not set in .env")

    ws = create_connection(URI, timeout=30)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    auth = json.loads(ws.recv())
    if auth.get("type") != "auth_ok":
        print("Auth failed:", auth)
        return 1

    users = ws_call(ws, 1, {"type": "config/auth/list"})
    msg_id = 2
    fixed = 0
    for user in users:
        if not isinstance(user, dict) or user.get("system_generated"):
            continue
        username = (user.get("username") or "").lower()
        if username not in FAMILY_USERNAMES:
            continue
        groups = user.get("group_ids") or []
        if FAMILY_GROUP in groups:
            print(f"OK   {username} — already in {FAMILY_GROUP}")
            continue
        ws_call(
            ws,
            msg_id,
            {
                "type": "config/auth/update",
                "user_id": user["id"],
                "group_ids": [FAMILY_GROUP],
            },
        )
        msg_id += 1
        print(f"FIX  {username} — assigned {FAMILY_GROUP}")
        fixed += 1

    ws.close()
    print(f"Done ({fixed} updated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
