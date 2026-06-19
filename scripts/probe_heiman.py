#!/usr/bin/env python3
import json, os, urllib.request
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
h=os.environ["HA_HOST"]; t=os.environ["HA_TOKEN"]
r=urllib.request.Request(f"http://{h}:8123/api/states", headers={"Authorization":f"Bearer {t}"})
for s in sorted(json.loads(urllib.request.urlopen(r,timeout=30).read()), key=lambda x:x["entity_id"]):
    e=s["entity_id"]
    if "heiman" in e and e.startswith("binary_sensor"):
        print(f"{e}: {s['state']}")
