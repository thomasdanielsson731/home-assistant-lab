#!/usr/bin/env python3
"""
Configure MQTT client and AOA scenarios on all Axis cameras via VAPIX.

Usage:  python scripts/configure_cameras.py

Requires: pip install requests

MQTT note: MQTT broker config requires firmware UI access for v12.x cameras
(activateClient with broker params). Script activates if already configured,
and reports if manual UI step is needed.

AOA note: Uses /local/objectanalytics/control.cgi (ACAP path, firmware-independent).
Axis coordinate system: top-left=(-1,-1), bottom-right=(1,1).
"""

import os, sys, time, json
from pathlib import Path
import requests
from requests.auth import HTTPDigestAuth

# Load .env from repo root (two levels up from scripts/)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        if _line.strip() and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

def _require(key):
    v = os.environ.get(key)
    if not v:
        sys.exit(f"ERROR: {key} not set — add it to .env (see .env.example)")
    return v

# ---------------------------------------------------------------------------
MQTT_BROKER   = os.environ.get("HA_HOST", "192.168.68.175")
MQTT_PORT     = 1883
MQTT_USER     = _require("MQTT_USER")
MQTT_PASS_VAL = _require("MQTT_PASS")

CAM_USER = _require("CAM_USER")
CAM_PASS = _require("CAM_PASS")

CAMERAS = [
    {"zone": "front",         "ip": "192.168.68.200"},  # P3288-LVE
    {"zone": "driveway_wide", "ip": "192.168.68.203"},  # Q3558-LVE
    {"zone": "driveway_id",   "ip": "192.168.68.204"},  # M2036-LE
    {"zone": "backyard",      "ip": "192.168.68.202"},  # Q1656-LE
    {"zone": "storage_ext",   "ip": "192.168.68.205"},  # M1055-L
    {"zone": "storage_int",   "ip": "192.168.68.206"},  # Q1656
]

# Axis coordinate system: full frame = corners at (-1,-1)..(1,1)
FULL_FRAME = [[-1, -1], [-1, 1], [1, 1], [1, -1]]

AOA_SCENARIOS = [
    {
        "name":    "PersonOccupancy",
        "type":    "occupancyInArea",
        "classes": ["human"],
        "zones":   ["front", "driveway_wide", "driveway_id",
                    "backyard", "storage_ext", "storage_int"],
    },
    {
        "name":    "VehicleOcc",   # max 15 chars
        "type":    "occupancyInArea",
        "classes": ["vehicle"],
        "zones":   ["front", "driveway_wide", "driveway_id"],
    },
    # Loitering: type "loitering" not supported in current AOA firmware.
    # Configure manually via camera UI as a Motion scenario with time filter.
]

# ---------------------------------------------------------------------------

def vapix(ip, path, payload):
    auth = HTTPDigestAuth(CAM_USER, CAM_PASS)
    try:
        r = requests.post(f"http://{ip}{path}", json=payload, auth=auth, timeout=10)
    except requests.exceptions.ConnectionError:
        return {"_error": "connection refused"}
    except requests.exceptions.Timeout:
        return {"_error": "timeout"}
    if r.status_code not in (200, 201):
        return {"_error": f"HTTP {r.status_code}"}
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text[:200]}


def get_serial(ip):
    r = vapix(ip, "/axis-cgi/basicdeviceinfo.cgi",
              {"apiVersion": "1.0", "method": "getAllProperties"})
    return r.get("data", {}).get("propertyList", {}).get("SerialNumber", "UNKNOWN")


