"""
Tests for world_builder.py — campaign world generation.
"""
import pytest
from dm.world_builder import (
    generate_npcs, build_world, create_campaign,
    SETTINGS, NPC_TEMPLATES
)


class TestGenerateNpcs:
    def test_generate_npcs_returns_dict(self):
        npcs = generate_npcs(count=3)
        assert isinstance(npcs, dict)
        assert len(npcs) == 3

    def test_generate_npcs_keys_are_valid_ids(self):
        npcs = generate_npcs(count=3)
        for npc_id in npcs:
            assert " " not in npc_id  # spaces replaced with underscores

    def test_generate_npcs_has_required_fields(self):
        npcs = generate_npcs(count=2)
        required = ["name", "role", "status", "location", "disposition",
                    "race", "disposition_value", "relationship_to_party",
                    "memory", "goals", "mood", "appearance", "secret"]
        for npc_id, npc in npcs.items():
            for field in required:
                assert field in npc, f"{npc_id} missing {field}"
            assert npc["status"] == "ALIVE"

    def test_generate_npcs_count_respects_max(self):
        all_npcs = generate_npcs(count=5)
        assert len(all_npcs) == 5
        few_npcs = generate_npcs(count=2)
        assert len(few_npcs) == 2


class TestBuildWorld:
    def test_build_world_fantasy(self):
        state = build_world("fantasy")
        assert state["campaign"]["setting"] == "fantasy"
        assert state["campaign"]["name"] == SETTINGS["fantasy"]["name"]
        assert state["campaign"]["current_location"] == SETTINGS["fantasy"]["starting_location"]
        assert len(state["npcs"]) == 3
        assert "world" in state
        assert "main_threat" in state["world"]
        assert len(state["history"]) == 1

    def test_build_world_scifi(self):
        state = build_world("scifi")
        assert state["campaign"]["setting"] == "scifi"
        assert state["campaign"]["name"] == SETTINGS["scifi"]["name"]

    def test_build_world_horror(self):
        state = build_world("horror")
        assert state["campaign"]["setting"] == "horror"
        assert state["campaign"]["name"] == SETTINGS["horror"]["name"]

    def test_build_world_unknown_falls_back_to_fantasy(self):
        state = build_world("unknown_setting")
        assert state["campaign"]["setting"] == "fantasy"

    def test_build_world_creates_location(self):
        state = build_world("fantasy")
        loc = state["campaign"]["current_location"]
        assert loc in state["world"]["locations"]
        assert "description" in state["world"]["locations"][loc]
        assert state["world"]["locations"][loc]["visited"] is True

    def test_build_world_npcs_linked_to_tavern(self):
        state = build_world("fantasy")
        loc = state["campaign"]["current_location"]
        tavern_npcs = state["world"]["locations"][loc].get("NPCs", [])
        assert len(tavern_npcs) >= 1


class TestCreateCampaign:
    def test_create_campaign_returns_id_and_state(self):
        result = create_campaign("fantasy")
        assert "campaign_id" in result
        assert "state" in result
        assert result["campaign_id"].startswith("campaign_")

    def test_create_campaign_saves_state(self):
        import os
        from state.state_manager import CAMPAIGNS_DIR, load_state
        result = create_campaign("fantasy")
        cid = result["campaign_id"]
        loaded = load_state(cid)
        assert loaded is not None
        assert loaded["campaign"]["id"] == cid

    def test_create_campaign_generates_uuid(self):
        r1 = create_campaign("fantasy")
        r2 = create_campaign("fantasy")
        assert r1["campaign_id"] != r2["campaign_id"]


class TestSettings:
    def test_all_settings_have_required_fields(self):
        required = ["name", "description", "starting_location",
                    "starting_location_desc", "factions", "main_threat"]
        for setting_name, setting in SETTINGS.items():
            for field in required:
                assert field in setting, f"{setting_name} missing {field}"

    def test_npc_templates_have_required_fields(self):
        required = ["name", "role", "disposition", "location",
                    "race", "secret", "goals"]
        for tmpl in NPC_TEMPLATES:
            for field in required:
                assert field in tmpl, f"{tmpl['name']} missing {field}"
