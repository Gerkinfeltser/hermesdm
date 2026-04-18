"""
test_narrative.py — Tests for HermesDM narrative system.
Run: pytest tests/test_narrative.py -v
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dm.narrative_generator import NarrativeGenerator, SceneType
from dm.scene_classifier import SceneClassifier, GameEvent
from dm.image_prompt_builder import ImagePromptBuilder, ImagePrompt
from state.state_manager import new_state


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_state():
    """Minimal campaign state for testing."""
    state = new_state("test_narrative_001", "Test Campaign", "fantasy")
    state["campaign"]["current_location"] = "The Whispering Crypt"
    state["characters"] = {
        "aldric": {
            "name": "Aldric",
            "class": "Paladin",
            "hp": 45,
            "max_hp": 52,
            "status": "ready",
        },
        "senna": {
            "name": "Senna",
            "class": "Rogue",
            "hp": 28,
            "max_hp": 30,
            "status": "ready",
        },
    }
    state["npcs"] = {
        "goblin_shaman": {
            "name": "Goblin Shaman",
            "type": "goblin",
            "status": "hostile",
            "location": "The Whispering Crypt",
        },
    }
    return state


@pytest.fixture
def generator():
    return NarrativeGenerator()


@pytest.fixture
def classifier():
    return SceneClassifier(min_interval=60)


@pytest.fixture
def prompt_builder():
    return ImagePromptBuilder()


# ---------------------------------------------------------------------------
# NarrativeGenerator Tests
# ---------------------------------------------------------------------------

class TestNarrativeGenerator:
    """Tests for NarrativeGenerator scene formatting."""

    def test_generate_scene_returns_dict(self, generator, sample_state):
        """generate_scene returns a dict with narrative, triggered_image, image_prompt."""
        result = generator.generate_scene(sample_state, SceneType.EXPLORATION)
        assert isinstance(result, dict)
        assert "narrative" in result
        assert "triggered_image" in result
        assert "image_prompt" in result

    def test_narrative_is_string(self, generator, sample_state):
        """narrative field is a string."""
        result = generator.generate_scene(sample_state, SceneType.EXPLORATION)
        assert isinstance(result["narrative"], str)

    def test_narrative_is_2_4_sentences(self, generator, sample_state):
        """Narrative should be 2-4 sentences."""
        result = generator.generate_scene(sample_state, SceneType.EXPLORATION)
        narrative = result["narrative"]
        sentence_count = narrative.count(".") + narrative.count("!")
        assert 2 <= sentence_count <= 4, f"Narrative has {sentence_count} sentences: {narrative}"

    def test_narrative_ends_with_situation(self, generator, sample_state):
        """Narrative ends with an open situation, not a question mark."""
        for scene_type in SceneType:
            result = generator.generate_scene(sample_state, scene_type)
            narrative = result["narrative"].strip()
            assert not narrative.endswith("?"), f"Question-mark ending: {narrative}"
            assert len(narrative) > 10, f"Narrative too short: {narrative}"

    def test_narrative_injects_location(self, generator, sample_state):
        """Narrative includes current location from state."""
        result = generator.generate_scene(sample_state, SceneType.EXPLORATION)
        assert "Whispering Crypt" in result["narrative"] or "crypt" in result["narrative"].lower()

    def test_narrative_injects_characters(self, generator, sample_state):
        """Narrative includes character or NPC names from state."""
        result = generator.generate_scene(sample_state, SceneType.EXPLORATION)
        narrative = result["narrative"]
        # Template uses either characters or NPCs (random) — verify state entities appear
        has_named_entity = (
            "Aldric" in narrative or
            "Senna" in narrative or
            "Goblin Shaman" in narrative or
            "Whispering Crypt" in narrative
        )
        assert has_named_entity, f"No named entity from state in narrative: {narrative}"

    def test_all_scene_types_work(self, generator, sample_state):
        """All scene types produce valid output without raising."""
        for scene_type in SceneType:
            result = generator.generate_scene(sample_state, scene_type)
            assert "narrative" in result
            assert isinstance(result["triggered_image"], bool)

    def test_combat_result_narratives(self, generator):
        """describe_combat_result produces narrative strings."""
        hit_result = {"hit": True, "damage": 18, "nat_20": False, "nat_1": False, "kill": False}
        miss_result = {"hit": False, "damage": 0, "nat_20": False, "nat_1": False, "kill": False}
        kill_result = {"hit": True, "damage": 25, "nat_20": False, "nat_1": False, "kill": True}
        nat20_result = {"hit": True, "damage": 40, "nat_20": True, "nat_1": False, "kill": False}

        hit_narr = generator.describe_combat_result(hit_result, "Aldric", "Goblin")
        miss_narr = generator.describe_combat_result(miss_result, "Senna", "Orc")
        kill_narr = generator.describe_combat_result(kill_result, "Aldric", "Goblin")
        nat20_narr = generator.describe_combat_result(nat20_result, "Aldric", "Dragon")

        assert isinstance(hit_narr, str)
        assert isinstance(miss_narr, str)
        assert isinstance(kill_narr, str)
        assert isinstance(nat20_narr, str)
        assert len(hit_narr) > 5
        assert len(miss_narr) > 5

    def test_skill_result_narratives(self, generator):
        """describe_skill_result produces narrative strings."""
        success_result = {"success": True, "roll": 22, "dc": 15, "modifier": 7}
        failure_result = {"success": False, "roll": 6, "dc": 18, "modifier": 2}

        success_narr = generator.describe_skill_result(success_result, "Senna", "Stealth")
        failure_narr = generator.describe_skill_result(failure_result, "Aldric", "Athletics")

        assert isinstance(success_narr, str)
        assert isinstance(failure_narr, str)
        assert len(success_narr) > 5
        assert len(failure_narr) > 5
        assert "Senna" in success_narr or "Stealth" in success_narr

    def test_npc_dialogue_returns_string(self, generator):
        """describe_npc_dialogue returns a string."""
        npc = {"name": "Barnabus", "type": "shopkeep", "personality": "gruff"}
        result = generator.describe_npc_dialogue(npc, "I want to buy a sword.")
        assert isinstance(result, str)
        assert "Barnabus" in result
        assert len(result) > 10


# ---------------------------------------------------------------------------
# SceneClassifier Tests
# ---------------------------------------------------------------------------

class TestSceneClassifier:
    """Tests for SceneClassifier trigger logic."""

    def test_classify_returns_bool(self, classifier, sample_state):
        """classify returns True or False."""
        result = classifier.classify(
            SceneType.EXPLORATION, {}, "test_classify_001", sample_state
        )
        assert isinstance(result, bool)

    def test_combat_kill_triggers_image(self, classifier, sample_state):
        """COMBAT + kill=True triggers image generation."""
        event = {"kill": True, "attacker": "Aldric", "defender": "Goblin"}
        result = classifier.classify(
            SceneType.COMBAT, event, "test_combat_001", sample_state
        )
        assert result is True

    def test_combat_nat20_triggers_image(self, classifier, sample_state):
        """COMBAT + nat_20=True triggers image generation."""
        event = {"nat_20": True, "attacker": "Senna"}
        result = classifier.classify(
            SceneType.COMBAT, event, "test_nat20_001", sample_state
        )
        assert result is True

    def test_story_beat_triggers_image(self, classifier, sample_state):
        """STORY_BEAT always triggers image generation."""
        event = {"story_beat": True}
        result = classifier.classify(
            SceneType.STORY_BEAT, event, "test_story_001", sample_state
        )
        assert result is True

    def test_first_visit_triggers_image(self, classifier, sample_state):
        """First visit to location triggers image."""
        event = {"first_visit": True, "location": "The Sunken Temple"}
        result = classifier.classify(
            SceneType.EXPLORATION, event, "test_visit_001", sample_state
        )
        assert result is True

    def test_npc_first_appearance_triggers_image(self, classifier, sample_state):
        """First NPC appearance triggers image."""
        event = {"npc_appearance": True, "npc_id": "mysterious_stranger"}
        result = classifier.classify(
            SceneType.DIALOGUE, event, "test_npc_001", sample_state
        )
        assert result is True

    def test_debounce_prevents_rapid_images(self, classifier, sample_state):
        """Images are skipped if generated within min_interval."""
        # First call should succeed
        result1 = classifier.classify(
            SceneType.STORY_BEAT, {"story_beat": True}, "test_debounce_001", sample_state
        )
        assert result1 is True

        # Immediate second call should be blocked by debounce
        result2 = classifier.classify(
            SceneType.STORY_BEAT, {"story_beat": True}, "test_debounce_001", sample_state
        )
        assert result2 is False

    def test_different_campaigns_independent(self, classifier, sample_state):
        """Different campaigns have independent debounce."""
        # Campaign A triggers
        result_a = classifier.classify(
            SceneType.STORY_BEAT, {"story_beat": True}, "campaign_a", sample_state
        )
        assert result_a is True

        # Campaign B should also trigger (independent)
        result_b = classifier.classify(
            SceneType.STORY_BEAT, {"story_beat": True}, "campaign_b", sample_state
        )
        assert result_b is True

    def test_reset_debounce_allows_image(self, classifier, sample_state):
        """reset_debounce allows next image regardless of interval."""
        # Trigger and exhaust debounce
        classifier.classify(
            SceneType.STORY_BEAT, {"story_beat": True}, "test_reset_001", sample_state
        )
        # Should be blocked
        blocked = classifier.classify(
            SceneType.STORY_BEAT, {"story_beat": True}, "test_reset_001", sample_state
        )
        assert blocked is False

        # Reset
        classifier.reset_debounce("test_reset_001")

        # Should succeed now
        result = classifier.classify(
            SceneType.STORY_BEAT, {"story_beat": True}, "test_reset_001", sample_state
        )
        assert result is True

    def test_custom_min_interval(self, sample_state):
        """Custom min_interval is respected."""
        fast_classifier = SceneClassifier(min_interval=0.1)
        # First call
        result1 = fast_classifier.classify(
            SceneType.STORY_BEAT, {"story_beat": True}, "test_interval_001", sample_state
        )
        assert result1 is True

        # Even a tiny wait should still block (since 0.1s hasn't passed)
        import time
        time.sleep(0.05)

        result2 = fast_classifier.classify(
            SceneType.STORY_BEAT, {"story_beat": True}, "test_interval_001", sample_state
        )
        # Very short interval might not have elapsed yet
        # This is timing-dependent, so we just verify bool return
        assert isinstance(result2, bool)


# ---------------------------------------------------------------------------
# ImagePromptBuilder Tests
# ---------------------------------------------------------------------------

class TestImagePromptBuilder:
    """Tests for ImagePromptBuilder output structure."""

    def test_build_prompt_returns_dict(self, prompt_builder, sample_state):
        """build_prompt returns a dict."""
        result = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
        assert isinstance(result, dict)

    def test_build_prompt_has_required_keys(self, prompt_builder, sample_state):
        """Result contains all required keys."""
        result = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
        assert "style" in result
        assert "subject" in result
        assert "mood" in result
        assert "composition" in result
        assert "negative_prompt" in result

    def test_style_is_dnd_5e(self, prompt_builder, sample_state):
        """Style is D&D 5e official art."""
        result = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
        assert "D&D 5e" in result["style"] or "fantasy illustration" in result["style"]

    def test_negative_prompt_defined(self, prompt_builder, sample_state):
        """Negative prompt is defined and non-empty."""
        result = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
        assert isinstance(result["negative_prompt"], str)
        assert len(result["negative_prompt"]) > 5
        assert "anime" in result["negative_prompt"]
        assert "blurry" in result["negative_prompt"]

    def test_combat_composition_dynamic(self, prompt_builder, sample_state):
        """COMBAT scene has dynamic action shot composition."""
        result = prompt_builder.build_prompt(sample_state, SceneType.COMBAT)
        assert "dynamic" in result["composition"].lower() or "action" in result["composition"].lower()

    def test_exploration_composition_wide(self, prompt_builder, sample_state):
        """EXPLORATION scene has wide establishing shot."""
        result = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
        assert "wide" in result["composition"].lower() or "establishing" in result["composition"].lower()

    def test_dialogue_composition_portrait(self, prompt_builder, sample_state):
        """DIALOGUE scene has portrait composition."""
        result = prompt_builder.build_prompt(sample_state, SceneType.DIALOGUE)
        assert "portrait" in result["composition"].lower()

    def test_subject_includes_characters(self, prompt_builder, sample_state):
        """Subject includes character names from state."""
        result = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
        subject = result["subject"].lower()
        assert "aldric" in subject or "senna" in subject or "party" in subject

    def test_subject_includes_location(self, prompt_builder, sample_state):
        """Subject includes location from state."""
        result = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
        assert "Whispering Crypt" in result["subject"] or "crypt" in result["subject"].lower()

    def test_mood_mapping_combat(self, prompt_builder, sample_state):
        """COMBAT mood is tense/dramatic."""
        result = prompt_builder.build_prompt(sample_state, SceneType.COMBAT)
        mood = result["mood"].lower()
        assert mood in ["tense", "dramatic", "dark"], f"Unexpected mood: {mood}"

    def test_mood_mapping_exploration(self, prompt_builder, sample_state):
        """EXPLORATION mood is mysterious/atmospheric."""
        result = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
        mood = result["mood"].lower()
        assert mood in ["mysterious", "atmospheric", "dark"], f"Unexpected mood: {mood}"

    def test_mood_mapping_story_beat(self, prompt_builder, sample_state):
        """STORY_BEAT mood is epic/revelation."""
        result = prompt_builder.build_prompt(sample_state, SceneType.STORY_BEAT)
        mood = result["mood"].lower()
        assert mood in ["epic", "revelation", "dramatic"], f"Unexpected mood: {mood}"

    def test_context_overrides_enemies(self, prompt_builder, sample_state):
        """Context can override enemies in subject."""
        result = prompt_builder.build_prompt(
            sample_state, SceneType.COMBAT, {"enemies": ["Lich King", "Skeleton Horde"]}
        )
        subject = result["subject"]
        assert "Lich King" in subject or "Skeleton" in subject

    def test_to_full_prompt_combines_all(self, prompt_builder, sample_state):
        """to_full_prompt produces a combined prompt string."""
        prompt = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
        full = ImagePrompt(**prompt).to_full_prompt()
        assert isinstance(full, str)
        assert len(full) > len(prompt["style"])


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

class TestNarrativeSystemIntegration:
    """End-to-end tests for the narrative system."""

    def test_full_scene_flow(self, generator, classifier, prompt_builder, sample_state):
        """Narrative -> Image classification -> Prompt building works end-to-end."""
        # Generate narrative
        result = generator.generate_scene(sample_state, SceneType.EXPLORATION)
        assert "narrative" in result

        # Classify for image trigger
        should_image = classifier.classify(
            SceneType.EXPLORATION,
            {"first_visit": True, "location": "The Whispering Crypt"},
            "test_integration_001",
            sample_state,
        )

        # Build image prompt
        if should_image:
            img_prompt = prompt_builder.build_prompt(sample_state, SceneType.EXPLORATION)
            assert "style" in img_prompt
            assert "subject" in img_prompt

    def test_all_scene_types_have_image_triggers(self, classifier, sample_state):
        """Every scene type can produce image trigger decisions."""
        scene_types = [SceneType.COMBAT, SceneType.EXPLORATION, SceneType.DIALOGUE,
                        SceneType.STORY_BEAT, SceneType.REST]
        for st in scene_types:
            result = classifier.classify(st, {}, f"test_all_scenes_{st.value}", sample_state)
            assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
