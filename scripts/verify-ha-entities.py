#!/usr/bin/env python3
"""Quick check of key HA entities via REST API."""
import json
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
host = os.environ["HA_HOST"]
token = os.environ["HA_TOKEN"]

ENTITIES = [
    "sensor.driveway_env_temperature",
    "sensor.driveway_env_co2",
    "sensor.driveway_env_aqi",
    "sensor.driveway_env_humidity",
    "binary_sensor.front_aoa_person",
    "binary_sensor.front_scene_object_present",
    "binary_sensor.driveway_wide_aoa_vehicle",
    "binary_sensor.driveway_id_aoa_person",
    "sensor.front_scene_persons",
    "person.thomasx",
    "person.nils_2",
    "person.hugo",
    "person.anna",
]

ok, missing, bad = 0, 0, 0
for entity in ENTITIES:
    req = urllib.request.Request(
        f"http://{host}:8123/api/states/{entity}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            state = d.get("state", "?")
            if state in ("unavailable", "unknown"):
                print(f"WARN  {entity}: {state}")
                bad += 1
            else:
                print(f"OK    {entity}: {state}")
                ok += 1
    except urllib.error.HTTPError as e:
        print(f"MISS  {entity}: HTTP {e.code}")
        missing += 1

print(f"\nSummary: {ok} ok, {bad} warn, {missing} missing")
