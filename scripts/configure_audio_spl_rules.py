#!/usr/bin/env python3
"""
Create Axis action rules: SPL Summary → MQTT publish.

Audio Analytics runs as a firmware plugin (SoundPressureLevel).
Summary events (~60 s) are application data — use action rules, not MQTT event filters.

Usage: python scripts/configure_audio_spl_rules.py
"""

import os
import re
import sys
from pathlib import Path

import requests
from requests.auth import HTTPDigestAuth

_env = Path(__file__).parent.parent / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _require(key: str) -> str:
    v = os.environ.get(key)
    if not v:
        sys.exit(f"ERROR: {key} not set")
    return v


CAM_USER = _require("CAM_USER")
CAM_PASS = _require("CAM_PASS")

CAMERAS = [
    {"zone": "front", "ip": "192.168.68.200"},
    {"zone": "driveway_wide", "ip": "192.168.68.201"},
    {"zone": "backyard", "ip": "192.168.68.203"},
]

ACTION_NS = "http://www.axis.com/vapix/ws/action1"
START_EVENT = "tnsaxis:SoundPressureLevel/tnsaxis:Summary"
# Prefer setting payload in camera UI after rule creation — SOAP payload modifiers
# for MaxSPL/MinSPL are unreliable (#M / %M clash). Placeholder until UI edit:
PAYLOAD = '{"max_spl":#MaxSPL,"min_spl":#MinSPL,"spl":#MaxSPL}'


def soap(ip: str, body: str) -> tuple[int, str]:
    r = requests.post(
        f"http://{ip}/vapix/services",
        data=body,
        headers={"Content-Type": "application/soap+xml; charset=utf-8"},
        auth=HTTPDigestAuth(CAM_USER, CAM_PASS),
        timeout=20,
    )
    return r.status_code, r.text


def verify_audio_enabled(ip: str) -> bool:
    r = requests.post(
        f"http://{ip}/axis-cgi/audioanalytics.cgi",
        json={"apiVersion": "1.0", "method": "getPluginsSettings", "params": {}},
        auth=HTTPDigestAuth(CAM_USER, CAM_PASS),
        timeout=12,
    )
    return r.status_code == 200 and "SoundPressureLevel" in r.text and '"enable": true' in r.text


def remove_existing(ip: str, zone: str) -> None:
    _, rules = soap(
        ip,
        f"""<?xml version="1.0"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:aa="{ACTION_NS}">
  <SOAP-ENV:Body><aa:GetActionRules/></SOAP-ENV:Body>
</SOAP-ENV:Envelope>""",
    )
    for rid in re.findall(r"<aa:RuleID>(\d+)</aa:RuleID>", rules):
        name_m = re.search(
            rf"<aa:RuleID>{rid}</aa:RuleID>.*?<aa:Name>([^<]+)</aa:Name>",
            rules,
            re.S,
        )
        if name_m and f"ha_spl_mqtt_{zone}" in name_m.group(1):
            soap(
                ip,
                f"""<?xml version="1.0"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:aa="{ACTION_NS}">
  <SOAP-ENV:Body><aa:RemoveActionRule><aa:RuleID>{rid}</aa:RuleID></aa:RemoveActionRule></SOAP-ENV:Body>
</SOAP-ENV:Envelope>""",
            )

    _, configs = soap(
        ip,
        f"""<?xml version="1.0"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:aa="{ACTION_NS}">
  <SOAP-ENV:Body><aa:GetActionConfigurations/></SOAP-ENV:Body>
</SOAP-ENV:Envelope>""",
    )
    for block in re.findall(
        r"<aa:ActionConfiguration>.*?</aa:ActionConfiguration>", configs, re.S
    ):
        if f"ha_spl_mqtt_{zone}" not in block:
            continue
        cid_m = re.search(r"<aa:ConfigurationID>(\d+)</aa:ConfigurationID>", block)
        if cid_m:
            cid = cid_m.group(1)
            soap(
                ip,
                f"""<?xml version="1.0"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:aa="{ACTION_NS}">
  <SOAP-ENV:Body><aa:RemoveActionConfiguration><aa:ConfigurationID>{cid}</aa:ConfigurationID></aa:RemoveActionConfiguration></SOAP-ENV:Body>
</SOAP-ENV:Envelope>""",
            )


