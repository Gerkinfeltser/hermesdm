"""
dm/__init__.py — HermesDM narrative system module.

Exports the three core DM modules:
    - NarrativeGenerator: Template-based scene narration
    - SceneClassifier: Image generation trigger logic
    - ImagePromptBuilder: Image prompt construction
"""
from .image_prompt_builder import ImagePrompt, ImagePromptBuilder
from .narrative_generator import NarrativeGenerator, SceneType
from .scene_classifier import GameEvent, SceneClassifier

__all__ = [
    "NarrativeGenerator",
    "SceneType",
    "SceneClassifier",
    "GameEvent",
    "ImagePromptBuilder",
    "ImagePrompt",
]
