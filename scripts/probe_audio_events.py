#!/usr/bin/env python3
"""Probe Axis event APIs for SoundPressureLevel topics."""
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])
IP = "192.168.68.201"

PATHS = [
    "/axis-cgi/eventlist.cgi",
    "/axis-cgi/param.cgi?action=list&group=Event",
    "/axis-cgi/param.cgi?action=list&group=Events",
    "/axis-cgi/param.cgi?action=list&group=MQTT",
]

for path in PATHS:
    r = requests.get(f"http://{IP}{path}", auth=auth, timeout=12)
    if r.status_code != 200:
        continue
    hits = [
        line.strip()
        for line in r.text.splitlines()
        if re.search(r"audio|sound|spl|pressure", line, re.I)
    ]
    if hits:
        print(f"\n=== {path} ===")
        for h in hits[:25]:
            print(h[:200])

# ONVIF ws-discovery style - try pull messages briefly via eventdata
r = requests.get(
    f"http://{IP}/axis-cgi/eventdata.cgi",
    auth=auth,
    timeout=12,
    params={"topic0": "tns1:AudioAnalytics"},
)
print("\neventdata AudioAnalytics:", r.status_code, r.text[:400])
