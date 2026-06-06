#!/usr/bin/env python3
"""Discover axis-cgi/audioanalytics.cgi methods."""
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])
IP = "192.168.68.201"

METHODS = [
    "getSupportedVersions",
    "getApiVersion",
    "getConfiguration",
    "getStatus",
    "getSoundPressureLevel",
    "getSpl",
    "getCurrentSpl",
    "getSplValue",
    "getLiveSpl",
    "getMetrics",
    "getStatistics",
    "listMethods",
]

for method in METHODS:
    for api in ("1.0", "1.1", "2.0"):
        body = {"apiVersion": api, "method": method}
        r = requests.post(
            f"http://{IP}/axis-cgi/audioanalytics.cgi",
            json=body,
            auth=auth,
            timeout=8,
        )
        if r.status_code != 200:
            continue
        try:
            data = r.json()
        except json.JSONDecodeError:
            continue
        err = data.get("error", {})
        if err.get("code") in (2103, 2104, 2105):  # unknown / missing param
            continue
        print(f"{method} api={api}: {json.dumps(data)[:400]}")