def configure_mqtt(ip, zone):
    # Use configureClient (API 1.5) — discovered by reading the camera web UI JS source.
    # The public VAPIX docs only mention updateClient (removed in 1.6), but the UI uses
    # configureClient (added in 1.5) which requires the camera's serial-derived clientId.
    serial    = get_serial(ip)
    client_id = f"client_{serial}"
    print(f"  [MQTT] configureClient -> {MQTT_BROKER}:{MQTT_PORT}  prefix=axis/{zone}")

    result = vapix(ip, "/axis-cgi/mqtt/client.cgi", {
        "apiVersion": "1.5",
        "method": "configureClient",
        "params": {
            "clientId":          client_id,
            "server":            {"protocol": "tcp", "host": MQTT_BROKER, "port": MQTT_PORT},
            "username":          MQTT_USER,
            "password":          MQTT_PASS_VAL,
            "deviceTopicPrefix": f"axis/{zone}",
            "keepAliveInterval": 60,
            "connectTimeout":    60,
            "cleanSession":      True,
            "autoReconnect":     True,
            "keepExistingPassword": False,
        }
    })
    err = result.get("error", {})
    if isinstance(err, dict) and err.get("code"):
        print(f"    FAIL configureClient: {err.get('message')}")
        return False

    result2 = vapix(ip, "/axis-cgi/mqtt/client.cgi",
                    {"apiVersion": "1.5", "method": "activateClient"})
    err2 = result2.get("error", {})
    if isinstance(err2, dict) and err2.get("code"):
        print(f"    FAIL activateClient: {err2.get('message')}")

    time.sleep(5)
    status = vapix(ip, "/axis-cgi/mqtt/client.cgi",
                   {"apiVersion": "1.6", "method": "getClientStatus"})
    conn = status.get("data", {}).get("status", {}).get("connectionStatus", "?")
    host = status.get("data", {}).get("config", {}).get("server", {}).get("host", "?")
    ok   = conn == "connected"
    print(f"    {'OK' if ok else 'WARN'} host={host} connection={conn}")
    return ok


def configure_event_publication(ip, zone):
    # includeTopicNamespaces=True (default) adds ONVIF namespace prefixes, e.g.
    # axis/<zone>/event/tns1:Analytics/tnsaxis:ObjectAnalytics/...
    # HA sensors expect clean paths without namespaces:
    # axis/<zone>/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active
    # FW 12.x: setEventPublicationConfig removed; use configureEventPublication (API 1.2).
    # Note: scenario events still need UI "Add condition" OR the aoa_bridge.py poller.
    print(f"  [MQTT-EVT] configureEventPublication  includeTopicNamespaces=false")
    result = vapix(ip, "/axis-cgi/mqtt/event.cgi", {
        "apiVersion": "1.2",
        "method": "configureEventPublication",
        "params": {
            "topicPrefix":                "default",
            "customTopicPrefix":          "",
            "appendEventTopic":           True,
            "includeTopicNamespaces":     False,
            "includeSerialNumberInPayload": False,
            "eventFilterList": [
                {"topicFilter": "tns1:Analytics/tnsaxis:ObjectAnalytics/ScenarioOccupancy",
                 "qos": 0, "retain": "none"},
                {"topicFilter": "tns1:Analytics/tnsaxis:ObjectAnalytics/ScenarioLoitering",
                 "qos": 0, "retain": "none"},
            ],
        }
    })
    err = result.get("error", {})
    if isinstance(err, dict) and err.get("code"):
        print(f"    FAIL: {err.get('message')}")
        return False
    print(f"    OK")
    return True


def get_aoa_scenarios(ip):
    r = vapix(ip, "/local/objectanalytics/control.cgi",
              {"apiVersion": "1.0", "method": "getConfiguration"})
    return {s["name"]: s for s in r.get("data", {}).get("scenarios", [])}