def add_mqtt_action(ip: str, zone: str) -> str | None:
    topic = f"axis/{zone}/audio/spl"
    body = f"""<?xml version="1.0" encoding="utf-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:aa="{ACTION_NS}">
  <SOAP-ENV:Body>
    <aa:AddActionConfiguration>
      <aa:NewActionConfiguration>
        <aa:Name>ha_spl_mqtt_{zone}</aa:Name>
        <aa:TemplateToken>com.axis.action.fixed.mqttpublish</aa:TemplateToken>
        <aa:Parameters>
          <aa:Parameter Name="topic" Value="{topic}" />
          <aa:Parameter Name="use_device_prefix" Value="false" />
          <aa:Parameter Name="payload" Value="{PAYLOAD}" />
          <aa:Parameter Name="qos" Value="0" />
          <aa:Parameter Name="retained" Value="true" />
        </aa:Parameters>
      </aa:NewActionConfiguration>
    </aa:AddActionConfiguration>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
    code, text = soap(ip, body)
    if code != 200 or "Fault" in text:
        print(f"    AddActionConfiguration failed: {text[text.find('Reason'):text.find('Reason')+200] if 'Reason' in text else text[:200]}")
        return None
    m = re.search(r"<aa:ConfigurationID>(\d+)</aa:ConfigurationID>", text)
    return m.group(1) if m else None


def add_spl_rule(ip: str, zone: str, config_id: str) -> bool:
    body = f"""<?xml version="1.0" encoding="utf-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:aa="{ACTION_NS}"
  xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
  xmlns:tns1="http://www.onvif.org/ver10/topics"
  xmlns:tnsaxis="http://www.axis.com/2009/event/topics">
  <SOAP-ENV:Body>
    <aa:AddActionRule>
      <aa:NewActionRule>
        <aa:Name>ha_spl_mqtt_{zone}</aa:Name>
        <aa:Enabled>true</aa:Enabled>
        <aa:StartEvent>
          <wsnt:TopicExpression Dialect="http://www.onvif.org/ver10/tev/topicExpression/ConcreteSet">{START_EVENT}</wsnt:TopicExpression>
        </aa:StartEvent>
        <aa:PrimaryAction>{config_id}</aa:PrimaryAction>
      </aa:NewActionRule>
    </aa:AddActionRule>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
    code, text = soap(ip, body)
    if code != 200 or "Fault" in text:
        print(f"    AddActionRule failed: {text[text.find('Reason'):text.find('Reason')+200] if 'Reason' in text else text[:200]}")
        return False
    return "RuleID" in text


def main() -> None:
    ok = True
    for cam in CAMERAS:
        zone, ip = cam["zone"], cam["ip"]
        print(f"\n{'=' * 50}\n{zone} ({ip})")

        if not verify_audio_enabled(ip):
            print("  SKIP — SoundPressureLevel not enabled (or camera unreachable)")
            ok = False
            continue
        print("  OK Audio Analytics SPL enabled")

        remove_existing(ip, zone)
        config_id = add_mqtt_action(ip, zone)
        if not config_id:
            ok = False
            continue
        print(f"  OK MQTT action config id={config_id}")

        if add_spl_rule(ip, zone, config_id):
            print(f"  OK action rule -> axis/{zone}/audio/spl")
        else:
            ok = False

    print()
    if ok:
        print("Done. SPL MQTT rules active. Verify: subscribe axis/+/audio/spl (~60 s).")
    else:
        print("Some cameras failed — see docs/runbooks/audio-analytics-setup.md for manual UI fallback.")


if __name__ == "__main__":
    main()
