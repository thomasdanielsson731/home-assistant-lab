#!/usr/bin/env python3
"""Reload MQTT entities and HA config via REST API."""
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
token = os.environ.get("HA_TOKEN")
host = os.environ.get("HA_HOST", "192.168.68.175")
if not token:
    sys.exit("HA_TOKEN not set")

base = f"http://{host}:8123/api"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

for domain, service, data in (
    ("mqtt", "reload", {}),
    ("homeassistant", "reload_all", {}),
):
    r = requests.post(f"{base}/services/{domain}/{service}", headers=headers, json=data, timeout=60)
    print(f"{domain}.{service}: {r.status_code} {r.text[:100]}")
