#!/usr/bin/env python3
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])
IP = "192.168.68.201"

create = """<?xml version="1.0"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:tev="http://www.onvif.org/ver10/events/wsdl">
  <SOAP-ENV:Body>
    <tev:CreatePullPointSubscription>
      <tev:InitialTerminationTime>PT90S</tev:InitialTerminationTime>
    </tev:CreatePullPointSubscription>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

r = requests.post(
    f"http://{IP}/vapix/services",
    data=create,
    headers={"Content-Type": "application/soap+xml"},
    auth=auth,
    timeout=20,
)
print("create", r.status_code)
if r.status_code != 200:
    print(r.text[:500])
    raise SystemExit(1)
m = re.search(r"<wsa5:Address[^>]*>([^<]+)</wsa5:Address>", r.text)
url = m.group(1).replace("127.0.0.1", IP).replace("localhost", IP)
print("pullpoint", url)
sub_id = re.search(r"SubscriptionId>([^<]+)<", r.text)
if sub_id:
    print("subscriptionId", sub_id.group(1))
for m in re.finditer(r"Address[^>]*>([^<]+)<", r.text):
    print("addr", m.group(1))

pull = """<?xml version="1.0"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:tev="http://www.onvif.org/ver10/events/wsdl">
  <SOAP-ENV:Body>
    <tev:PullMessages>
      <tev:Timeout>PT75S</tev:Timeout>
      <tev:MessageLimit>30</tev:MessageLimit>
    </tev:PullMessages>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

session = requests.Session()
session.auth = auth
for target_name, target_url in [("onvif", url), ("vapix", f"http://{IP}/vapix/services")]:
    r2 = session.post(
        target_url,
        data=pull,
        headers={"Content-Type": "application/soap+xml"},
        timeout=90,
    )
    print(f"pull via {target_name}", r2.status_code, "len", len(r2.text))
    if r2.status_code == 401:
        print(r2.text[:200])
        continue
for kw in ("MaxSPL", "MinSPL", "LEQ", "SoundPressure", "Summary"):
    print(f"  {kw}: {r2.text.count(kw)}")
topics = set(re.findall(r"<wsnt:Topic[^>]*>([^<]+)</wsnt:Topic>", r2.text))
for t in sorted(topics):
    if re.search(r"sound|audio|spl", t, re.I):
        print("topic", t)
if "MaxSPL" in r2.text:
    i = r2.text.find("MaxSPL")
    print("sample", r2.text[max(0, i - 80) : i + 120])
