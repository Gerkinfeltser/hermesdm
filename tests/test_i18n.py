"""Tests for bot/i18n.py — translation lookups, fallbacks, interpolation."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from bot.i18n import TRANSLATIONS, get, get_for_campaign


class TestGet:
    def test_basic_en_lookup(self):
        result = get("error_generic", language="en", e="boom")
        assert result == "Error: boom"

    def test_basic_es_lookup(self):
        result = get("error_generic", language="es", e="boom")
        assert result == "Error: boom"

    def test_fallback_to_en_when_key_missing_in_lang(self):
        result = get("no_character_found", language="es")
        assert "join" in result.lower()

    def test_fallback_to_raw_key_when_missing_everywhere(self):
        result = get("totally_fake_key_xyz_123", language="en")
        assert result == "totally_fake_key_xyz_123"

    def test_default_language_is_en(self):
        result = get("error_generic", e="test")
        assert result == "Error: test"

    def test_interpolation_with_kwargs(self):
        result = get("roll_character_died", language="en", name="Valdric", status="dead")
        assert "Valdric" in result
        assert "DIED" in result

    def test_interpolation_missing_kwarg_graceful(self):
        result = get("error_generic", language="en")
        assert "{e}" in result

    def test_language_enum_accepted(self):
        from campaign_settings import Language
        result = get("error_generic", language=Language.EN, e="ok")
        assert result == "Error: ok"

    def test_none_language_uses_default(self):
        result = get("error_generic", language=None, e="default")
        assert result == "Error: default"

    def test_unknown_language_falls_back_to_key(self):
        result = get("error_generic", language="xx", e="what")
        assert result == "Error: what"

    def test_multiline_string(self):
        result = get("cmd_start_welcome", language="en")
        assert "HermesDM" in result
        assert "/setup" in result

    def test_es_multiline_string(self):
        result = get("cmd_start_welcome", language="es")
        assert "HermesDM" in result


class TestTranslationDictIntegrity:
    def test_en_es_have_same_keys(self):
        en_keys = set(TRANSLATIONS["en"].keys())
        es_keys = set(TRANSLATIONS["es"].keys())
        missing_in_es = en_keys - es_keys
        missing_in_en = es_keys - en_keys
        assert not missing_in_es, f"Keys in EN but missing in ES: {sorted(missing_in_es)}"
        assert not missing_in_en, f"Keys in ES but missing in EN: {sorted(missing_in_en)}"

    def test_all_keys_are_lowercase_snake(self):
        for lang, pairs in TRANSLATIONS.items():
            for key in pairs:
                assert key == key.lower(), f"Key '{key}' in lang '{lang}' not lowercase"
                assert " " not in key, f"Key '{key}' in lang '{lang}' contains spaces"

    def test_no_empty_values(self):
        for lang, pairs in TRANSLATIONS.items():
            for key, val in pairs.items():
                assert val, f"Empty value for key '{key}' in lang '{lang}'"

    def test_minimum_key_count(self):
        assert len(TRANSLATIONS["en"]) >= 200
        assert len(TRANSLATIONS["es"]) >= 200


class TestGetForCampaign:
    def test_returns_default_when_no_campaign(self):
        result = get_for_campaign("nonexistent_campaign", "error_generic", e="test")
        assert "Error" in result

    def test_uses_campaign_language(self):
        with patch("bot.i18n.get") as mock_get:
            mock_get.return_value = "translated"
            with patch("state.state_manager.get_settings") as mock_settings:
                from campaign_settings import CampaignSettings, Language
                mock_settings.return_value = CampaignSettings(language=Language.ES)
                result = get_for_campaign("test123", "error_generic", e="x")
                mock_get.assert_called_once_with("error_generic", Language.ES, e="x")
                assert result == "translated"

    def test_falls_back_on_settings_exception(self):
        with patch("state.state_manager.get_settings", side_effect=Exception("db down")):
            result = get_for_campaign("broken", "error_generic", e="fallback")
            assert "Error" in result


class TestDefaultLanguageEnv:
    def test_default_lang_from_env(self):
        with patch.dict(os.environ, {"DEFAULT_LANGUAGE": "es"}):
            import importlib

            import bot.i18n as i18n_mod
            importlib.reload(i18n_mod)
            assert i18n_mod._DEFAULT_LANG.value == "es"
            result = i18n_mod.get("cmd_version_error")
            assert "versión" in result.lower()

    def test_default_lang_en_when_not_set(self):
        with patch.dict(os.environ, {}, clear=False):
            if "DEFAULT_LANGUAGE" in os.environ:
                del os.environ["DEFAULT_LANGUAGE"]
            import importlib

            import bot.i18n as i18n_mod
            importlib.reload(i18n_mod)
            assert i18n_mod._DEFAULT_LANG.value == "en"


class TestSpecificTranslations:
    @pytest.mark.parametrize("key,lang,expected_fragment", [
        ("cmd_setup_already_active", "en", "active campaign"),
        ("cmd_setup_already_active", "es", "campaña activa"),
        ("roll_tpk_message", "en", "TOTAL PARTY KILL"),
        ("roll_tpk_message", "es", "TOTAL PARTY KILL"),
        ("cmd_end_closed_successfully", "en", "closed successfully"),
        ("cmd_end_closed_successfully", "es", "cerrada exitosamente"),
        ("cmd_imagen_disabled", "en", "disabled"),
        ("cmd_imagen_disabled", "es", "desactivada"),
        ("settings_language_invalid", "en", "es, pt, en"),
        ("settings_language_invalid", "es", "es, pt, en"),
    ])
    def test_key_contains_expected_text(self, key, lang, expected_fragment):
        result = get(key, language=lang)
        assert expected_fragment in result, f"Expected '{expected_fragment}' in '{result}'"

    def test_combat_turn_countdown_interpolation(self):
        result = get("combat_turn_countdown", language="en",
                     character="Valdric", round=3, bar="████░░", seconds=45)
        assert "Valdric" in result
        assert "3" in result
        assert "45" in result

    def test_give_success_interpolation(self):
        result = get("cmd_give_success", language="en",
                     giver="Alice", item="Sword", receiver="Bob",
                     used_g=5, max_g=10, used_r=3, max_r=10)
        assert "Alice" in result
        assert "Sword" in result
        assert "Bob" in result
        assert "5" in result

    def test_shortrest_result_interpolation(self):
        result = get("cmd_shortrest_result", language="en",
                     name="Valdric", hp_rec=5, hp_now=15, hp_max=20,
                     hd_left=2, warlock_note="")
        assert "Valdric" in result
        assert "+5" in result
        assert "15/20" in result

    def test_longrest_result_interpolation(self):
        result = get("cmd_longrest_result", language="en",
                     name="Valdric", old_hp=5, hp_now=20, hp_max=20, hd_rec=3)
        assert "Valdric" in result
        assert "5" in result
        assert "20/20" in result

    def test_settings_summary_interpolation(self):
        result = get("settings_summary_images", language="en", status="✅ Enabled")
        assert "✅ Enabled" in result
