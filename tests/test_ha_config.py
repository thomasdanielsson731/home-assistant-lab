"""Regression tests for HA YAML config layout (dashboard split, automations)."""

from __future__ import annotations

from pathlib import Path

import re

import yaml

REPO = Path(__file__).resolve().parents[1]
HA = REPO / "config" / "home-assistant"
DASHBOARDS = HA / "dashboards"


def _load_dashboard_yaml(filename: str) -> dict:
    text = (DASHBOARDS / filename).read_text(encoding="utf-8")
    text = re.sub(r"!secret\s+\S+", '"/secret/placeholder"', text)
    return yaml.safe_load(text)

ANNA_DASHBOARDS = {
    "home-hem.yaml": "home",
    "home-cameras.yaml": "cameras",
    "home-security.yaml": "security",
    "home-events.yaml": "events",
    "home-rooms.yaml": "rooms",
}


def test_dashboard_split_files():
    for filename in ANNA_DASHBOARDS:
        assert (DASHBOARDS / filename).is_file()
    assert (DASHBOARDS / "home-tech.yaml").is_file()
    assert not (DASHBOARDS / "home-lab.yaml").exists()
    assert not (DASHBOARDS / "home-anna.yaml").exists()


def test_anna_dashboards_single_view_each():
    for filename, path in ANNA_DASHBOARDS.items():
        data = _load_dashboard_yaml(filename)
        assert len(data["views"]) == 1
        assert data["views"][0]["path"] == path


def test_tech_dashboard_views():
    data = _load_dashboard_yaml("home-tech.yaml")
    paths = {view["path"] for view in data["views"]}
    assert paths == {"tech", "ops"}


def test_configuration_registers_split_dashboards():
    text = (HA / "configuration.yaml").read_text(encoding="utf-8")
    for panel_id, filename in (
        ("home-hem", "home-hem.yaml"),
        ("home-cameras", "home-cameras.yaml"),
        ("home-security", "home-security.yaml"),
        ("home-events", "home-events.yaml"),
        ("home-rooms", "home-rooms.yaml"),
    ):
        assert f"{panel_id}:" in text
        assert f"filename: dashboards/{filename}" in text
    assert "home-tech:" in text
    assert "filename: dashboards/home-tech.yaml" in text
    assert "require_admin: true" in text
    assert "home-lab:" not in text


def test_loitering_automation_enabled():
    automations = yaml.safe_load(
        (HA / "automations/security/aoa_loitering_alert.yaml").read_text(encoding="utf-8")
    )
    auto = automations[0]
    assert auto["id"] == "aoa_loitering_detected"
    assert auto["initial_state"] is True
    entity_ids = auto["trigger"][0]["entity_id"]
    assert len(entity_ids) == 6
    message = auto["action"][0]["data"]["message"]
    assert "trigger.entity_id" in message
    assert "_aoa_loitering" in message


def test_multisensor_entry_notification_enabled():
    text = (HA / "automations/security/smart_notifications.yaml").read_text(encoding="utf-8")
    assert "notify_person_entry_multisensor" in text
    assert "initial_state: true" in text


def test_light_control_scripts_defined():
    scripts = yaml.safe_load((HA / "scripts/light_controls.yaml").read_text(encoding="utf-8"))
    for key in (
        "light_turn_off_common",
        "light_turn_off_kitchen",
        "light_turn_off_living_room",
        "light_turn_off_bedroom",
    ):
        assert key in scripts


def test_anna_lampor_tanda_uses_mushroom_light_cards():
    text = (DASHBOARDS / "home-hem.yaml").read_text(encoding="utf-8")
    assert "LAMPOR TÄNDA" in text
    assert "custom:mushroom-light-card" in text
    assert "type: entities" not in text
    assert "entity-filter" not in text


def test_sidebar_script_keeps_tech_panel():
    text = (REPO / "scripts/configure_ha_sidebar.py").read_text(encoding="utf-8")
    assert 'DEFAULT_PANEL = "home-hem"' in text
    assert 'TECH_PANEL = "home-tech"' in text
    assert "home-cameras" in text


def test_no_stale_home_lab_navigation_paths():
    for filename in (*ANNA_DASHBOARDS.keys(), "home-tech.yaml"):
        text = (DASHBOARDS / filename).read_text(encoding="utf-8")
        assert "/lovelace/home-lab" not in text
