#!/usr/bin/env python3
import json, os, urllib.request
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
h=os.environ["HA_HOST"]; t=os.environ["HA_TOKEN"]
for eid in ["sensor.insights_persons_24h", "sensor.house_home_status", "binary_sensor.house_smoke_alarm"]:
    r=urllib.request.Request(f"http://{h}:8123/api/states/{eid}", headers={"Authorization":f"Bearer {t}"})
    s=json.loads(urllib.request.urlopen(r,timeout=15).read())
    print(eid, s["state"], s.get("attributes",{}).get("detector_count"))
