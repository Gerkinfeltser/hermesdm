"""
scene_classifier.py — Image generation trigger logic for HermesDM.

Decides when to trigger image generation based on scene type, game events,
and a per-campaign debounce timer.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum

from .narrative_generator import SceneType


class GameEvent(str, Enum):
    """Event types that can trigger image generation."""
    KILL = "kill"
    NAT_20 = "nat_20"
    NAT_1 = "nat_1"
    FIRST_VISIT = "first_visit"
    NPC_APPEARANCE = "npc_appearance"
    STORY_BEAT = "story_beat"
    REST_COMPLETE = "rest_complete"


@dataclass
class CampaignImageState:
    """Tracks image generation state per campaign."""
    last_image_time: float = 0.0
    visited_locations: set[str] = field(default_factory=set)
    seen_npcs: set[str] = field(default_factory=set)


class SceneClassifier:
    """
    Determines whether a scene should trigger image generation.

    Trigger conditions:
      - COMBAT + KILL or NAT_20
      - STORY_BEAT
      - First visit to a location
      - First appearance of an NPC

    Debounce:
      - Per-campaign minimum interval between images (default 60s)
      - Configurable via __init__(min_interval=60)

    Usage:
        classifier = SceneClassifier(min_interval=60)
        should_generate = classifier.classify(
            scene_type=SceneType.COMBAT,
            game_event={"kill": True, "attacker": "Aldric", "defender": "Goblin"},
            campaign_id="my-campaign",
            state=current_state,
        )
    """

    def __init__(self, min_interval: float = 60.0) -> None:
        """
        Initialize the classifier.

        Args:
            min_interval: Minimum seconds between image generations per campaign.
                         Defaults to 60 seconds.
        """
        self.min_interval = min_interval
        self._campaign_states: dict[str, CampaignImageState] = {}

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def classify(
        self,
        scene_type: SceneType,
        game_event: dict,
        campaign_id: str,
        state: dict | None = None,
    ) -> bool:
        """
        Determine if an image should be generated for this scene.

        Args:
            scene_type: The type of scene being generated
            game_event: Dict describing the game event (kill, nat_20, etc.)
            campaign_id: Campaign identifier for debounce tracking
            state: Optional full campaign state for context

        Returns:
            True if image generation should be triggered, False otherwise
        """
        campaign_state = self._get_campaign_state(campaign_id)

        # Check debounce first
        if not self._check_debounce(campaign_state):
            return False

        # Check trigger conditions
        triggered = self._evaluate_triggers(scene_type, game_event, campaign_state, state)

        if triggered:
            campaign_state.last_image_time = time.time()

        return triggered

    def reset_debounce(self, campaign_id: str) -> None:
        """
        Manually reset the debounce timer for a campaign.

        Useful when a major story beat occurs and you want to force
        an image regardless of the minimum interval.
        """
        if campaign_id in self._campaign_states:
            self._campaign_states[campaign_id].last_image_time = 0.0

    def mark_location_visited(self, campaign_id: str, location: str) -> None:
        """Record that the party has visited a location."""
        self._get_campaign_state(campaign_id).visited_locations.add(location)

    def mark_npc_seen(self, campaign_id: str, npc_id: str) -> None:
        """Record that the party has encountered an NPC."""
        self._get_campaign_state(campaign_id).seen_npcs.add(npc_id)

    def get_time_since_last_image(self, campaign_id: str) -> float:
        """
        Get seconds elapsed since last image generation.

        Returns 0.0 if no image has been generated yet.
        """
        campaign_state = self._campaign_states.get(campaign_id)
        if not campaign_state:
            return 0.0
        return time.time() - campaign_state.last_image_time

    def clear_campaign_state(self, campaign_id: str) -> None:
        """Remove all tracking state for a campaign."""
        self._campaign_states.pop(campaign_id, None)

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

    def _get_campaign_state(self, campaign_id: str) -> CampaignImageState:
        """Get or create campaign state tracker."""
        if campaign_id not in self._campaign_states:
            self._campaign_states[campaign_id] = CampaignImageState()
        return self._campaign_states[campaign_id]

    def _check_debounce(self, campaign_state: CampaignImageState) -> bool:
        """Check if minimum interval has elapsed since last image."""
        if campaign_state.last_image_time == 0.0:
            return True  # First image always allowed
        elapsed = time.time() - campaign_state.last_image_time
        return elapsed >= self.min_interval

    def _evaluate_triggers(
        self,
        scene_type: SceneType,
        game_event: dict,
        campaign_state: CampaignImageState,
        state: dict | None,
    ) -> bool:
        """
        Evaluate whether any trigger condition is met.

        Returns True if at least one trigger condition fires.
        """
        # Combat + kill or nat_20
        if scene_type == SceneType.COMBAT:
            if game_event.get("kill"):
                return True
            if game_event.get("nat_20"):
                return True

        # Story beat always triggers
        if scene_type == SceneType.STORY_BEAT:
            return True

        # First visit to location
        if scene_type == SceneType.EXPLORATION:
            location = game_event.get("location", "")
            if location and location not in campaign_state.visited_locations:
                return True

        # First NPC appearance
        if game_event.get("npc_appearance"):
            npc_id = game_event.get("npc_id", "")
            if npc_id and npc_id not in campaign_state.seen_npcs:
                return True

        # Rest complete (important moments only)
        if scene_type == SceneType.REST:
            if game_event.get("major_rest", False):
                return True

        return False

    def get_trigger_description(
        self,
        scene_type: SceneType,
        game_event: dict,
    ) -> str:
        """
        Human-readable description of why a trigger fired (or didn't).

        Useful for debugging and logging.
        """
        reasons = []

        if scene_type == SceneType.COMBAT:
            if game_event.get("kill"):
                reasons.append("COMBAT+KILL")
            if game_event.get("nat_20"):
                reasons.append("COMBAT+NAT_20")

        if scene_type == SceneType.STORY_BEAT:
            reasons.append("STORY_BEAT")

        if game_event.get("first_visit"):
            reasons.append(f"FIRST_VISIT:{game_event.get('location', 'unknown')}")

        if game_event.get("npc_appearance"):
            reasons.append(f"NPC_APPEARANCE:{game_event.get('npc_id', 'unknown')}")

        if game_event.get("major_rest"):
            reasons.append("MAJOR_REST")

        return ", ".join(reasons) if reasons else "NO_TRIGGER"
