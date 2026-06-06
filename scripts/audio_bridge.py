#!/usr/bin/env python3
"""
AXIS Audio Analytics SPL → MQTT bridge.

SPL Summary events are application data — not available via MQTT event filters
or reliable action-rule payload modifiers over SOAP. This bridge subscribes via
the VAPIX WebSocket event API and republishes to:

  axis/<zone>/audio/spl  {"max_spl": 55.3, "min_spl": 36.8, "spl": 55.3}

Requires AXIS_ROOT_PASSWORD in .env (root digest for wssession + ws-data-stream).

Run: python scripts/audio_bridge.py
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import requests
from dotenv import load_dotenv
from paho.mqtt.client import CallbackAPIVersion
from requests.auth import HTTPDigestAuth
from websocket import WebSocketConnectionClosedException, create_connection

load_dotenv(Path(__file__).parent.parent / ".env")

CAMERAS = [
    {"zone": "front", "ip": "192.168.68.200"},
    {"zone": "driveway_wide", "ip": "192.168.68.201"},
    {"zone": "backyard", "ip": "192.168.68.203"},
]

SPL_TOPIC_FILTER = "tnsaxis:SoundPressureLevel/tnsaxis:Summary"

CAM_USER = os.environ.get("AXIS_ROOT_USER") or os.environ["CAM_USER"]
CAM_PASS = os.environ.get("AXIS_ROOT_PASSWORD") or os.environ["CAM_PASS"]
MQTT_HOST = os.environ.get("HA_HOST", "192.168.68.175")
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASS = os.environ["MQTT_PASS"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("audio_bridge")

ACTION_NS = "http://www.axis.com/vapix/ws/action1"


def _soap(ip: str, body: str) -> str:
    r = requests.post(
        f"http://{ip}/vapix/services",
        data=body,
        headers={"Content-Type": "application/soap+xml; charset=utf-8"},
        auth=HTTPDigestAuth(CAM_USER, CAM_PASS),
        timeout=20,
    )
    return r.text


def remove_camera_spl_rules() -> None:
    """Drop on-camera MQTT SPL actions so only this bridge publishes."""
    for cam in CAMERAS:
        zone, ip = cam["zone"], cam["ip"]
        rules = _soap(
            ip,
            f'<?xml version="1.0"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:aa="{ACTION_NS}"><SOAP-ENV:Body><aa:GetActionRules/></SOAP-ENV:Body></SOAP-ENV:Envelope>',
        )
        for rid in re.findall(r"<aa:RuleID>(\d+)</aa:RuleID>", rules):
            block = rules[rules.find(f"<aa:RuleID>{rid}</aa:RuleID>") : rules.find(f"<aa:RuleID>{rid}</aa:RuleID>") + 400]
            if "ha_spl_mqtt" in block or "ha_spl_test" in block:
                _soap(
                    ip,
                    f'<?xml version="1.0"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:aa="{ACTION_NS}"><SOAP-ENV:Body><aa:RemoveActionRule><aa:RuleID>{rid}</aa:RuleID></aa:RemoveActionRule></SOAP-ENV:Body></SOAP-ENV:Envelope>',
                )
        cfgs = _soap(
            ip,
            f'<?xml version="1.0"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:aa="{ACTION_NS}"><SOAP-ENV:Body><aa:GetActionConfigurations/></SOAP-ENV:Body></SOAP-ENV:Envelope>',
        )
        for block in re.findall(
            r"<aa:ActionConfiguration>.*?</aa:ActionConfiguration>", cfgs, re.S
        ):
            if "ha_spl_mqtt" not in block and "audio/spl" not in block:
                continue
            cid_m = re.search(r"<aa:ConfigurationID>(\d+)</aa:ConfigurationID>", block)
            if cid_m:
                _soap(
                    ip,
                    f'<?xml version="1.0"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:aa="{ACTION_NS}"><SOAP-ENV:Body><aa:RemoveActionConfiguration><aa:ConfigurationID>{cid_m.group(1)}</aa:ConfigurationID></aa:RemoveActionConfiguration></SOAP-ENV:Body></SOAP-ENV:Envelope>',
                )
        log.info("%s removed on-camera SPL MQTT rules (bridge-only)", zone)


def get_wssession(ip: str) -> str:
    r = requests.get(
        f"http://{ip}/axis-cgi/wssession.cgi",
        auth=HTTPDigestAuth(CAM_USER, CAM_PASS),
        timeout=10,
    )
    r.raise_for_status()
    token = r.text.strip()
    if not re.match(r"^-?\d+$", token):
        raise RuntimeError(f"{ip}: invalid wssession token")
    return token


def parse_spl_data(data: dict) -> dict[str, float] | None:
    out: dict[str, float] = {}
    for key in ("MaxSPL", "MinSPL", "LEQ"):
        if key in data:
            try:
                out[key.lower()] = float(data[key])
            except (TypeError, ValueError):
                pass
    if "maxspl" not in out:
        return None
    return out


def publish_spl(client: mqtt.Client, zone: str, data: dict[str, float]) -> None:
    topic = f"axis/{zone}/audio/spl"
    payload = {
        "max_spl": data["maxspl"],
        "min_spl": data.get("minspl"),
        "spl": data["maxspl"],
    }
    client.publish(topic, json.dumps(payload), qos=0, retain=True)
    log.info(
        "%s SPL max=%.1f min=%s",
        zone,
        payload["max_spl"],
        f"{payload['min_spl']:.1f}" if payload["min_spl"] is not None else "—",
    )


def stream_camera(zone: str, ip: str, client: mqtt.Client) -> None:
    while True:
        try:
            token = get_wssession(ip)
            url = f"ws://{ip}/vapix/ws-data-stream?wssession={token}&sources=events"
            ws = create_connection(url, timeout=90)
            ws.send(
                json.dumps(
                    {
                        "apiVersion": "1.0",
                        "context": f"spl-{zone}",
                        "method": "events:configure",
                        "params": {
                            "eventFilterList": [{"topicFilter": SPL_TOPIC_FILTER}]
                        },
                    }
                )
            )
            ack = json.loads(ws.recv())
            if ack.get("error"):
                raise RuntimeError(f"events:configure failed: {ack['error']}")
            log.info("%s WebSocket subscribed", zone)

            while True:
                ws.settimeout(120)
                raw = ws.recv()
                msg = json.loads(raw)
                if msg.get("method") != "events:notify":
                    continue
                note = msg.get("params", {}).get("notification", {})
                spl = parse_spl_data(note.get("message", {}).get("data", {}))
                if spl:
                    publish_spl(client, zone, spl)
        except WebSocketConnectionClosedException:
            log.warning("%s WebSocket closed — reconnecting", zone)
        except Exception as exc:
            log.warning("%s error: %s — retry in 10s", zone, exc)
            time.sleep(10)


def main() -> None:
    if not os.environ.get("AXIS_ROOT_PASSWORD"):
        log.warning(
            "AXIS_ROOT_PASSWORD not set — using CAM_USER (WebSocket may fail)"
        )

    mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.connect(MQTT_HOST, 1883, 60)
    mqtt_client.loop_start()

    remove_camera_spl_rules()
    log.info("Audio SPL bridge started (%d cameras)", len(CAMERAS))
    threads = [
        threading.Thread(
            target=stream_camera,
            args=(cam["zone"], cam["ip"], mqtt_client),
            name=f"spl-{cam['zone']}",
            daemon=True,
        )
        for cam in CAMERAS
    ]
    for t in threads:
        t.start()
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
