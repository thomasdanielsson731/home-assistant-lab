#!/usr/bin/env python3
"""Inspect HA REST config entries (legacy) and MQTT insights entities."""
import json
import os
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
HOST = os.environ["HA_HOST"]
TOKEN = os.environ["HA_TOKEN"]
headers = {"Authorization": f"Bearer {TOKEN}"}

for url in (
    f"http://{HOST}:8123/api/config/config_entries/entry",
    f"http://{HOST}:8123/api/error_log",
):
    req = urllib.request.Request(url, headers=headers)
    data = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
    if "config_entries" in url:
        entries = json.loads(data)
        rest = [e for e in entries if e.get("domain") == "rest"]
        print(f"REST config entries: {len(rest)}")
        for e in rest:
            print(json.dumps(e, indent=2)[:800])
    else:
        lines = [ln for ln in data.splitlines() if "rest" in ln.lower() or "insights" in ln.lower()]
        print("Error log (rest/insights/mqtt):")
        for ln in lines[-20:]:
            print(ln)
