"""
narrative_generator.py — Template-based narrative generation for HermesDM.

Divides labor: Python (this module) handles template-based narrative generation.
The LLM layer takes these templates and applies the final creative polish.

Scene types: EXPLORATION, COMBAT, DIALOGUE, STORY_BEAT, REST
Format: 2-4 sentences, ends with an open SITUATION (never a question).
"""
from __future__ import annotations

import random
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from state.state_manager import GameState


class SceneType(str, Enum):
    """Supported scene types for narrative generation."""
    EXPLORATION = "EXPLORATION"
    COMBAT = "COMBAT"
    DIALOGUE = "DIALOGUE"
    STORY_BEAT = "STORY_BEAT"
    REST = "REST"


# ---------------------------------------------------------------------------
# Narrative Templates
# ---------------------------------------------------------------------------

_NARRATIVE_TEMPLATES: dict[SceneType, list[str]] = {
    SceneType.EXPLORATION: [
        "The {location} stretches before you, {sensory_detail}. "
        "{character_present} {action_description}. "
        "The path forward is {obstacle}",

        "You find yourself in {location}, where {environmental_detail}. "
        "{npc_or_character_present} {reaction_description}. "
        "{ambient_threat} as you consider your next move",

        "The {location} greets you with {sensory_detail}. "
        "{character_present} {action_description}. "
        "Something about this place feels {emotional_tone}",
    ],
    SceneType.COMBAT: [
        "{attacker} lunges toward {defender}, {attack_description}. "
        "The {impact_type} echoes through the {environment}. "
        "{defender_status}",

        "Chaos erupts as {attacker} {attack_description} against {defender}. "
        "{bystanders_react}. "
        "{tactical_situation}",

        "{attacker} strikes with {attack_descriptor}, {attack_description}. "
        "The {environment} provides {environmental_factor}. "
        "{defender_status}",
    ],
    SceneType.DIALOGUE: [
        "{speaker} turns to face you, {speech_trait}. "
        "\"{dialogue_excerpt}\", they say, {gesture}. "
        "The air between you feels {emotional_tone}",

        "{speaker} meets your gaze, {character_mood}. "
        "\"{first_words}\" {speech_descriptor}. "
        "{listener_reaction}",

        "You find {speaker} {location_context}. "
        "\"{opening_line}\" {speaker_action}. "
        "{tension_point}",
    ],
    SceneType.STORY_BEAT: [
        "The truth unfolds before you: {revelation}. "
        "{affected_party} {reaction_to_truth}. "
        "Nothing will be the same after this",

        "Word reaches you of {event_summary}. "
        "{stake_holder} {emotional_response}. "
        "The pieces are in motion now",

        "A turning point arrives as {incident_description}. "
        "{witness_or_participant} {response_to_incident}. "
        "{consequence_looming}",
    ],
    SceneType.REST: [
        "The relative quiet of {location} offers a moment to breathe. "
        "{healing_atmosphere}. "
        "{resources_available} for those who seek them",

        "You take shelter in {location}, where {rest_comforts}. "
        "{party_status} as fatigue settles in. "
        "Dawn will bring new challenges",

        "The {location} provides respite from your journey. "
        "{ambient_details}. "
        "{opportunity_available}",
    ],
}

# ---------------------------------------------------------------------------
# Combat Result Narratives
# ---------------------------------------------------------------------------

_HIT_NARRATIVES = [
    "The blow lands clean, {damage_descriptor}!",
    "{attacker} strikes true, {damage_description}!",
    "A solid hit — {damage_detail}!",
]

_MISS_NARRATIVES = [
    "{attacker} swings wide, the attack missing by a breath.",
    "The strike glances off harmlessly.",
    "{attacker} overextends, leaving the attack incomplete.",
]

_KILL_NARRATIVES = [
    "{defender} crumples to the ground, {death_descriptor}.",
    "{defender} falls, {final_words}. Silence follows.",
    "{defender} is slain. {bystander_reaction}",
]

_NAT_20_NARRATIVES = [
    "A critical hit! The attack strikes with devastating precision!",
    "Natural 20! {attacker} delivers a devastating blow!",
    "Critical success — the attack lands with terrible force!",
]

# ---------------------------------------------------------------------------
# Skill Check Narratives
# ---------------------------------------------------------------------------

_SKILL_SUCCESS = [
    "{character} {skill_action} with practiced ease.",
    "Success! {character} {skill_result_description}.",
    "{character}'s expertise shows as they {skill_result_description}.",
]

_SKILL_FAILURE = [
    "{character} attempts to {skill_attempt}, but {failure_reason}.",
    "The check fails — {failure_detail}.",
    "{character} struggles, but {failure_reason}.",
]

# ---------------------------------------------------------------------------
# Dialogue Placeholder Templates
# ---------------------------------------------------------------------------

