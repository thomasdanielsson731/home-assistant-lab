#!/usr/bin/env python3
"""Deep probe for AXIS Audio Analytics on cameras."""
import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])

CAMERAS = [
    ("front", "192.168.68.200"),
    ("driveway_wide", "192.168.68.201"),
    ("backyard", "192.168.68.203"),
]


def get(ip, path):
    r = requests.get(f"http://{ip}{path}", auth=auth, timeout=10)
    return r.status_code, r.text


def post(ip, path, body):
    r = requests.post(f"http://{ip}{path}", json=body, auth=auth, timeout=10)
    return r.status_code, r.text


for zone, ip in CAMERAS:
    print(f"\n{'='*55}\n{zone} ({ip})")

    code, text = get(ip, "/axis-cgi/applications/list.cgi")
    print(f"applications [{code}]:")
    for line in text.splitlines():
        if line.strip():
            print(f"  {line[:140]}")

    for method in (
        "getConfiguration",
        "getStatus",
        "getSoundPressureLevel",
        "getSpl",
        "getCurrentSpl",
    ):
        code, text = post(
            ip,
            "/local/audioanalytics/control.cgi",
            {"apiVersion": "1.0", "method": method},
        )
        if code == 200 and "not found" not in text.lower()[:100]:
            print(f"audioanalytics.{method} [{code}]: {text[:350]}")

    for path in (
        "/local/audioanalytics/",
        "/local/audio-analytics/",
        "/axis-cgi/audioanalytics.cgi",
    ):
        code, text = get(ip, path)
        if code not in (404, 0):
            print(f"{path} [{code}]: {text[:200]}")

    code, text = post(
        ip,
        "/axis-cgi/mqtt/event.cgi",
        {"apiVersion": "1.2", "method": "getEventPublicationConfig"},
    )
    if code == 200:
        try:
            cfg = json.loads(text)
            flist = cfg.get("data", {}).get("eventFilterList", [])
            print(f"mqtt event filters ({len(flist)}):")
            for f in flist:
                print(f"  {f.get('topicFilter')}")
        except json.JSONDecodeError:
            print(f"mqtt events: {text[:300]}")

    for ver in ("v1", "v1beta1"):
        code, text = get(ip, f"/config/rest/openapi/{ver}")
        if code == 200 and len(text) > 300:
            keys = set(re.findall(r"com\.axis\.[^\s\"'\\]+", text))
            audio = sorted(k for k in keys if re.search(r"audio|sound|spl", k, re.I))
            if audio:
                print(f"openapi/{ver} audio keys: {audio}")
