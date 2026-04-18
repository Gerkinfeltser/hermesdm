"""
Tests for scene_classifier.py — when to generate images.
"""
import pytest
from unittest.mock import MagicMock
from dm.scene_classifier import SceneClassifier, SceneType, GameEvent


class TestSceneClassifier:
    def setup_method(self):
        self.sc = SceneClassifier(min_interval=0)  # No debounce for tests

    def test_explore_no_image(self):
        should = self.sc.classify(SceneType.EXPLORATION, {}, "c1", MagicMock())
        assert should is False

    def test_combat_no_kill_no_crit(self):
        event = {"kill": False, "nat_20": False}
        should = self.sc.classify(SceneType.COMBAT, event, "c1", MagicMock())
        assert should is False

    def test_combat_kill_generates_image(self):
        event = {"kill": True, "nat_20": False}
        should = self.sc.classify(SceneType.COMBAT, event, "c1", MagicMock())
        assert should is True

    def test_combat_nat_20_generates_image(self):
        event = {"kill": False, "nat_20": True}
        should = self.sc.classify(SceneType.COMBAT, event, "c1", MagicMock())
        assert should is True

    def test_combat_kill_and_nat_20_generates_image(self):
        event = {"kill": True, "nat_20": True}
        should = self.sc.classify(SceneType.COMBAT, event, "c1", MagicMock())
        assert should is True

    def test_story_beat_generates_image(self):
        should = self.sc.classify(SceneType.STORY_BEAT, {}, "c1", MagicMock())
        assert should is True

    def test_dialogue_no_image(self):
        should = self.sc.classify(SceneType.DIALOGUE, {}, "c1", MagicMock())
        assert should is False

    def test_rest_no_image(self):
        should = self.sc.classify(SceneType.REST, {}, "c1", MagicMock())
        assert should is False

    def test_debounce_prevents_rapid_images(self):
        sc = SceneClassifier(min_interval=60)
        event = {"kill": True}
        state = MagicMock()
        should1 = sc.classify(SceneType.COMBAT, event, "c1", state)
        assert should1 is True
        should2 = sc.classify(SceneType.COMBAT, event, "c1", state)
        assert should2 is False

    def test_debounce_per_campaign(self):
        sc = SceneClassifier(min_interval=60)
        event = {"kill": True}
        state = MagicMock()
        sc.classify(SceneType.COMBAT, event, "campaign_A", state)
        should = sc.classify(SceneType.COMBAT, event, "campaign_B", state)
        assert should is True

    def test_debounce_zero_interval_allows_repeat(self):
        sc = SceneClassifier(min_interval=0)
        event = {"kill": True}
        state = MagicMock()
        should1 = sc.classify(SceneType.COMBAT, event, "c1", state)
        should2 = sc.classify(SceneType.COMBAT, event, "c1", state)
        assert should1 is True
        assert should2 is True


class TestSceneType:
    def test_all_scene_type_members_exist(self):
        expected = ["EXPLORATION", "COMBAT", "DIALOGUE", "STORY_BEAT", "REST"]
        for st in expected:
            assert hasattr(SceneType, st)

    def test_scene_type_values_are_uppercase_strings(self):
        """SceneType values are the enum member names as strings."""
        assert SceneType.EXPLORATION.value == "EXPLORATION"
        assert SceneType.COMBAT.value == "COMBAT"
        assert SceneType.DIALOGUE.value == "DIALOGUE"
        assert SceneType.STORY_BEAT.value == "STORY_BEAT"
        assert SceneType.REST.value == "REST"