def create_aoa_scenario(ip, scenario_def, existing, current_data):
    name = scenario_def["name"]
    if name in existing:
        print(f"  [AOA] {name} -- already exists, skipping")
        return True

    print(f"  [AOA] Creating {name} ({scenario_def['type']}) ...")
    existing_ids = {s.get("id", 0) for s in current_data.get("scenarios", [])}
    new_id = max(existing_ids) + 1 if existing_ids else 1

    new_scenario = {
        "id":      new_id,
        "name":    name,
        "type":    scenario_def["type"],
        "devices": [{"id": 1}],
        "objectClassifications": [{"type": c} for c in scenario_def["classes"]],
        "triggers": [{"type": "includeArea", "vertices": FULL_FRAME}],
        "filters": [],
        "eventInterval":   {"enabled": False},
        "metadataOverlay": None,
        "thresholdConfiguration": {
            "enabled":      False,
            "thresholds":   [{"level": 0, "type": "moreThan"}],
            "triggerDelay": 0,
        },
    }
    if scenario_def.get("minTimeMs"):
        new_scenario["presetLoiteringTime"] = scenario_def["minTimeMs"]

    updated_params = {
        "devices":         current_data.get("devices", [{"id": 1}]),
        "metadataOverlay": current_data.get("metadataOverlay", []),
        "scenarios":       list(current_data.get("scenarios", [])) + [new_scenario],
    }

    r = vapix(ip, "/local/objectanalytics/control.cgi",
              {"apiVersion": "1.0", "method": "setConfiguration",
               "params": updated_params})

    err = r.get("error")
    if err and isinstance(err, dict) and err.get("code", 0) != 0:
        print(f"    FAIL {err}")
        return False
    if "_error" in r:
        print(f"    FAIL {r}")
        return False

    # Re-read to confirm scenario was saved
    cfg = vapix(ip, "/local/objectanalytics/control.cgi",
                {"apiVersion": "1.0", "method": "getConfiguration"})
    saved = {s["name"] for s in cfg.get("data", {}).get("scenarios", [])}
    if name in saved:
        print(f"    OK  confirmed in camera config")
        # Update current_data reference for next scenario in loop
        current_data["scenarios"] = cfg["data"]["scenarios"]
        return True

    print(f"    WARN scenario not found after write")
    return False

# ---------------------------------------------------------------------------

def main():
    results = {}
    for cam in CAMERAS:
        zone, ip = cam["zone"], cam["ip"]
        print(f"\n{'='*60}")
        print(f"Camera: {zone}  ({ip})")
        print(f"{'='*60}")

        info  = vapix(ip, "/axis-cgi/basicdeviceinfo.cgi",
                      {"apiVersion": "1.0", "method": "getAllProperties"})
        if "_error" in info:
            print(f"  SKIP — camera unreachable ({info['_error']})")
            results[zone] = {"mqtt": False, "aoa": {}, "skip": True}
            continue
        props = info.get("data", {}).get("propertyList", {})
        print(f"  {props.get('ProdShortName','?')}  FW:{props.get('Version','?')}"
              f"  SoC:{props.get('Soc','?')}")

        mqtt_ok = configure_mqtt(ip, zone)
        configure_event_publication(ip, zone)

        current_cfg  = vapix(ip, "/local/objectanalytics/control.cgi",
                             {"apiVersion": "1.0", "method": "getConfiguration"})
        current_data = current_cfg.get("data", {"scenarios": [], "devices": [{"id": 1}]})
        existing     = {s["name"]: s for s in current_data.get("scenarios", [])}
        aoa_results  = {}
        for s in AOA_SCENARIOS:
            if zone not in s["zones"]:
                continue
            aoa_results[s["name"]] = create_aoa_scenario(ip, s, existing, current_data)

        results[zone] = {"mqtt": mqtt_ok, "aoa": aoa_results}

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    all_ok = True
    for zone, r in results.items():
        if r.get("skip"):
            print(f"  {zone:15s}  SKIP (unreachable)")
            all_ok = False
            continue
        mqtt = "OK  " if r["mqtt"] else "MANUAL"
        aoa  = "  ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in r["aoa"].items())
        print(f"  {zone:15s}  MQTT:{mqtt}  AOA: {aoa or 'none'}")
        if not r["mqtt"] or not all(r["aoa"].values()):
            all_ok = False

    print(f"\n{'OK - all done' if all_ok else 'Some steps need manual attention (see MANUAL above)'}")


if __name__ == "__main__":
    main()
