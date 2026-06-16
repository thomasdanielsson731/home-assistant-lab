#!/usr/bin/env python3
"""List HA users and login status (diagnostic)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from websocket import create_connection

load_dotenv(Path(__file__).parent.parent / ".env")

HOST = os.environ.get("HA_HOST", "192.168.68.175")
TOKEN = os.environ.get("HA_TOKEN")
URI = os.environ.get("HA_WS_URL", f"ws://{HOST}:8123/api/websocket")


def check_http(url: str) -> str:
    try:
        with urllib.request.urlopen(url, timeout=12) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return f"ERROR: {e}"


def main() -> int:
    print(f"HA_HOST={HOST}")
    print(f"LAN:  {check_http(f'http://{HOST}:8123/')}")
    print(f"CF:   {check_http('https://ha.danielsson.cloud/')}")

    if not TOKEN:
        print("HA_TOKEN not set — cannot list users")
        return 1

    ws = create_connection(URI, timeout=20)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    auth = json.loads(ws.recv())
    if auth.get("type") != "auth_ok":
        print("WebSocket auth failed:", auth)
        return 1

    ws.send(json.dumps({"id": 1, "type": "config/auth/list"}))
    users = []
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == 1:
            users = data.get("result") or []
            break

    print("\nUsers (non-system):")
    for u in users:
        if u.get("system_generated"):
            continue
        creds = u.get("credentials") or []
        ha_login = [
            c.get("data", {}).get("username")
            for c in creds
            if c.get("type") == "homeassistant"
        ]
        print(
            f"  {u.get('name')!r}: active={u.get('is_active')} owner={u.get('is_owner')} "
            f"groups={u.get('group_ids')} login={ha_login or 'NONE'}"
        )

    ws.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
