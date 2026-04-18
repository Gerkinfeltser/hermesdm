"""
image_prompt_builder.py — Builds image generation prompts from game state.

Constructs Stable Diffusion / image generator prompts using scene type,
characters present, enemies, location, and mood mapping.

Style is fixed to D&D 5e official art aesthetic for consistency.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .narrative_generator import SceneType

import random


class Mood(str, Enum):
    """Mood descriptors for image generation."""
    TENSE = "tense"
    DRAMATIC = "dramatic"
    MYSTERIOUS = "mysterious"
    ATMOSPHERIC = "atmospheric"
    INTIMATE = "intimate"
    EPIC = "epic"
    REVELATION = "revelation"
    CALM = "calm"
    DARK = "dark"
    HOPEFUL = "hopeful"


# ---------------------------------------------------------------------------
# Style Constants
# ---------------------------------------------------------------------------

STYLE: str = (
    "D&D 5e official art, cinematic, 4k, highly detailed, fantasy illustration"
)

NEGATIVE_PROMPT: str = (
    "anime, cartoon, low quality, deformed, blurry, watermark, text, signature"
)

COMPOSITION_BY_SCENE: dict[str, str] = {
    "COMBAT": "dynamic action shot",
    "EXPLORATION": "wide establishing shot",
    "DIALOGUE": "portrait",
    "STORY_BEAT": "cinematic wide shot",
    "REST": "peaceful wide shot",
}

MOOD_BY_SCENE: dict[str, list[str]] = {
    "COMBAT": ["tense", "dramatic", "dark"],
    "EXPLORATION": ["mysterious", "atmospheric", "dark"],
    "DIALOGUE": ["intimate", "dramatic", "tense"],
    "STORY_BEAT": ["epic", "revelation", "dramatic"],
    "REST": ["calm", "hopeful", "atmospheric"],
}

# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

@dataclass
class ImagePrompt:
    """
    Structured image prompt components.

    Attributes:
        style: Fixed D&D 5e art style
        subject: Who/what is depicted
        mood: Emotional tone
        composition: Framing type
        negative_prompt: Things to avoid
    """
    style: str
    subject: str
    mood: str
    composition: str
    negative_prompt: str

    def to_dict(self) -> dict:
        """Convert to dict for downstream consumers."""
        return {
            "style": self.style,
            "subject": self.subject,
            "mood": self.mood,
            "composition": self.composition,
            "negative_prompt": self.negative_prompt,
        }

    def to_full_prompt(self) -> str:
        """
        Combine into a single image generation prompt string.

        Format: style + subject + mood + composition
        """
        parts = [
            self.style,
            self.subject,
            f"mood: {self.mood}",
            f"composition: {self.composition}",
        ]
        return ", ".join(parts)


class ImagePromptBuilder:
    """
    Builds structured image prompts from game state and scene type.

    Usage:
        builder = ImagePromptBuilder()
        prompt = builder.build_prompt(state, SceneType.COMBAT, {"enemies": ["Goblin", "Orc"]})
        # Returns dict with style, subject, mood, composition, negative_prompt
    """

    def __init__(self) -> None:
        self.style = STYLE
        self.negative_prompt = NEGATIVE_PROMPT

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def build_prompt(
        self,
        state: dict,
        scene_type: SceneType,
        context: dict | None = None,
    ) -> dict:
        """
        Build an image prompt dict from game state.

        Args:
            state: Full campaign state from state_manager
            scene_type: Type of scene (EXPLORATION, COMBAT, etc.)
            context: Optional overrides (enemies, special_details, etc.)

        Returns:
            dict with keys: style, subject, mood, composition, negative_prompt
        """
        context = context or {}

        scene_name = scene_type.value if hasattr(scene_type, "value") else str(scene_type)

        subject = self._build_subject(state, scene_type, context)
        mood = self._pick_mood(scene_name, context)
        composition = self._get_composition(scene_name)

        return {
            "style": self.style,
            "subject": subject,
            "mood": mood,
            "composition": composition,
            "negative_prompt": self.negative_prompt,
        }

    def build_prompt_from_result(
        self,
        narrative: str,
        scene_type: SceneType,
    ) -> dict:
        """
        Build an image prompt from a narrative description.

        Useful when the calling code has already generated a narrative
        and wants to extract visual elements from it.

        Args:
            narrative: The narrative text to extract visual elements from
            scene_type: Type of scene

        Returns:
            dict with standard prompt keys
        """
        scene_name = scene_type.value if hasattr(scene_type, "value") else str(scene_type)

        # Extract potential subjects from narrative
        subject = self._extract_subject_from_narrative(narrative)
        mood = self._pick_mood(scene_name, {})
        composition = self._get_composition(scene_name)

        return {
            "style": self.style,
            "subject": subject,
            "mood": mood,
            "composition": composition,
            "negative_prompt": self.negative_prompt,
        }

    # -----------------------------------------------------------------------
    # Subject Building
    # -----------------------------------------------------------------------

    def _build_subject(
        self,
        state: dict,
        scene_type: SceneType,
        context: dict,
    ) -> str:
        """
        Build the subject line of the image prompt.

        Combines characters present, enemies, location, and scene-specific details.
        """
        parts: list[str] = []

        # Characters present
        characters = self._get_characters_present(state)
        if characters:
            parts.append(f"party: {characters}")

        # Enemies
        enemies = context.get("enemies", [])
        if enemies:
            enemy_list = ", ".join(enemies) if isinstance(enemies, list) else str(enemies)
            parts.append(f"enemies: {enemy_list}")

        # Location
        location = state.get("campaign", {}).get("current_location", "")
        if location:
            parts.append(f"location: {location}")
        elif context.get("location"):
            parts.append(f"location: {context['location']}")

        # Scene-specific additions
        if scene_type.value == "COMBAT" and not enemies:
            parts.append("battle scene")

        if scene_type.value == "DIALOGUE":
            parts.append("two characters facing each other")

        if scene_type.value == "STORY_BEAT":
            parts.append("dramatic revelation moment")

        if scene_type.value == "REST":
            parts.append("peaceful camp or tavern interior")

        if scene_type.value == "EXPLORATION":
            parts.append("adventurers in mysterious environment")

        # Special details from context
        special = context.get("special_details", "")
        if special:
            parts.append(special)

        return "; ".join(parts) if parts else "fantasy scene"

    def _get_characters_present(self, state: dict) -> str:
        """Get formatted list of active characters in the scene."""
        characters = state.get("characters", {})
        if not characters:
            return "adventurers"

        names = []
        for char in characters.values():
            name = char.get("name", "Unknown")
            hp = char.get("hp", 0)
            max_hp = char.get("max_hp", 0)
            if hp and max_hp:
                names.append(f"{name} (HP {hp}/{max_hp})")
            else:
                names.append(name)

        return ", ".join(names)

    def _extract_subject_from_narrative(self, narrative: str) -> str:
        """
        Attempt to extract visual subject matter from narrative text.

        Looks for known entity patterns (character names, locations, etc.)
        """
        # Simple extraction — look for quoted speech and common patterns
        if '"' in narrative:
            # Likely dialogue scene
            return "characters engaged in conversation"

        # Fallback: use first 100 chars as descriptor
        return narrative[:150] + "..." if len(narrative) > 150 else narrative

    # -----------------------------------------------------------------------
    # Mood & Composition
    # -----------------------------------------------------------------------

    def _pick_mood(self, scene_name: str, context: dict) -> str:
        """Pick a mood descriptor based on scene type and context."""
        mood_overrides = context.get("mood")
        if mood_overrides:
            return mood_overrides

        moods = MOOD_BY_SCENE.get(scene_name, ["dramatic"])
        return random.choice(moods)

    def _get_composition(self, scene_name: str) -> str:
        """Get composition type for scene."""
        return COMPOSITION_BY_SCENE.get(scene_name, "cinematic wide shot")

    # -----------------------------------------------------------------------
    # Utility
    # -----------------------------------------------------------------------

    def get_negative_prompt(self) -> str:
        """Return the standard negative prompt."""
        return self.negative_prompt

    def preview_prompt(
        self,
        state: dict,
        scene_type: SceneType,
        context: dict | None = None,
    ) -> str:
        """
        Generate a preview of the full prompt string.

        Useful for debugging and logging.
        """
        prompt_dict = self.build_prompt(state, scene_type, context)
        return ImagePrompt(**prompt_dict).to_full_prompt()
