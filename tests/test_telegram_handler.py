"""
tests/test_telegram_handler.py — Mock async tests for all telegram handlers.

Run with: pytest tests/test_telegram_handler.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

from bot.telegram_handler import (
    cmd_start,
    cmd_help,
    cmd_newgame,
    cmd_join,
    cmd_roll,
    cmd_attack,
    cmd_cast,
    cmd_skill,
    cmd_status,
    cmd_hp,
    cmd_inventory,
    cmd_talk,
    cmd_map,
    cmd_quests,
    cmd_recap,
    cmd_resume,
    cmd_endturn,
    cmd_campaign,
    cmd_save,
    ChatState,
    Settings,
    build_app,
    _fmt_character,
    _fmt_dice_result,
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def mock_update():
    """Create a mock Update with common objects."""
    user = MagicMock(spec=User)
    user.first_name = "TestPlayer"
    user.id = 12345

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890

    message = AsyncMock(spec=Message)
    message.text = "/test"
    message.reply_text = AsyncMock()
    message.chat = chat
    message.from_user = user

    update = MagicMock(spec=Update)
    update.effective_user = user
    update.effective_chat = chat
    update.message = message
    return update


@pytest.fixture
def mock_context(mock_update):
    """Create a mock Context with chat_data and args."""
    ctx = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    ctx.chat_data = {"_hermes_state": ChatState()}
    ctx.args = []
    ctx.user_data = {}
    return ctx


@pytest.fixture
def chat_state(mock_context):
    return mock_context.chat_data["_hermes_state"]


# ------------------------------------------------------------------
# Helper tests (format functions)
# ------------------------------------------------------------------


class TestFmtHelpers:
    """Test the formatting helper functions."""

    def test_fmt_dice_result_basic(self):
        """Test formatting a basic dice roll result."""
        r = {
            "total": 14,
            "rolls": [14],
            "modifier": 0,
            "natural": 14,
            "is_crit": False,
            "is_fumble": False,
            "str": "d20",
        }
        result = _fmt_dice_result(r)
        assert "d20" in result
        assert "14" in result
        assert "CRITICAL" not in result
        assert "FUMBLE" not in result

    def test_fmt_dice_result_crit(self):
        """Test formatting a natural 20."""
        r = {
            "total": 20,
            "rolls": [20],
            "modifier": 0,
            "natural": 20,
            "is_crit": True,
            "is_fumble": False,
            "str": "d20",
        }
        result = _fmt_dice_result(r)
        assert "NATURAL 20" in result
        assert "CRITICAL" in result

    def test_fmt_dice_result_fumble(self):
        """Test formatting a natural 1."""
        r = {
            "total": 1,
            "rolls": [1],
            "modifier": 0,
            "natural": 1,
            "is_crit": False,
            "is_fumble": True,
            "str": "d20",
        }
        result = _fmt_dice_result(r)
        assert "NATURAL 1" in result
        assert "FUMBLE" in result

    def test_fmt_dice_result_with_modifier(self):
        """Test formatting with a modifier."""
        r = {
            "total": 17,
            "rolls": [12],
            "modifier": 5,
            "natural": 12,
            "is_crit": False,
            "is_fumble": False,
            "str": "d20+5",
        }
        result = _fmt_dice_result(r)
        assert "Modifier: +5" in result
        assert "Total: 17" in result


# ------------------------------------------------------------------
# ChatState
# ------------------------------------------------------------------


class TestChatState:
    """Test ChatState dataclass."""

    def test_chat_state_defaults(self):
        """Test default ChatState values."""
        cs = ChatState()
        assert cs.active_campaign is None
        assert cs.pending_attacks == {}
        assert cs.pending_spell is None
        assert cs.pending_skill_check is None
        assert cs.pending_save is None
        assert cs.characters == {}
        assert cs.combat_state is None

    def test_chat_state_character_for(self, chat_state):
        """Test character_for returns None when no character."""
        result = chat_state.character_for("Valdric")
        assert result is None

    def test_chat_state_active_character_names(self, chat_state):
        """Test active_character_names returns empty when no characters."""
        result = chat_state.active_character_names()
        assert result == []


# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------


class TestSettings:
    """Test pydantic Settings."""

    def test_default_token(self):
        """Test default bot token."""
        s = Settings()
        assert s.TELEGRAM_BOT_TOKEN == "8685005944:AAEmjcpY"

    def test_env_override(self):
        """Test environment variable override."""
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "test:token"}):
            s = Settings()
            assert s.TELEGRAM_BOT_TOKEN == "test:token"


# ------------------------------------------------------------------
# /start
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdStart:
    """Tests for cmd_start."""

    async def test_start_sends_welcome(self, mock_update, mock_context):
        """Test /start sends a welcome message."""
        await cmd_start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0]
        assert "HermesDM" in text
        assert "welcome" in text.lower() or "Welcome" in text

    async def test_start_no_crash_on_exception(self, mock_update, mock_context):
        """Test /start handles exceptions gracefully."""
        mock_update.message.reply_text.side_effect = Exception("Send failed")
        # Should not raise
        await cmd_start(mock_update, mock_context)


# ------------------------------------------------------------------
# /help
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdHelp:
    """Tests for cmd_help."""

    async def test_help_sends_command_list(self, mock_update, mock_context):
        """Test /help sends the command list."""
        await cmd_help(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0]
        assert "/newgame" in text
        assert "/join" in text
        assert "/roll" in text
        assert "/attack" in text

    async def test_help_handles_exception(self, mock_update, mock_context):
        """Test /help handles exceptions gracefully."""
        mock_update.message.reply_text.side_effect = Exception("Send failed")
        await cmd_help(mock_update, mock_context)  # Should not raise


# ------------------------------------------------------------------
# /newgame
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdNewgame:
    """Tests for cmd_newgame."""

    async def test_newgame_creates_campaign(self, mock_update, mock_context):
        """Test /newgame creates a campaign and updates state."""
        mock_context.args = ["fantasy"]
        with patch("bot.telegram_handler._create_campaign") as mock_create:
            mock_create.return_value = {
                "campaign_id": "campaign_test123",
                "state": {
                    "campaign": {
                        "id": "campaign_test123",
                        "name": "Test Kingdom",
                        "setting": "fantasy",
                        "current_location": "The Rusty Anchor Tavern",
                    },
                    "world": {
                        "description": "A test world.",
                        "factions": {},
                        "main_threat": "Test threat",
                    },
                    "npcs": {},
                },
            }
            await cmd_newgame(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0]
        assert "campaign_test123" in text or "Campaign Created" in text

        cs = mock_context.chat_data["_hermes_state"]
        assert cs.active_campaign == "campaign_test123"

    async def test_newgame_defaults_to_fantasy(self, mock_update, mock_context):
        """Test /newgame defaults to fantasy setting."""
        mock_context.args = []
        with patch("bot.telegram_handler._create_campaign") as mock_create:
            mock_create.return_value = {
                "campaign_id": "campaign_test",
                "state": {
                    "campaign": {
                        "id": "campaign_test",
                        "name": "Test",
                        "setting": "fantasy",
                        "current_location": " Tavern",
                    },
                    "world": {"description": ".", "factions": {}, "main_threat": ""},
                    "npcs": {},
                },
            }
            await cmd_newgame(mock_update, mock_context)
        mock_create.assert_called_once_with("fantasy")

    async def test_newgame_invalid_setting_falls_back(self, mock_update, mock_context):
        """Test /newgame with invalid setting falls back to fantasy."""
        mock_context.args = ["invalid_setting"]
        with patch("bot.telegram_handler._create_campaign") as mock_create:
            mock_create.return_value = {
                "campaign_id": "campaign_test",
                "state": {
                    "campaign": {
                        "id": "campaign_test",
                        "name": "Test",
                        "setting": "fantasy",
                        "current_location": " Tavern",
                    },
                    "world": {"description": ".", "factions": {}, "main_threat": ""},
                    "npcs": {},
                },
            }
            await cmd_newgame(mock_update, mock_context)
        mock_create.assert_called_once_with("fantasy")


# ------------------------------------------------------------------
# /join
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdJoin:
    """Tests for cmd_join."""

    async def test_join_missing_args(self, mock_update, mock_context):
        """Test /join with missing args shows usage."""
        mock_context.args = []
        await cmd_join(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in text

    async def test_join_invalid_class(self, mock_update, mock_context):
        """Test /join with invalid class shows error."""
        mock_context.args = ["Valdric", "notaclass"]
        await cmd_join(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Unknown class" in text

    async def test_join_creates_character(self, mock_update, mock_context):
        """Test /join creates a character and stores in chat state."""
        mock_context.args = ["Valdric", "fighter", "3"]
        await cmd_join(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        cs = mock_context.chat_data["_hermes_state"]
        assert "valdric" in cs.characters
        char = cs.characters["valdric"]
        assert char.name == "Valdric"
        assert char.player_class == "fighter"
        assert char.level == 3

    async def test_join_defaults_level_to_1(self, mock_update, mock_context):
        """Test /join defaults level to 1 when not specified."""
        mock_context.args = ["Mira", "wizard"]
        await cmd_join(mock_update, mock_context)

        cs = mock_context.chat_data["_hermes_state"]
        assert "mira" in cs.characters
        assert cs.characters["mira"].level == 1


# ------------------------------------------------------------------
# /roll
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdRoll:
    """Tests for cmd_roll."""

    async def test_roll_default_d20(self, mock_update, mock_context):
        """Test /roll with no args rolls d20."""
        mock_context.args = []
        with patch("bot.telegram_handler._roll") as mock_roll:
            mock_roll.return_value = {
                "total": 10,
                "rolls": [10],
                "modifier": 0,
                "natural": 10,
                "is_crit": False,
                "is_fumble": False,
                "str": "d20",
            }
            await cmd_roll(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()

    async def test_roll_with_dice_string(self, mock_update, mock_context):
        """Test /roll with a dice string."""
        mock_context.args = ["2d6+3"]
        with patch("bot.telegram_handler._roll") as mock_roll:
            mock_roll.return_value = {
                "total": 11,
                "rolls": [4, 4],
                "modifier": 3,
                "natural": None,
                "is_crit": False,
                "is_fumble": False,
                "str": "2d6+3",
            }
            await cmd_roll(mock_update, mock_context)
        mock_roll.assert_called_once_with("2d6+3")

    async def test_roll_handles_error(self, mock_update, mock_context):
        """Test /roll handles _roll exceptions."""
        mock_context.args = ["bad_dice"]
        with patch("bot.telegram_handler._roll") as mock_roll:
            mock_roll.side_effect = Exception("Invalid dice")
            await cmd_roll(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "error" in text.lower() or "Invalid" in text

    async def test_roll_resolves_pending_attack(self, mock_update, mock_context):
        """Test /roll resolves a pending attack."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.pending_attacks["attack_0"] = {
            "attacker_name": "Valdric",
            "defender_name": "Goblin",
            "weapon": "sword",
            "defender_ac": 12,
            "rage_bonus": 0,
            "advantage": False,
            "disadvantage": False,
        }
        cs.characters["valdric"] = MagicMock()
        cs.characters["valdric"].hp = MagicMock()

        mock_context.args = ["d20+5"]
        with patch("bot.telegram_handler._roll") as mock_roll:
            mock_roll.return_value = {
                "total": 16,
                "rolls": [16],
                "modifier": 5,
                "natural": 16,
                "is_crit": False,
                "is_fumble": False,
                "str": "d20+5",
            }
            with patch("bot.telegram_handler.resolve_attack") as mock_attack:
                mock_attack.return_value = {
                    "hit": True,
                    "crit": False,
                    "damage": 8,
                    "rolls": [6, 2],
                    "note": "Hit! Valdric deals 8 damage to Goblin! (6, 2)",
                    "attacker": "Valdric",
                    "defender": "Goblin",
                }
                with patch("bot.telegram_handler.apply_damage") as mock_damage:
                    mock_damage.return_value = {"hp_lost": 8}
                    await cmd_roll(mock_update, mock_context)

        assert "attack_0" not in cs.pending_attacks
        mock_update.message.reply_text.assert_called_once()

    async def test_roll_resolves_pending_skill_check(self, mock_update, mock_context):
        """Test /roll resolves a pending skill check."""
        cs = mock_context.chat_data["_hermes_state"]
        mock_char = MagicMock()
        mock_char.name = "Valdric"
        mock_char.mod = MagicMock(return_value=3)
        mock_char.is_proficient = MagicMock(return_value=True)
        mock_char.proficiency_bonus = 2

        cs.pending_skill_check = {
            "character": mock_char,
            "skill": "athletics",
            "dc": 15,
            "advantage": False,
            "disadvantage": False,
        }
        cs.characters["valdric"] = mock_char

        mock_context.args = ["d20"]
        with patch("bot.telegram_handler._roll") as mock_roll:
            mock_roll.return_value = {
                "total": 14,
                "rolls": [14],
                "modifier": 0,
                "natural": 14,
                "is_crit": False,
                "is_fumble": False,
                "str": "d20",
            }
            await cmd_roll(mock_update, mock_context)

        assert cs.pending_skill_check is None
        mock_update.message.reply_text.assert_called_once()

    async def test_roll_resolves_pending_save(self, mock_update, mock_context):
        """Test /roll resolves a pending saving throw."""
        cs = mock_context.chat_data["_hermes_state"]
        mock_char = MagicMock()
        mock_char.name = "Valdric"
        mock_char.mod = MagicMock(return_value=1)
        mock_char.is_proficient = MagicMock(return_value=False)
        mock_char.proficiency_bonus = 2

        cs.pending_save = {
            "character": mock_char,
            "stat": "dex",
            "dc": 12,
            "advantage": False,
            "disadvantage": False,
        }
        cs.characters["valdric"] = mock_char

        mock_context.args = ["d20"]
        with patch("bot.telegram_handler._roll") as mock_roll:
            mock_roll.return_value = {
                "total": 15,
                "rolls": [15],
                "modifier": 0,
                "natural": 15,
                "is_crit": False,
                "is_fumble": False,
                "str": "d20",
            }
            await cmd_roll(mock_update, mock_context)

        assert cs.pending_save is None
        mock_update.message.reply_text.assert_called_once()


