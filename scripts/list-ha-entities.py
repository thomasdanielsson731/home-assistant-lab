#!/usr/bin/env python3
import json, os, urllib.request
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
req = urllib.request.Request(
    "http://" + os.environ["HA_HOST"] + ":8123/api/states",
    headers={"Authorization": "Bearer " + os.environ["HA_TOKEN"]},
)
data = json.loads(urllib.request.urlopen(req, timeout=30).read())
for s in sorted(data, key=lambda x: x["entity_id"]):
    e = s["entity_id"]
    if "aoa" in e or "driveway_env" in e or "scene" in e:
        print(f"{e}: {s['state']}")
