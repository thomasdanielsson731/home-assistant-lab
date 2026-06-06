#!/usr/bin/env python3
"""List HA frontend panels (debug Timeline iframe)."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from websocket import create_connection

load_dotenv(Path(__file__).parent.parent / ".env")
host = os.environ.get("HA_HOST", "192.168.68.175")
token = os.environ["HA_TOKEN"]

ws = create_connection(f"ws://{host}:8123/api/websocket", timeout=15)
ws.recv()
ws.send(json.dumps({"type": "auth", "access_token": token}))
assert json.loads(ws.recv())["type"] == "auth_ok"
ws.send(json.dumps({"id": 1, "type": "get_panels"}))
while True:
    data = json.loads(ws.recv())
    if data.get("id") == 1:
        panels = data["result"]
        break
ws.close()

for pid, info in sorted(panels.items()):
    title = info.get("title") or pid
    url = info.get("url", "")
    print(f"  {pid}: {title!r}" + (f" -> {url[:50]}" if url else ""))
print("house_timeline registered:", "house_timeline" in panels)
