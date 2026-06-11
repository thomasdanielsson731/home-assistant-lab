#!/usr/bin/env python3
"""Minimal Home Assistant REST + WebSocket helpers for lab scripts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from websocket import create_connection

load_dotenv(Path(__file__).parent.parent / ".env")

HOST = os.environ.get("HA_HOST", "192.168.68.175")
TOKEN = os.environ.get("HA_TOKEN")
BASE = f"http://{HOST}:8123/api"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
WS_URI = f"ws://{HOST}:8123/api/websocket"


def require_token() -> None:
    if not TOKEN:
        raise SystemExit("HA_TOKEN not set in .env")


def ws_call(msg_type: str, msg_id: int = 1, timeout: int = 60, **extra: Any) -> Any:
    require_token()
    ws = create_connection(WS_URI, timeout=timeout)
    ws.settimeout(timeout)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    ws.recv()
    ws.send(json.dumps({"id": msg_id, "type": msg_type, **extra}))
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == msg_id:
            if not data.get("success", True):
                raise RuntimeError(data.get("error"))
            ws.close()
            return data.get("result")


def ws_fire_and_forget(msg_type: str, msg_id: int = 1, **extra: Any) -> None:
    """Send a WS command without waiting for long-running work (e.g. ZHA reconfigure)."""
    require_token()
    ws = create_connection(WS_URI, timeout=15)
    ws.settimeout(15)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    ws.recv()
    ws.send(json.dumps({"id": msg_id, "type": msg_type, **extra}))
    ws.close()


def zha_entry_id() -> str | None:
    require_token()
    r = requests.get(f"{BASE}/config/config_entries/entry", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return next((e["entry_id"] for e in r.json() if e["domain"] == "zha"), None)


def zha_end_devices() -> list[dict]:
    """Device registry entries for ZHA end devices (excludes coordinator)."""
    zha = zha_entry_id()
    if not zha:
        return []
    devices = ws_call("config/device_registry/list")
    return [
        d
        for d in devices
        if d.get("config_entries") and zha in d.get("config_entries", [])
        and "coordinator" not in (d.get("name") or "").lower()
        and (d.get("name") or "").lower() != "texas instruments cc2652"
    ]


def zha_network_devices() -> list[dict]:
    return ws_call("zha/devices") or []


def ieee_for_device(device_id: str, entities: list[dict]) -> str | None:
    for ent in entities:
        if ent.get("device_id") != device_id:
            continue
        uid = ent.get("unique_id") or ""
        if uid and ":" in uid.split("-")[0]:
            return uid.split("-")[0]
    for d in zha_network_devices():
        name = d.get("user_given_name") or d.get("name") or ""
        if device_id[:8] in str(d):
            pass
    return None


def device_ieee_map() -> dict[str, str]:
    """Map device registry id → IEEE from ZHA network list (by name match)."""
    reg = {d["id"]: d for d in zha_end_devices()}
    network = zha_network_devices()
    out: dict[str, str] = {}
    entities = ws_call("config/entity_registry/list")
    for dev_id, dev in reg.items():
        for ent in entities:
            if ent.get("device_id") != dev_id:
                continue
            uid = ent.get("unique_id") or ""
            if uid and len(uid.split("-")[0].split(":")) >= 8:
                out[dev_id] = uid.split("-")[0]
                break
        if dev_id in out:
            continue
        dev_name = (dev.get("name_by_user") or dev.get("name") or "").lower()
        for nd in network:
            if nd.get("device_type") == "Coordinator":
                continue
            nname = (nd.get("user_given_name") or nd.get("name") or "").lower()
            if dev_name and nname and dev_name == nname and nd.get("ieee"):
                out[dev_id] = nd["ieee"]
                break
    for nd in network:
        if nd.get("device_type") == "Coordinator":
            continue
        ieee = nd.get("ieee")
        if not ieee:
            continue
        for dev_id, dev in reg.items():
            if dev_id in out:
                continue
            if ieee in json.dumps(dev):
                out[dev_id] = ieee
    return out
