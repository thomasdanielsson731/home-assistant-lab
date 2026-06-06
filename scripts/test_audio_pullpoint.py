#!/usr/bin/env python3
"""Test PullPoint subscription for SPL Summary."""
import os
import re
import time

import requests
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])
IP = "192.168.68.201"

TOPICS = [
    "",  # no filter — catch any SPL summary in 75s
    "tnsaxis:SoundPressureLevel/tnsaxis:Summary",
    "tnsaxis:SoundPressureLevel/Summary",
    "tnsaxis:SoundPressureLevel//.",
]

for topic in TOPICS:
    filter_xml = ""
    if topic:
        filter_xml = f"""
      <tev:Filter>
        <wsnt:TopicExpression Dialect="http://www.onvif.org/ver10/tev/topicExpression/ConcreteSet">
          {topic}
        </wsnt:TopicExpression>
      </tev:Filter>"""
    envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
  xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
  xmlns:tnsaxis="http://www.axis.com/2009/event/topics">
  <SOAP-ENV:Body>
    <tev:CreatePullPointSubscription>{filter_xml}
      <tev:InitialTerminationTime>PT90S</tev:InitialTerminationTime>
    </tev:CreatePullPointSubscription>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
    r = requests.post(
        f"http://{IP}/vapix/services",
        data=envelope,
        headers={"Content-Type": "application/soap+xml; charset=utf-8"},
        auth=auth,
        timeout=20,
    )
    label = topic or "(no filter)"
    print(f"\n=== topic {label} status {r.status_code} ===")
    if r.status_code != 200:
        print(r.text[:300])
        continue
    m = re.search(r"<wsa5:Address[^>]*>([^<]+)</wsa5:Address>", r.text)
    if not m:
        print("no address:", r.text[:400])
        continue
    url = m.group(1).strip()
    if url.startswith("/"):
        url = f"http://{IP}{url}"
    url = url.replace("127.0.0.1", IP).replace("localhost", IP)
    print("pullpoint:", url)
    pull = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:tev="http://www.onvif.org/ver10/events/wsdl">
  <SOAP-ENV:Body>
    <tev:PullMessages><tev:Timeout>PT70S</tev:Timeout><tev:MessageLimit>5</tev:MessageLimit></tev:PullMessages>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
    r2 = requests.post(url, data=pull, headers={"Content-Type": "application/soap+xml"}, auth=auth, timeout=80)
    print("pull status", r2.status_code)
    if "MaxSPL" in r2.text or "MinSPL" in r2.text or "SoundPressure" in r2.text:
        print("GOT SPL DATA:", r2.text[:800])
    elif "Fault" in r2.text:
        print("fault:", r2.text[:400])
    else:
        print("empty/short:", r2.text[:300])
