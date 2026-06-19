#!/usr/bin/env python3
"""Reload HA template/MQTT integrations after insights counter changes."""
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

RELOADS = (
    ("homeassistant", "reload_core_config", {}),
    ("template", "reload", {}),
    ("mqtt", "reload", {}),
)


def call(domain: str, service: str, data: dict, timeout: int = 120) -> None:
    r = requests.post(
        f"{base}/services/{domain}/{service}",
        headers=headers,
        json=data,
        timeout=timeout,
    )
    print(f"{domain}.{service}: {r.status_code} {r.text[:200]}")


if __name__ == "__main__":
    for domain, service, data in RELOADS:
        call(domain, service, data)
