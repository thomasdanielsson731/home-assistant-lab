"""Tests for smoke zone mapping."""

from smoke_zones import PLANNED_ROOM_ASSIGNMENTS, SMOKE_ROOMS, zone_for_area


def test_smoke_rooms():
    assert SMOKE_ROOMS == ("kok", "vardagsrum", "hall")


def test_planned_assignments_match_rooms():
    assert len(PLANNED_ROOM_ASSIGNMENTS) == 3
    assert [z for z, _ in PLANNED_ROOM_ASSIGNMENTS] == list(SMOKE_ROOMS)


def test_zone_for_ha_areas():
    assert zone_for_area("kok") == "kok"
    assert zone_for_area("living_room") == "vardagsrum"
    assert zone_for_area("hall_ground_floor") == "hall"
    assert zone_for_area("hall_nere") == "hall"
    assert zone_for_area(None) == "room"