# ------------------------------------------------------------------
# /attack
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdAttack:
    """Tests for cmd_attack."""

    async def test_attack_missing_target(self, mock_update, mock_context):
        """Test /attack with no target shows usage."""
        mock_context.args = []
        await cmd_attack(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in text

    async def test_attack_queues_pending_attack(self, mock_update, mock_context):
        """Test /attack queues a pending attack."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.characters["testplayer"] = MagicMock()
        cs.characters["testplayer"].name = "TestPlayer"
        cs.characters["testplayer"].equipped_weapon = "longsword"

        mock_context.args = ["Goblin", "adv"]
        await cmd_attack(mock_update, mock_context)

        assert len(cs.pending_attacks) == 1
        attack = list(cs.pending_attacks.values())[0]
        assert attack["defender_name"] == "Goblin"
        assert attack["advantage"] is True
        assert attack["weapon"] == "longsword"

    async def test_attack_no_character(self, mock_update, mock_context):
        """Test /attack when no character joined shows error."""
        mock_context.args = ["Goblin"]
        await cmd_attack(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No character" in text


# ------------------------------------------------------------------
# /cast
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdCast:
    """Tests for cmd_cast."""

    async def test_cast_missing_args(self, mock_update, mock_context):
        """Test /cast with missing args shows usage."""
        mock_context.args = []
        await cmd_cast(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in text or "Available spells" in text

    async def test_cast_unknown_spell(self, mock_update, mock_context):
        """Test /cast with unknown spell shows error."""
        mock_context.args = ["notaspell", "Goblin"]
        await cmd_cast(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Unknown spell" in text

    async def test_cast_queues_pending_spell(self, mock_update, mock_context):
        """Test /cast queues a pending spell."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.characters["testplayer"] = MagicMock()
        cs.characters["testplayer"].name = "TestPlayer"
        cs.characters["testplayer"].level = 5

        mock_context.args = ["fireball", "Goblin"]
        await cmd_cast(mock_update, mock_context)

        assert cs.pending_spell is not None
        assert cs.pending_spell["spell_name"] == "fireball"
        assert cs.pending_spell["target_name"] == "Goblin"

    async def test_cast_no_character(self, mock_update, mock_context):
        """Test /cast when no character joined shows error."""
        mock_context.args = ["fireball", "Goblin"]
        await cmd_cast(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No character" in text


# ------------------------------------------------------------------
# /skill
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdSkill:
    """Tests for cmd_skill."""

    async def test_skill_missing_args(self, mock_update, mock_context):
        """Test /skill with missing args shows usage."""
        mock_context.args = []
        await cmd_skill(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in text

    async def test_skill_invalid_dc(self, mock_update, mock_context):
        """Test /skill with non-integer DC shows error."""
        mock_context.args = ["athletics", "notanumber"]
        await cmd_skill(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Invalid DC" in text

    async def test_skill_queues_pending_check(self, mock_update, mock_context):
        """Test /skill queues a pending skill check."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.characters["testplayer"] = MagicMock()
        cs.characters["testplayer"].name = "TestPlayer"

        mock_context.args = ["athletics", "15"]
        await cmd_skill(mock_update, mock_context)

        assert cs.pending_skill_check is not None
        assert cs.pending_skill_check["skill"] == "athletics"
        assert cs.pending_skill_check["dc"] == 15

    async def test_skill_with_advantage(self, mock_update, mock_context):
        """Test /skill with advantage flag."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.characters["testplayer"] = MagicMock()
        cs.characters["testplayer"].name = "TestPlayer"

        mock_context.args = ["athletics", "15", "adv"]
        await cmd_skill(mock_update, mock_context)

        assert cs.pending_skill_check is not None
        assert cs.pending_skill_check["advantage"] is True


# ------------------------------------------------------------------
# /save
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdSave:
    """Tests for cmd_save."""

    async def test_save_missing_args(self, mock_update, mock_context):
        """Test /save with missing args shows usage."""
        mock_context.args = []
        await cmd_save(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in text

    async def test_save_queues_pending_save(self, mock_update, mock_context):
        """Test /save queues a pending saving throw."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.characters["testplayer"] = MagicMock()
        cs.characters["testplayer"].name = "TestPlayer"

        mock_context.args = ["dex", "12"]
        await cmd_save(mock_update, mock_context)

        assert cs.pending_save is not None
        assert cs.pending_save["stat"] == "dex"
        assert cs.pending_save["dc"] == 12


# ------------------------------------------------------------------
# /status
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdStatus:
    """Tests for cmd_status."""

    async def test_status_no_characters(self, mock_update, mock_context):
        """Test /status when no characters joined."""
        await cmd_status(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No characters" in text

    async def test_status_shows_party(self, mock_update, mock_context):
        """Test /status shows party summary."""
        cs = mock_context.chat_data["_hermes_state"]
        mock_char = MagicMock()
        mock_char.name = "Valdric"
        mock_char.player_class = "fighter"
        mock_char.level = 3
        mock_char.hp.current = 20
        mock_char.hp.max = 30
        mock_char.hp.temp = 0
        mock_char.ac = 16
        cs.characters["valdric"] = mock_char

        await cmd_status(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Valdric" in text


# ------------------------------------------------------------------
# /hp
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdHP:
    """Tests for cmd_hp."""

    async def test_hp_no_character(self, mock_update, mock_context):
        """Test /hp when no character joined."""
        await cmd_hp(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No character" in text

    async def test_hp_shows_hp_report(self, mock_update, mock_context):
        """Test /hp shows HP report."""
        cs = mock_context.chat_data["_hermes_state"]
        mock_char = MagicMock()
        mock_char.name = "Valdric"
        mock_char.hp.current = 18
        mock_char.hp.max = 25
        mock_char.hp.temp = 5
        mock_char.death_saves.successes = 1
        mock_char.death_saves.failures = 0
        cs.characters["testplayer"] = mock_char

        await cmd_hp(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "18" in text
        assert "25" in text
        assert "5" in text


# ------------------------------------------------------------------
# /inventory
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdInventory:
    """Tests for cmd_inventory."""

    async def test_inventory_no_character(self, mock_update, mock_context):
        """Test /inventory when no character joined."""
        await cmd_inventory(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No character" in text

    async def test_inventory_empty(self, mock_update, mock_context):
        """Test /inventory with empty inventory."""
        cs = mock_context.chat_data["_hermes_state"]
        mock_char = MagicMock()
        mock_char.name = "Valdric"
        mock_char.inventory = []
        mock_char.inventory_slots = 10
        cs.characters["testplayer"] = mock_char

        await cmd_inventory(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "(empty)" in text

    async def test_inventory_shows_items(self, mock_update, mock_context):
        """Test /inventory shows item list."""
        cs = mock_context.chat_data["_hermes_state"]
        mock_item = MagicMock()
        mock_item.name = "Longsword"
        mock_item.quantity = 1
        mock_item.equipped = True
        mock_item.description = "A fine blade"

        mock_char = MagicMock()
        mock_char.name = "Valdric"
        mock_char.inventory = [mock_item]
        mock_char.inventory_slots = 10
        cs.characters["testplayer"] = mock_char

        await cmd_inventory(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Longsword" in text


# ------------------------------------------------------------------
# /talk
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdTalk:
    """Tests for cmd_talk."""

    async def test_talk_missing_args(self, mock_update, mock_context):
        """Test /talk with missing args shows usage."""
        mock_context.args = []
        await cmd_talk(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in text

    async def test_talk_no_active_campaign(self, mock_update, mock_context):
        """Test /talk with no active campaign."""
        mock_context.args = ["captain_vorn", "Hello"]
        await cmd_talk(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No active campaign" in text

    async def test_talk_npc_not_found(self, mock_update, mock_context):
        """Test /talk with unknown NPC."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.active_campaign = "campaign_test"

        with patch("bot.telegram_handler.load_state") as mock_load:
            mock_load.return_value = {
                "campaign": {"id": "campaign_test"},
                "npcs": {},
                "history": [],
            }
            mock_context.args = ["captain_vorn", "Hello"]
            await cmd_talk(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "not found" in text.lower() or "NPC not found" in text

    async def test_talk_found_npc(self, mock_update, mock_context):
        """Test /talk with a known NPC."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.active_campaign = "campaign_test"
        cs.characters["testplayer"] = MagicMock()
        cs.characters["testplayer"].name = "TestPlayer"

        with patch("bot.telegram_handler.load_state") as mock_load:
            mock_load.return_value = {
                "campaign": {"id": "campaign_test", "name": "Test"},
                "npcs": {
                    "captain_vorn": {
                        "name": "Captain Vorn",
                        "role": "Retired soldier",
                        "disposition": "Cautious",
                        "disposition_value": 10,
                        "dialogue_style": "Speaks carefully",
                        "location": "tavern",
                    }
                },
                "history": [{"session": 1, "event": "Test"}],
            }
            mock_context.args = ["captain_vorn", "Hello"]
            await cmd_talk(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Captain Vorn" in text


# ------------------------------------------------------------------
# /map
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdMap:
    """Tests for cmd_map."""

    async def test_map_no_campaign(self, mock_update, mock_context):
        """Test /map with no active campaign."""
        await cmd_map(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No active campaign" in text

    async def test_map_shows_location(self, mock_update, mock_context):
        """Test /map shows location details."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.active_campaign = "campaign_test"

        with patch("bot.telegram_handler.load_state") as mock_load:
            mock_load.return_value = {
                "campaign": {
                    "id": "campaign_test",
                    "name": "Test",
                    "current_location": "The Rusty Anchor Tavern",
                },
                "world": {
                    "locations": {
                        "The Rusty Anchor Tavern": {
                            "description": "A cozy tavern.",
                            "npcs": ["captain_vorn"],
                        }
                    },
                    "factions": {"royal_guard": "DOMINANT"},
                    "main_threat": "Dragon",
                },
                "npcs": {
                    "captain_vorn": {
                        "name": "Captain Vorn",
                        "role": "Retired soldier",
                    }
                },
            }
            await cmd_map(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Rusty Anchor" in text


# ------------------------------------------------------------------
# /quests
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdQuests:
    """Tests for cmd_quests."""

    async def test_quests_no_campaign(self, mock_update, mock_context):
        """Test /quests with no active campaign."""
        await cmd_quests(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No active campaign" in text

    async def test_quests_shows_active(self, mock_update, mock_context):
        """Test /quests shows active quests."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.active_campaign = "campaign_test"

        with patch("bot.telegram_handler.load_state") as mock_load:
            mock_load.return_value = {
                "campaign": {"id": "campaign_test"},
                "quests": {
                    "active": ["Find the ancient artifact"],
                    "completed": [],
                },
                "history": [],
            }
            await cmd_quests(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "ancient artifact" in text


# ------------------------------------------------------------------
# /recap
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdRecap:
    """Tests for cmd_recap."""

    async def test_recap_no_campaign(self, mock_update, mock_context):
        """Test /recap with no active campaign."""
        await cmd_recap(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No active campaign" in text

    async def test_recap_shows_history(self, mock_update, mock_context):
        """Test /recap shows history entries."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.active_campaign = "campaign_test"

        with patch("bot.telegram_handler.load_state") as mock_load:
            mock_load.return_value = {
                "campaign": {"id": "campaign_test"},
                "history": [
                    {"session": 1, "event": "Campaign started"},
                    {"session": 1, "event": "Met Captain Vorn at the tavern"},
                ],
            }
            await cmd_recap(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Campaign started" in text


# ------------------------------------------------------------------
# /resume
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdResume:
    """Tests for cmd_resume."""

    async def test_resume_no_campaigns(self, mock_update, mock_context):
        """Test /resume when no campaigns exist."""
        with patch("bot.telegram_handler.list_campaigns") as mock_list:
            mock_list.return_value = []
            await cmd_resume(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No campaigns" in text

    async def test_resume_loads_latest(self, mock_update, mock_context):
        """Test /resume loads the most recent campaign."""
        with patch("bot.telegram_handler.list_campaigns") as mock_list:
            mock_list.return_value = [{"id": "campaign_latest", "name": "Latest"}]
            with patch("bot.telegram_handler.load_state") as mock_load:
                mock_load.return_value = {
                    "campaign": {
                        "id": "campaign_latest",
                        "name": "Latest Campaign",
                        "setting": "fantasy",
                        "current_location": "Tavern",
                    },
                    "world": {"main_threat": "Dragon", "factions": {}},
                    "npcs": {},
                }
                await cmd_resume(mock_update, mock_context)

        cs = mock_context.chat_data["_hermes_state"]
        assert cs.active_campaign == "campaign_latest"


# ------------------------------------------------------------------
# /endturn
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdEndturn:
    """Tests for cmd_endturn."""

    async def test_endturn_no_combat(self, mock_update, mock_context):
        """Test /endturn with no active combat."""
        await cmd_endturn(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No active combat" in text

    async def test_endturn_advances_turn(self, mock_update, mock_context):
        """Test /endturn advances to the next turn."""
        cs = mock_context.chat_data["_hermes_state"]

        mock_cs = MagicMock()
        mock_cs.active = True

        from bot.turn_manager import Combatant
        mock_cs.initiative_order = [
            Combatant(name="Valdric", initiative=18, is_player=True),
            Combatant(name="Goblin", initiative=12, is_player=False),
        ]
        mock_cs.current_index = 0
        mock_cs.round = 1
        mock_cs.current_turn = "Valdric"

        cs.combat_state = mock_cs

        with patch("bot.telegram_handler.next_turn") as mock_next:
            mock_next.return_value = {
                "who": "Goblin",
                "round": 1,
                "note": "Goblin's turn",
            }
            await cmd_endturn(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


# ------------------------------------------------------------------
# /campaign
# ------------------------------------------------------------------


@pytest.mark.asyncio
class TestCmdCampaign:
    """Tests for cmd_campaign."""

    async def test_campaign_no_active(self, mock_update, mock_context):
        """Test /campaign with no active campaign."""
        await cmd_campaign(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No active campaign" in text

    async def test_campaign_shows_details(self, mock_update, mock_context):
        """Test /campaign shows campaign details."""
        cs = mock_context.chat_data["_hermes_state"]
        cs.active_campaign = "campaign_test"
        mock_char = MagicMock()
        mock_char.name = "Valdric"
        mock_char.player_class = "fighter"
        mock_char.level = 3
        cs.characters["valdric"] = mock_char

        with patch("bot.telegram_handler.load_state") as mock_load:
            mock_load.return_value = {
                "campaign": {
                    "id": "campaign_test",
                    "name": "Test Campaign",
                    "setting": "fantasy",
                    "current_location": "Tavern",
                },
                "world": {
                    "main_threat": "Dragon",
                    "factions": {"royal_guard": "DOMINANT"},
                },
                "npcs": {"captain_vorn": {"name": "Captain Vorn", "role": "Soldier"}},
                "history": [],
            }
            await cmd_campaign(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Test Campaign" in text


# ------------------------------------------------------------------
# build_app
# ------------------------------------------------------------------


class TestBuildApp:
    """Test the application builder."""

    def test_build_app_returns_application(self):
        """Test build_app returns an Application instance."""
        mock_app_instance = MagicMock()

        with patch("bot.telegram_handler.ApplicationBuilder") as MockAppBuilder:
            instance = MockAppBuilder.return_value
            instance.token.return_value = instance
            instance.build.return_value = mock_app_instance
            from bot.telegram_handler import build_app
            app = build_app()
            assert app is mock_app_instance

    def test_build_app_registers_all_handlers(self):
        """Test build_app registers all command handlers."""
        mock_app_instance = MagicMock()
        call_count = 0

        def count_handlers(*args, **kwargs):
            nonlocal call_count
            call_count += 1

        mock_app_instance.add_handler = count_handlers

        with patch("bot.telegram_handler.ApplicationBuilder") as MockAppBuilder:
            instance = MockAppBuilder.return_value
            instance.token.return_value = instance
            instance.build.return_value = mock_app_instance
            from bot.telegram_handler import build_app
            build_app()
            # We expect: 19 CommandHandlers + 1 MessageHandler = 20
            assert call_count == 20, f"Expected 20 handler registrations, got {call_count}"

# ------------------------------------------------------------------
# Error handling — all handlers
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handler_no_crash_on_reply_error_cmd_start(mock_update, mock_context):
    """Test that cmd_start doesn't propagate reply_text exceptions."""
    from bot.telegram_handler import cmd_start
    async def silent_reply_text(*args, **kwargs):
        pass
    mock_update.message.reply_text = silent_reply_text
    await cmd_start(mock_update, mock_context)  # Should not raise