_DIALOGUE_RESPONSES = [
    "I have nothing more to say on this matter.",
    "You think I will bend to your will? Think again.",
    "The road ahead is long, and many have walked it before.",
]


# ---------------------------------------------------------------------------
# Main Generator
# ---------------------------------------------------------------------------

class NarrativeGenerator:
    """
    Template-based narrative generator for HermesDM.

    Reads system_prompt.md content and injects current game state to produce
    narrative descriptions. Does NOT make LLM calls — purely template-based.

    Usage:
        ng = NarrativeGenerator()
        result = ng.generate_scene(state, SceneType.EXPLORATION, context={"location": "Dark Forest"})
    """

    SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.md"

    def __init__(self) -> None:
        self._system_prompt: str | None = None
        self._load_system_prompt()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def generate_scene(
        self,
        state: GameState,
        scene_type: SceneType,
        context: dict | None = None,
    ) -> dict:
        """
        Generate a narrative scene based on current state and scene type.

        Args:
            state: Full campaign state dict from state_manager
            scene_type: One of SceneType enum values
            context: Optional overrides for template variables

        Returns:
            dict with keys:
                - narrative (str): 2-4 sentence narrative ending in situation
                - triggered_image (bool): Whether an image should be generated
                - image_prompt (str | None): Prompt for image generator
        """
        context = context or {}

        # Merge state-derived context
        full_context = self._build_context(state, context)

        # Select and format template
        template = self._select_template(scene_type)
        narrative = self._fill_template(template, full_context)

        # Determine if image should trigger
        triggered_image = self._should_trigger_image(scene_type, full_context)
        image_prompt = None

        return {
            "narrative": narrative,
            "triggered_image": triggered_image,
            "image_prompt": image_prompt,
        }

    def describe_combat_result(
        self,
        attack_result: dict,
        attacker_name: str,
        defender_name: str,
    ) -> str:
        """
        Narrate a combat attack result.

        Args:
            attack_result: Dict with keys {hit: bool, damage: int, nat_20: bool,
                         nat_1: bool, kill: bool, description: str}
            attacker_name: Name of the attacking character
            defender_name: Name of the defending character

        Returns:
            Narrative string describing the result
        """
        templates: list[str]

        if attack_result.get("nat_20"):
            templates = _NAT_20_NARRATIVES
            base = self._pick_template(templates)
            base = base.replace("{attacker}", attacker_name)
            return base

        if attack_result.get("kill"):
            templates = _KILL_NARRATIVES
            base = self._pick_template(templates)
            base = base.replace("{defender}", defender_name)
            if "{bystander_reaction}" in base:
                base = base.replace("{bystander_reaction}", "The ground grows still.")
            if "{death_descriptor}" in base:
                base = base.replace("{death_descriptor}", "life draining away")
            if "{final_words}" in base:
                base = base.replace("{final_words}", "no words remain")
            return base

        if attack_result.get("nat_1"):
            templates = _MISS_NARRATIVES
            base = self._pick_template(templates)
            base = base.replace("{attacker}", attacker_name)
            return base

        if attack_result.get("hit"):
            templates = _HIT_NARRATIVES
            base = self._pick_template(templates)
            base = base.replace("{attacker}", attacker_name)
            base = base.replace("{damage_descriptor}", f"{attack_result.get('damage', 0)} damage dealt")
            base = base.replace("{damage_description}", f"dealing {attack_result.get('damage', 0)} damage")
            base = base.replace("{damage_detail}", f"{attack_result.get('damage', 0)} points of damage")
            return base
        else:
            templates = _MISS_NARRATIVES
            base = self._pick_template(templates)
            base = base.replace("{attacker}", attacker_name)
            return base

    def describe_skill_result(
        self,
        skill_result: dict,
        character_name: str,
        skill_name: str,
    ) -> str:
        """
        Narrate a skill check result.

        Args:
            skill_result: Dict with keys {success: bool, modifier: int,
                         roll: int, dc: int, note: str}
            character_name: Name of the character making the check
            skill_name: Name of the skill being used

        Returns:
            Narrative string describing the result
        """
        if skill_result.get("success"):
            templates = _SKILL_SUCCESS
            base = self._pick_template(templates)
            base = base.replace("{character}", character_name)
            base = base.replace("{skill_action}", f"succeeds on the {skill_name} check")
            base = base.replace(
                "{skill_result_description}",
                f"succeeds at {skill_name} (rolled {skill_result.get('roll', 0)} vs DC {skill_result.get('dc', 0)})"
            )
            return base
        else:
            templates = _SKILL_FAILURE
            base = self._pick_template(templates)
            base = base.replace("{character}", character_name)
            base = base.replace("{skill_attempt}", f"{skill_name} check")
            base = base.replace(
                "{failure_reason}",
                f"rolled {skill_result.get('roll', 0)} against DC {skill_result.get('dc', 0)}"
            )
            base = base.replace("{failure_detail}", f"rolled {skill_result.get('roll', 0)}, needed {skill_result.get('dc', 0)}")
            return base

    def describe_npc_dialogue(
        self,
        npc_data: dict,
        player_message: str,
    ) -> str:
        """
        Generate placeholder NPC dialogue response.

        This is a template placeholder. In production, the LLM would generate
        the actual dialogue. This method provides structural consistency.

        Args:
            npc_data: Dict with keys {name, personality, speech_pattern, ...}
            player_message: What the player said to the NPC

        Returns:
            Placeholder dialogue string
        """
        npc_name = npc_data.get("name", "The stranger")
        _npc_type = npc_data.get("type", "figure")  # reserved for personality logic

        base = self._pick_template(_DIALOGUE_RESPONSES)
        response = f'"{base}"'

        return f"{npc_name} responds: {response}"

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

    def _load_system_prompt(self) -> None:
        """Load system_prompt.md content for reference."""
        if self.SYSTEM_PROMPT_PATH.exists():
            self._system_prompt = self.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        else:
            self._system_prompt = None

    def _build_context(self, state: GameState, overrides: dict) -> dict:
        """
        Build template context from state, applying overrides.

        Extracts location, characters present, NPCs nearby, and environmental
        details from state, then applies any context overrides.
        """
        campaign = state.get("campaign", {})
        location = campaign.get("current_location", "an unknown place")
        characters = state.get("characters", {})
        npcs = state.get("npcs", {})

        # Format active characters
        char_summaries = []
        for cid, char in characters.items():
            hp = char.get("hp", 0)
            max_hp = char.get("max_hp", 0)
            name = char.get("name", cid)
            status = char.get("status", "ready")
            char_summaries.append(f"{name} (HP {hp}/{max_hp}, {status})")

        character_present = (
            ", ".join(char_summaries)
            if char_summaries
            else "The party stands ready"
        )

        # Format nearby NPCs
        npc_summaries = []
        for nid, npc in npcs.items():
            if npc.get("location") == location or not npc.get("location"):
                name = npc.get("name", nid)
                status = npc.get("status", "present")
                npc_summaries.append(f"{name} ({status})")

        npc_or_character = (
            f"{npc_summaries[0]} is here" if npc_summaries else character_present
        )

        context = {
            "location": location,
            "sensory_detail": "shadows cling to every surface",
            "environmental_detail": "cold mist rolls between ancient stones",
            "ambient_threat": "A distant growl echoes",
            "obstacle": "obscured by undergrowth and memory",
            "character_present": character_present,
            "npc_or_character_present": npc_or_character,
            "action_description": "moves cautiously through the terrain",
            "reaction_description": "watches with guarded interest",
            "emotional_tone": "charged with unspoken tension",
            "speaker": "A voice emerges",
            "listener_reaction": "You weigh their words carefully.",
            "environment": state.get("world", {}).get("current_environment", "battlefield"),
            "tactical_situation": "Positioning becomes critical.",
            "revelation": "everything you believed was built on lies",
            "affected_party": "The weight of it settles over the party",
            "healing_atmosphere": "a fire crackles nearby",
            "resources_available": "Provisions and rest",
            "party_status": "Fatigue weighs heavy",
            "ambient_details": "The night passes slowly",
            "opportunity_available": "Training or preparation is possible",
        }

        # Apply state overrides
        for key, value in overrides.items():
            if key in context or key in [
                "location", "speaker", "defender", "attacker",
                "npc_name", "damage", "dc", "roll", "skill_name"
            ]:
                context[key] = value

        return context

    def _select_template(self, scene_type: SceneType) -> str:
        """Select a random template for the given scene type."""
        templates = _NARRATIVE_TEMPLATES.get(scene_type, _NARRATIVE_TEMPLATES[SceneType.STORY_BEAT])
        return random.choice(templates)

    def _pick_template(self, templates: list[str]) -> str:
        """Pick a random template from a list."""
        return random.choice(templates)

    def _fill_template(self, template: str, context: dict) -> str:
        """
        Fill in template placeholders with context values.

        Unfilled placeholders are left intact so partial templates
        still render sensibly.
        """
        result = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result

    def _should_trigger_image(self, scene_type: SceneType, context: dict) -> bool:
        """
        Determine if this scene should trigger an image generation.

        Uses scene type and presence of combatants or story beats.
        """
        if scene_type == SceneType.COMBAT:
            return True
        if scene_type == SceneType.STORY_BEAT:
            return True
        if scene_type == SceneType.EXPLORATION:
            # Trigger on first visit to a location
            return context.get("first_visit", False)
        return False

    def get_system_prompt_excerpt(self, max_chars: int = 500) -> str:
        """
        Return a snippet of the system prompt for injection into prompts.

        Used by the LLM layer to give context about voice, style, and rules.
        """
        if not self._system_prompt:
            return ""
        return self._system_prompt[:max_chars] + "..." if len(self._system_prompt) > max_chars else self._system_prompt
