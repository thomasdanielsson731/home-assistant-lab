#!/usr/bin/env python3
"""Fetch Axis GetEventInstances via SOAP to find AudioAnalytics topics."""
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])
IP = os.environ.get("PROBE_IP", "192.168.68.201")

SOAP = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://www.w3.org/2003/05/soap-envelope"
  xmlns:aev="http://www.axis.com/vapix/ws/event1">
  <soapenv:Header/>
  <soapenv:Body>
    <aev:GetEventInstances/>
  </soapenv:Body>
</soapenv:Envelope>"""

r = requests.post(
    f"http://{IP}/vapix/services",
    data=SOAP,
    headers={"Content-Type": "application/soap+xml; charset=utf-8"},
    auth=auth,
    timeout=15,
)
print("status", r.status_code)
text = r.text
out = Path(__file__).parent.parent / "_event_instances.xml"
out.write_text(text, encoding="utf-8")
print("saved", out)
for m in re.findall(r"tns1:[A-Za-z0-9_/]+|tnsaxis:[A-Za-z0-9_]+", text):
    if re.search(r"audio|sound|spl|pressure|level", m, re.I):
        print(m)
# also print nice names near audio
for line in text.replace("><", ">\n<").splitlines():
    if re.search(r"audio|sound|spl|pressure|Sound", line, re.I):
        print(line[:250])
