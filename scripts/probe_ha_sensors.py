#!/usr/bin/env python3
"""List HA states for dashboard-critical sensors."""
import json
import os
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
HOST = os.environ["HA_HOST"]
TOKEN = os.environ["HA_TOKEN"]
KEYS = (
    "insights",
    "house_",
    "heiman",
    "loitering",
    "radar",
    "audio_spl",
    "aoa_person",
    "aoa_vehicle",
)

req = urllib.request.Request(
    f"http://{HOST}:8123/api/states",
    headers={"Authorization": f"Bearer {TOKEN}"},
)
states = json.loads(urllib.request.urlopen(req, timeout=30).read())
filter_keys = tuple(k.lower() for k in (sys.argv[1:] if len(sys.argv) > 1 else KEYS))
problems = []
for s in sorted(states, key=lambda x: x["entity_id"]):
    eid = s["entity_id"]
    if not any(k in eid for k in filter_keys):
        continue
    state = s["state"]
    flag = "OK" if state not in ("unavailable", "unknown", "") else "WARN"
    if flag == "WARN":
        problems.append(eid)
    print(f"{flag:4}  {eid}: {state}")

print(f"\nProblems: {len(problems)}")
for p in problems:
    print(f"  - {p}")
