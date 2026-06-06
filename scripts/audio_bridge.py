#!/usr/bin/env python3
"""
AXIS Audio Analytics SPL → MQTT bridge.

Audio Analytics runs as a firmware plugin (audioanalytics.cgi), not a separate ACAP.
SPL Summary events (MaxSPL / MinSPL every ~60 s) are application data and are NOT
published via analytics-mqtt or standard MQTT event filters.

This bridge uses ONVIF PullPoint subscription and republishes to:
  axis/<zone>/audio/spl  {"max_spl": 45.2, "min_spl": 32.1}

Run: python scripts/audio_bridge.py
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import paho.mqtt.client as mqtt
import requests
from dotenv import load_dotenv
from paho.mqtt.client import CallbackAPIVersion
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")

CAMERAS = [
    {"zone": "front", "ip": "192.168.68.200"},
    {"zone": "driveway_wide", "ip": "192.168.68.201"},
    {"zone": "backyard", "ip": "192.168.68.203"},
]

# Summary SPL events — verified via GetEventInstances on Q3558
SPL_TOPIC = "tnsaxis:SoundPressureLevel/tnsaxis:Summary"

PULL_INTERVAL = 5
TIMEOUT = "PT70S"

CAM_USER = os.environ["CAM_USER"]
CAM_PASS = os.environ["CAM_PASS"]
MQTT_HOST = os.environ.get("HA_HOST", "192.168.68.175")
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASS = os.environ["MQTT_PASS"]

NS = {
    "SOAP-ENV": "http://www.w3.org/2003/05/soap-envelope",
    "tev": "http://www.onvif.org/ver10/events/wsdl",
    "wsnt": "http://docs.oasis-open.org/wsn/b-2",
    "tt": "http://www.onvif.org/ver10/schema",
    "tnsaxis": "http://www.axis.com/2009/event/topics",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("audio_bridge")


def soap_post(ip: str, body: str) -> str:
    r = requests.post(
        f"http://{ip}/vapix/services",
        data=body,
        headers={"Content-Type": "application/soap+xml; charset=utf-8"},
        auth=HTTPDigestAuth(CAM_USER, CAM_PASS),
        timeout=20,
    )
    r.raise_for_status()
    return r.text


def create_pullpoint(ip: str) -> str | None:
    envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
  xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
  xmlns:tnsaxis="http://www.axis.com/2009/event/topics">
  <SOAP-ENV:Body>
    <tev:CreatePullPointSubscription>
      <tev:Filter>
        <wsnt:TopicExpression Dialect="http://www.onvif.org/ver10/tev/topicExpression/ConcreteSet">
          {SPL_TOPIC}
        </wsnt:TopicExpression>
      </tev:Filter>
      <tev:InitialTerminationTime>{TIMEOUT}</tev:InitialTerminationTime>
    </tev:CreatePullPointSubscription>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
    text = soap_post(ip, envelope)
    m = re.search(r"<wsa5:Address[^>]*>([^<]+)</wsa5:Address>", text)
    if not m:
        m = re.search(r"<tev:SubscriptionReference>.*?<wsa:Address[^>]*>([^<]+)</wsa:Address>", text, re.S)
    if not m:
        log.warning("%s: no pullpoint address in response", ip)
        return None
    url = m.group(1).strip()
    url = url.replace("127.0.0.1", ip).replace("localhost", ip)
    if url.startswith("http"):
        return url
    return f"http://{ip}{url}" if url.startswith("/") else url


def pull_messages(url: str) -> list[dict]:
    envelope = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
  xmlns:tev="http://www.onvif.org/ver10/events/wsdl">
  <SOAP-ENV:Body>
    <tev:PullMessages>
      <tev:Timeout>PT5S</tev:Timeout>
      <tev:MessageLimit>10</tev:MessageLimit>
    </tev:PullMessages>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
    r = requests.post(
        url,
        data=envelope,
        headers={"Content-Type": "application/soap+xml; charset=utf-8"},
        auth=HTTPDigestAuth(CAM_USER, CAM_PASS),
        timeout=15,
    )
    if r.status_code != 200:
        return []
    return parse_spl_messages(r.text)


def parse_spl_messages(xml_text: str) -> list[dict]:
    results: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return results

    for msg in root.iter():
        if not msg.tag.endswith("NotificationMessage"):
            continue
        data: dict[str, float] = {}
        for item in msg.iter():
            tag = item.tag.split("}")[-1] if "}" in item.tag else item.tag
            if tag in ("MaxSPL", "MinSPL") and item.text:
                try:
                    data[tag.lower()] = float(item.text)
                except ValueError:
                    pass
        if data:
            results.append(data)
    return results


def publish_spl(client: mqtt.Client, zone: str, data: dict) -> None:
    topic = f"axis/{zone}/audio/spl"
    payload = {
        "max_spl": data.get("maxspl"),
        "min_spl": data.get("minspl"),
        "spl": data.get("maxspl"),
    }
    client.publish(topic, json.dumps(payload), qos=0, retain=True)
    log.info("%s SPL max=%s min=%s", zone, payload["max_spl"], payload["min_spl"])


def main() -> None:
    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_HOST, 1883, 60)
    client.loop_start()

    pullpoints: dict[str, str | None] = {c["zone"]: None for c in CAMERAS}

    log.info("Audio SPL bridge started (%d cameras)", len(CAMERAS))
    while True:
        for cam in CAMERAS:
            zone, ip = cam["zone"], cam["ip"]
            try:
                if not pullpoints[zone]:
                    pullpoints[zone] = create_pullpoint(ip)
                    if pullpoints[zone]:
                        log.info("%s pullpoint OK", zone)
                    else:
                        continue
                for data in pull_messages(pullpoints[zone]):
                    publish_spl(client, zone, data)
            except requests.RequestException as exc:
                log.warning("%s error: %s — renewing pullpoint", zone, exc)
                pullpoints[zone] = None
        time.sleep(PULL_INTERVAL)


if __name__ == "__main__":
    main()
