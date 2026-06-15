"""Regression tests for HA YAML config layout (dashboard split, automations)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
HA = REPO / "config" / "home-assistant"
DASHBOARDS = HA / "dashboards"


def test_dashboard_split_files():
    assert (DASHBOARDS / "home-anna.yaml").is_file()
    assert (DASHBOARDS / "home-tech.yaml").is_file()
    assert not (DASHBOARDS / "home-lab.yaml").exists()


def test_anna_dashboard_views():
    data = yaml.safe_load((DASHBOARDS / "home-anna.yaml").read_text(encoding="utf-8"))
    paths = {view["path"] for view in data["views"]}
    assert paths == {"home", "cameras", "security", "rooms"}


def test_tech_dashboard_views():
    data = yaml.safe_load((DASHBOARDS / "home-tech.yaml").read_text(encoding="utf-8"))
    paths = {view["path"] for view in data["views"]}
    assert paths == {"tech", "ops"}


def test_configuration_registers_split_dashboards():
    text = (HA / "configuration.yaml").read_text(encoding="utf-8")
    assert "home-lab:" in text
    assert "filename: dashboards/home-anna.yaml" in text
    assert "home-tech:" in text
    assert "filename: dashboards/home-tech.yaml" in text
    assert "require_admin: true" in text


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
    text = (DASHBOARDS / "home-anna.yaml").read_text(encoding="utf-8")
    lampor_idx = text.index("LAMPOR TÄNDA")
    rooms_idx = text.index("VIEW 2 — KAMEROR")
    section = text[lampor_idx:rooms_idx]
    assert "custom:mushroom-light-card" in section
    assert "type: entities" not in section
    assert "entity-filter" not in section


def test_sidebar_script_keeps_tech_panel():
    text = (REPO / "scripts/configure_ha_sidebar.py").read_text(encoding="utf-8")
    assert 'TECH_PANEL = "home-tech"' in text
    assert "home-tech" in text
