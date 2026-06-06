#!/usr/bin/env python3
"""Create a Home Assistant long-lived access token and update .env.

Requires an existing HA_TOKEN in .env (or HA_USERNAME + HA_PASSWORD flow not implemented).

Usage:
  python scripts/create-ha-token.py
  python scripts/create-ha-token.py --name my-integration --lifespan 365

Requires: pip install websocket-client python-dotenv
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import websocket
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).parent.parent
ENV_FILE = REPO_ROOT / ".env"


def create_token(host: str, access_token: str, client_name: str, lifespan: int) -> str:
    ws = websocket.create_connection(f"ws://{host}:8123/api/websocket", timeout=15)
    if json.loads(ws.recv())["type"] != "auth_required":
        raise RuntimeError("Unexpected websocket handshake")

    ws.send(json.dumps({"type": "auth", "access_token": access_token}))
    if json.loads(ws.recv())["type"] != "auth_ok":
        raise RuntimeError("Authentication failed — check existing HA_TOKEN in .env")

    ws.send(json.dumps({
        "id": 1,
        "type": "auth/long_lived_access_token",
        "client_name": client_name,
        "lifespan": lifespan,
    }))
    result = json.loads(ws.recv())
    ws.close()

    if not result.get("success"):
        raise RuntimeError(f"Token creation failed: {result}")
    return result["result"]


def update_env(token: str) -> None:
    text = ENV_FILE.read_text(encoding="utf-8")
    if re.search(r"^HA_TOKEN=", text, re.MULTILINE):
        text = re.sub(r"^HA_TOKEN=.*$", f"HA_TOKEN={token}", text, count=1, flags=re.MULTILINE)
    else:
        text = text.rstrip() + f"\nHA_TOKEN={token}\n"
    ENV_FILE.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create HA long-lived token and update .env")
    parser.add_argument("--name", default="home-assistant-lab-maintenance")
    parser.add_argument("--lifespan", type=int, default=3650, help="Days (default: 10 years)")
    args = parser.parse_args()

    load_dotenv(ENV_FILE)
    host = os.environ.get("HA_HOST", "192.168.68.175")
    existing = os.environ.get("HA_TOKEN")
    if not existing:
        sys.exit("ERROR: HA_TOKEN not set in .env — create one manually in HA UI first")

    token = create_token(host, existing, args.name, args.lifespan)
    update_env(token)
    print(f"Created token '{args.name}' (lifespan {args.lifespan} days)")
    print(f"Updated {ENV_FILE}")
    print("Revoke the old token in HA → Profile → Security if no longer needed.")


if __name__ == "__main__":
    main()
