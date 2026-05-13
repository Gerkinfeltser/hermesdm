"""Campaign settings — configurable options per campaign."""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Language(str, Enum):
    ES = "es"
    PT = "pt"
    EN = "en"


    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class Difficulty(str, Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


# Module-level DC modifier table (outside the enum to avoid __members__ collision)
_DC_MODIFIER: dict[str, int] = {
    "easy": -2,
    "normal": 0,
    "hard": +2,
}


def Difficulty_get_dc(difficulty: Difficulty, base_dc: int) -> int:
    """Apply difficulty modifier to a base DC."""
    return base_dc + _DC_MODIFIER[difficulty.value]


class NarrativeTone(str, Enum):
    SERIOUS = "serious"
    FUNNY = "funny"
    DARK = "dark"
    EPIC = "epic"


@dataclass
class CampaignSettings:
    """
    Configurable settings for a campaign.
    Persisted inside the campaign JSON under the key 'settings'.
    """

    # === Image generation (on/off switch) ===
    # True = generar imagen de cada escena nueva via Pollinations (gratis)
    # False = no generar imágenes automáticamente
    image_generation: bool = True

    # === Combat / Gameplay ===
    difficulty: Difficulty = Difficulty.NORMAL
    turn_timer_seconds: int = 120  # 0 = no timer

    # === Narrative ===
    narrative_tone: NarrativeTone = NarrativeTone.SERIOUS
    language: Language = Language.EN

    # === Advanced ===
    # Bonus to all skill checks (for easier/harder parties)
    luck_bonus: int = 0
    # If True, DM describes dice results narratively
    dramatic_dice: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CampaignSettings":
        # Handle enum conversion from raw strings
        if "difficulty" in data and isinstance(data["difficulty"], str):
            data["difficulty"] = Difficulty(data["difficulty"])
        if "narrative_tone" in data and isinstance(data["narrative_tone"], str):
            data["narrative_tone"] = NarrativeTone(data["narrative_tone"])
        if "language" in data and isinstance(data["language"], str):
            data["language"] = Language(data["language"])
        # Handle legacy free_image_mode → image_generation migration
        if "free_image_mode" in data and "image_generation" not in data:
            data["image_generation"] = data["free_image_mode"]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def apply_update(self, key: str, value: str) -> tuple[bool, str]:
        """
        Apply a setting update from a command string.
        Returns (success, message).
        """
        from bot.i18n import get as t

        key = key.lower().strip()
        value = value.lower().strip()
        lang = self.language

        match key:
            case "imagen" | "image_gen" | "imágenes":
                if value in ("on", "true", "1", "yes", "enabled", "si"):
                    self.image_generation = True
                    return True, t("settings_image_activated", language=lang)
                elif value in ("off", "false", "0", "no", "disabled"):
                    self.image_generation = False
                    return True, t("settings_image_deactivated", language=lang)
                return False, t("settings_invalid_value", language=lang, value=value)

            case "free":
                if value in ("on", "true", "1", "yes", "ascii"):
                    self.image_generation = True
                    return True, t("settings_image_activated", language=lang)
                elif value in ("off", "false", "0", "no", "paid"):
                    self.image_generation = False
                    return True, t("settings_image_deactivated", language=lang)
                return False, t("settings_invalid_value", language=lang, value=value)

            case "dificultad" | "difficulty":
                try:
                    self.difficulty = Difficulty(value)
                    labels = {
                        "easy": t("settings_diff_easy", language=lang),
                        "normal": t("settings_diff_normal", language=lang),
                        "hard": t("settings_diff_hard", language=lang),
                    }
                    return True, t("settings_difficulty_updated", language=lang, label=labels[value])
                except ValueError:
                    return False, t("settings_difficulty_invalid", language=lang)

            case "tono" | "tone" | "narrative_tone":
                try:
                    self.narrative_tone = NarrativeTone(value)
                    labels = {
                        "serious": t("settings_tone_serious", language=lang),
                        "funny": t("settings_tone_funny", language=lang),
                        "dark": t("settings_tone_dark", language=lang),
                        "epic": t("settings_tone_epic", language=lang),
                    }
                    return True, t("settings_tone_updated", language=lang, label=labels[value])
                except ValueError:
                    return False, t("settings_tone_invalid", language=lang)

            case "timer" | "turn_timer":
                try:
                    seconds = int(value)
                    if seconds < 0:
                        return False, t("settings_timer_negative", language=lang)
                    self.turn_timer_seconds = seconds
                    if seconds == 0:
                        return True, t("settings_timer_deactivated", language=lang)
                    return True, t("settings_timer_updated", language=lang, seconds=seconds)
                except ValueError:
                    return False, t("settings_timer_invalid", language=lang, value=value)

            case "suerte" | "luck_bonus" | "luck":
                try:
                    bonus = int(value)
                    self.luck_bonus = bonus
                    if bonus >= 0:
                        return True, t("settings_luck_positive", language=lang, bonus=bonus)
                    return True, t("settings_luck_negative", language=lang, bonus=bonus)
                except ValueError:
                    return False, t("settings_luck_invalid", language=lang, value=value)

            case "dados" | "dramatic_dice":
                if value in ("on", "true", "1", "yes"):
                    self.dramatic_dice = True
                    return True, t("settings_dramatic_dice_activated", language=lang)
                elif value in ("off", "false", "0", "no"):
                    self.dramatic_dice = False
                    return True, t("settings_dramatic_dice_deactivated", language=lang)
                return False, t("settings_invalid_value", language=lang, value=value)

            case "idioma" | "language":
                try:
                    self.language = Language(value)
                    labels = {
                        "es": t("settings_lang_es", language=lang),
                        "pt": t("settings_lang_pt", language=lang),
                        "en": t("settings_lang_en", language=lang),
                    }
                    return True, t("settings_language_updated", language=lang, label=labels[value])
                except ValueError:
                    return False, t("settings_language_invalid", language=lang)

            case _:
                return False, t("settings_unknown_option", language=lang, key=key)

    def summary(self) -> str:
        """Human-readable current settings."""
        from bot.i18n import get as t

        lang = self.language
        img_on = t("settings_img_on", language=lang)
        img_off = t("settings_img_off", language=lang)
        img_status = img_on if self.image_generation else img_off
        timer_str = f"{self.turn_timer_seconds}s" if self.turn_timer_seconds else "off"
        labels_tone = {
            "serious": t("settings_tone_serious", language=lang),
            "funny": t("settings_tone_funny", language=lang),
            "dark": t("settings_tone_dark", language=lang),
            "epic": t("settings_tone_epic", language=lang),
        }
        labels_diff = {
            "easy": t("settings_diff_easy", language=lang),
            "normal": t("settings_diff_normal", language=lang),
            "hard": t("settings_diff_hard", language=lang),
        }
        labels_lang = {
            "es": t("settings_lang_es", language=lang),
            "pt": t("settings_lang_pt", language=lang),
            "en": t("settings_lang_en", language=lang),
        }
        yes = t("settings_yes", language=lang)
        no = t("settings_no", language=lang)
        return (
            t("settings_summary_header", language=lang)
            + t("settings_summary_images", language=lang, status=img_status) + "\n"
            + t("settings_summary_difficulty", language=lang, label=labels_diff[self.difficulty.value]) + "\n"
            + t("settings_summary_tone", language=lang, label=labels_tone[self.narrative_tone.value]) + "\n"
            + t("settings_summary_language", language=lang, label=labels_lang[self.language.value]) + "\n"
            + t("settings_summary_timer", language=lang, seconds=timer_str) + "\n"
            + t("settings_summary_dramatic_dice", language=lang, yes_no=(yes if self.dramatic_dice else no)) + "\n"
            + t("settings_summary_luck", language=lang, bonus=f"{'+' if self.luck_bonus >= 0 else ''}{self.luck_bonus}")
        )
