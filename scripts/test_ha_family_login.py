#!/usr/bin/env python3
"""Test HA username/password login via auth flow."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
HOST = os.environ.get("HA_HOST", "192.168.68.175")
BASE = f"http://{HOST}:8123"
PASSWORD = os.environ.get("HA_FAMILY_PASSWORD", "")


def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def try_login(username: str, password: str) -> str:
    try:
        flow = post("/auth/login_flow", {"client_id": f"{BASE}/", "handler": ["homeassistant", None]})
        if flow.get("type") != "form":
            return f"unexpected flow type: {flow.get('type')}"
        result = post(
            f"/auth/login_flow/{flow['flow_id']}",
            {"username": username, "password": password},
        )
        if result.get("type") == "create_entry":
            return "OK"
        return f"FAIL: {result.get('type')} errors={result.get('errors')}"
    except Exception as e:
        return f"ERROR: {e}"


def main() -> int:
    if not PASSWORD:
        print("HA_FAMILY_PASSWORD not set — cannot test logins")
        return 1
    for user in ("anna", "hugo", "nils"):
        print(f"{user}: {try_login(user, PASSWORD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
