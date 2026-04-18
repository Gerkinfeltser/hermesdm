"""
telegram_handler.py — Telegram bot handler for HermesDM.

Implements all game commands (/start, /newgame, /join, /roll, /attack,
/cast, /skill, /status, /hp, /inventory, /talk, /map, /quests, /recap,
/resume, /endturn, /campaign, /help) using python-telegram-bot v20+.

Per-chat state is stored in context.chat_data.
Entry point: ApplicationBuilder startup in __main__.
"""
from __future__ import annotations

import logging
import textwrap
from dataclasses import dataclass, field

from pydantic_settings import BaseSettings
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.character_sheet import (
    ALL_SKILLS,
    CLASS_DEFINITIONS,
    SKILL_BY_STAT,
    STATS,
    Character,
    create_character,
)
from bot.combat_engine import (
    SPELLS,
    apply_damage,
    resolve_attack,
    resolve_spell,
)

# Local modules
from bot.dice_engine import roll as _roll
from bot.turn_manager import (
    CombatState,
    combat_summary,
    next_turn,
)
from dm.world_builder import create_campaign as _create_campaign
from state.state_manager import (
    campaign_exists,
    list_campaigns,
    load_state,
    save_state,
)

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------


class Settings(BaseSettings):
    """Bot configuration via environment variables."""

    TELEGRAM_BOT_TOKEN: str = "8685005944:AAEmjcpY"
    ADMIN_USER_IDS: list[int] = []
    MAX_DICE_COUNT: int = 100
    MAX_DICE_SIDES: int = 100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# ------------------------------------------------------------------
# Per-chat state
# ------------------------------------------------------------------


@dataclass
class ChatState:
    """
    Per-chat (per-group) state kept in context.chat_data.
    """

    active_campaign: str | None = None
    """Campaign ID currently active in this chat."""

    pending_attacks: dict[str, dict] = field(default_factory=dict)
    """
    Pending attacks awaiting /roll confirmation.
    key = label like 'attack_0', value = {
        'attacker_name': str,
        'defender_name': str,
        'weapon': str,
        'defender_ac': int,
        'rage_bonus': int,
        'advantage': bool,
        'disadvantage': bool,
    }
    """

    pending_spell: dict | None = None
    """
    Pending spell awaiting /roll confirmation.
    {
        'caster_name': str,
        'spell_name': str,
        'target_name': str,
        'caster_level': int,
        'spell_data': dict,
    }
    """

    pending_skill_check: dict | None = None
    """
    Pending skill check awaiting /roll confirmation.
    {
        'character': Character,
        'skill': str,
        'dc': int,
        'advantage': bool,
        'disadvantage': bool,
    }
    """

    pending_save: dict | None = None
    """
    Pending saving throw awaiting /roll confirmation.
    {
        'character': Character,
        'stat': str,
        'dc': int,
        'advantage': bool,
        'disadvantage': bool,
    }
    """

    characters: dict[str, Character] = field(default_factory=dict)
    """
    Characters registered in this chat (player_name -> Character).
    """

    combat_state: CombatState | None = None
    """Active combat state for this chat."""

    def character_for(self, player_name: str) -> Character | None:
        return self.characters.get(player_name.lower())

    def active_character_names(self) -> list[str]:
        return list(self.characters.keys())


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _fmt_dice_result(r: dict) -> str:
    """Format a dice roll result as a readable string."""
    parts = [f"Rolling {r['str']}..."]
    parts.append(f"  Rolls: {r['rolls']}")
    if r["modifier"] != 0:
        parts.append(f"  Modifier: {r['modifier']:+d}")
    parts.append(f"  Total: {r['total']}")
    if r.get("is_crit"):
        parts.append("  >> NATURAL 20! CRITICAL! <<")
    elif r.get("is_fumble"):
        parts.append("  >> NATURAL 1! FUMBLE! <<")
    return "\n".join(parts)


def _fmt_character(c: Character) -> str:
    """Format a character sheet as a readable string."""
    stat_lines = ", ".join(f"{s.upper()}: {c.stats[s]} ({c.mod_str(s)})" for s in STATS)
    hp_line = f"{c.hp.current}/{c.hp.max}" + (
        f" (+{c.hp.temp} temp)" if c.hp.temp > 0 else ""
    )
    items = ", ".join(f"{i.name} x{i.quantity}" for i in c.inventory) or "empty"
    conds = ", ".join(c.conditions) if c.conditions else "none"
    death = (
        f"Death saves: {c.death_saves.successes} ✓ / {c.death_saves.failures} ✗"
        if c.hp.current == 0
        else ""
    )

    return "\n".join(
        [
            f"=== {c.name} ===",
            f"Class: {c.player_class.capitalize()} | Level {c.level}",
            f"HP: {hp_line} | AC: {c.ac}",
            f"Stats: {stat_lines}",
            f"Proficiencies: {', '.join(c.proficiencies) or 'none'}",
            f"Conditions: {conds}",
            f"Inventory ({len(c.inventory)}/{c.inventory_slots}): {items}",
            f"Weapon: {c.equipped_weapon or 'none'} | Armor: {c.equipped_armor or 'none'}",
            death,
        ]
    )


def _fmt_combat_summary(cs: CombatState) -> str:
    """Format active combat state."""
    if cs is None or not cs.active:
        return "No active combat."
    return combat_summary(cs)


# ------------------------------------------------------------------
# Command handlers
# ------------------------------------------------------------------


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start."""
    try:
        welcome = textwrap.dedent("""
            🎲 *HermesDM — AI Dungeon Master*

            Welcome, adventurer! I am your AI-powered dungeon master,
            ready to run epic tabletop RPG campaigns right here in Telegram.

            *Quick Start:*
            1. /newgame — Create a new campaign
            2. /join — Add your character to the campaign
            3. /campaign — View campaign details
            4. /help — Full command list

            May fortune favor the bold!
        """).strip()
        await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_start error")
        try:
            await update.message.reply_text(f"Error: {e}")
        except Exception:
            pass  # Already failing, give up silently


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help."""
    try:
        help_text = textwrap.dedent("""
            *HermesDM Commands*

            *Campaign*
            /newgame [fantasy|scifi|horror] — Create a new campaign
            /campaign — View active campaign details
            /join <name> <class> [level] — Add your character
            /map — View current location
            /quests — View active quests
            /recap — Story so far
            /resume — Resume last session

            *Character*
            /status — Character summary
            /hp — Detailed HP info
            /inventory — View inventory
            /skill <name> <dc> — Make a skill check
            /save <stat> <dc> — Make a saving throw

            *Combat*
            /attack <target> [adv|dis] — Start an attack (then /roll to resolve)
            /cast <spell> <target> — Cast a spell (then /roll to resolve)
            /endturn — End your turn
            /roll <dice> — Roll dice / confirm pending action

            *Info*
            /talk <npc> <message> — Talk to an NPC
            /help — Show this message
        """).strip()
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_help error")
        try:
            await update.message.reply_text(f"Error: {e}")
        except Exception:
            pass  # Already failing, give up silently


async def cmd_newgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /newgame [setting]."""
    try:
        setting = (context.args[0].lower() if context.args else "fantasy")
        if setting not in ("fantasy", "scifi", "horror"):
            setting = "fantasy"

        result = _create_campaign(setting)
        campaign_id = result["campaign_id"]
        state = result["state"]

        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())
        cs.active_campaign = campaign_id
        cs.characters.clear()
        cs.pending_attacks.clear()
        cs.pending_spell = None
        cs.pending_skill_check = None
        cs.pending_save = None
        cs.combat_state = None
        chat_data["_hermes_state"] = cs

        intro = (
            f"🌍 *Campaign Created!* `{campaign_id}`\n\n"
            f"*{state['campaign']['name']}*\n"
            f"_{state['campaign']['setting'].capitalize()}_\n\n"
            f"{state['world']['description'][:200]}...\n\n"
            f"Use /join to add your character, then /campaign for details."
        )
        await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_newgame error")
        await update.message.reply_text(f"Error creating campaign: {e}")


async def cmd_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /join <name> <class> [level]."""
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /join <name> <class> [level]\n"
                "Example: /join Valdric fighter 3\n"
                "Classes: fighter, wizard, rogue, cleric, ranger, barbarian"
            )
            return

        name = args[0].strip()
        player_class = args[1].lower()
        level = int(args[2]) if len(args) > 2 and args[2].isdigit() else 1

        if player_class not in CLASS_DEFINITIONS:
            await update.message.reply_text(
                f"Unknown class: `{player_class}`\n"
                f"Valid classes: {', '.join(CLASS_DEFINITIONS.keys())}"
            )
            return

        char = create_character(name, player_class, level)
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())
        cs.characters[name.lower()] = char
        chat_data["_hermes_state"] = cs

        await update.message.reply_text(
            f"✅ *Character Joined!*\n\n{_fmt_character(char)}",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        log.exception("cmd_join error")
        await update.message.reply_text(f"Error joining: {e}")


async def cmd_roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /roll [dice] or confirm pending action."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        # Check for pending attacks
        if cs.pending_attacks:
            label, attack = list(cs.pending_attacks.items())[0]
            del cs.pending_attacks[label]

            raw = context.args[0] if context.args else "d20"
            result = _roll(raw)
            attack_roll = result["total"]

            resolved = resolve_attack(
                attacker_name=attack["attacker_name"],
                defender_name=attack["defender_name"],
                attack_roll=attack_roll,
                weapon=attack.get("weapon", "sword"),
                advantage=attack.get("advantage", False),
                disadvantage=attack.get("disadvantage", False),
                defender_ac=attack.get("defender_ac", 10),
                rage_bonus=attack.get("rage_bonus", 0),
            )

            note = f"🎯 *Attack Result*\n{resolved['note']}"
            if resolved["hit"] and resolved["damage"] > 0:
                # Find character and apply damage to their HP
                char = cs.character_for(attack["attacker_name"])
                if char:
                    dmg_result = apply_damage(char.hp, resolved["damage"])
                    note += f"\n{dmg_result['hp_lost']} damage applied to {attack['attacker_name']}"

            chat_data["_hermes_state"] = cs
            await update.message.reply_text(note, parse_mode=ParseMode.MARKDOWN)
            return

        # Check for pending spell
        if cs.pending_spell:
            spell_info = cs.pending_spell
            cs.pending_spell = None

            raw = context.args[0] if context.args else "d20"
            result = _roll(raw)

            spell_result = resolve_spell(
                caster_level=spell_info["caster_level"],
                spell_name=spell_info["spell_name"],
                spell_save_dc=spell_info["spell_data"].get("dc_base", 15),
                target_count=1,
                spell_data=spell_info["spell_data"],
            )

            note = f"✨ *Spell Result*\n{spell_result['note']}"
            chat_data["_hermes_state"] = cs
            await update.message.reply_text(note, parse_mode=ParseMode.MARKDOWN)
            return

        # Check for pending skill check
        if cs.pending_skill_check:
            check_info = cs.pending_skill_check
            cs.pending_skill_check = None

            raw = context.args[0] if context.args else "d20"
            result = _roll(raw)

            # Re-resolve with actual roll
            stat = None
            for s, skills in SKILL_BY_STAT.items():
                if check_info["skill"] in skills:
                    stat = s
                    break

            if stat:
                char: Character = check_info["character"]
                stat_mod = char.mod(stat)
                prof = char.is_proficient(check_info["skill"])
                prof_bonus = char.proficiency_bonus if prof else 0
                total = result["total"] + stat_mod + prof_bonus
                dc = check_info["dc"]
                success = total >= dc
                margin = total - dc

                note = (
                    f"🎲 *Skill Check*\n"
                    f"{char.name} uses {check_info['skill']} vs DC {dc}\n"
                    f"Roll: {result['rolls'][0]} + {stat_mod:+d}" +
                    (f" + prof {prof_bonus:+d}" if prof else "") +
                    f" = *{total}*\n"
                    f"→ *{'SUCCESS' if success else 'FAILURE'}* (by {margin:+d})"
                )
            else:
                note = f"Unknown skill: {check_info['skill']}"

            chat_data["_hermes_state"] = cs
            await update.message.reply_text(note, parse_mode=ParseMode.MARKDOWN)
            return

        # Check for pending save
        if cs.pending_save:
            save_info = cs.pending_save
            cs.pending_save = None

            raw = context.args[0] if context.args else "d20"
            result = _roll(raw)

            char: Character = save_info["character"]
            stat = save_info["stat"]
            stat_mod = char.mod(stat)
            save_prof = char.is_proficient(stat)
            prof_bonus = char.proficiency_bonus if save_prof else 0
            total = result["total"] + stat_mod + prof_bonus
            dc = save_info["dc"]
            success = total >= dc

            note = (
                f"🛡️ *Saving Throw*\n"
                f"{char.name} vs {stat.upper()} DC {dc}\n"
                f"Roll: {result['rolls'][0]} + {stat_mod:+d}" +
                (f" + prof {prof_bonus:+d}" if save_prof else "") +
                f" = *{total}*\n"
                f"→ *{'SUCCESS' if success else 'FAILURE'}*"
            )

            chat_data["_hermes_state"] = cs
            await update.message.reply_text(note, parse_mode=ParseMode.MARKDOWN)
            return

        # Plain /roll
        dice_str = context.args[0] if context.args else "d20"
        try:
            result = _roll(dice_str)
            await update.message.reply_text(
                _fmt_dice_result(result),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as roll_err:
            await update.message.reply_text(f"Roll error: {roll_err}")

    except Exception as e:
        log.exception("cmd_roll error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /attack <target> [adv|dis]."""
    try:
        args = context.args
        if not args:
            await update.message.reply_text(
                "Usage: /attack <target_name> [adv|dis]\n"
                "Then use /roll to resolve the attack."
            )
            return

        target = args[0]
        advantage = "adv" in args
        disadvantage = "dis" in args

        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        player_name = update.effective_user.first_name.lower()

        # Use player's active character or default
        char = cs.character_for(player_name)
        if char is None and cs.characters:
            char = list(cs.characters.values())[0]

        if char is None:
            await update.message.reply_text(
                "No character found. Use /join to create one first."
            )
            return

        attacker_name = char.name
        weapon = char.equipped_weapon or "sword"

        label = f"attack_{len(cs.pending_attacks)}"
        cs.pending_attacks[label] = {
            "attacker_name": attacker_name,
            "defender_name": target,
            "weapon": weapon,
            "defender_ac": 10,  # default AC; bot DM would set actual
            "rage_bonus": 0,
            "advantage": advantage,
            "disadvantage": disadvantage,
        }
        chat_data["_hermes_state"] = cs

        adv_note = " (ADV)" if advantage else (" (DIS)" if disadvantage else "")
        await update.message.reply_text(
            f"⚔️ *Attack queued*\n"
            f"{attacker_name} attacks {target}{adv_note} with {weapon}.\n"
            f"Use /roll <dice> (e.g. /roll d20+5) to resolve.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        log.exception("cmd_attack error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_cast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cast <spell> <target>."""
    try:
        args = context.args
        if len(args) < 2:
            spell_list = ", ".join(SPELLS.keys())
            await update.message.reply_text(
                f"Usage: /cast <spell_name> <target>\n\n"
                f"Available spells: {spell_list}\n"
                f"Use /roll to resolve the spell effect.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        spell_name = args[0].lower()
        target = " ".join(args[1:])

        if spell_name not in SPELLS:
            await update.message.reply_text(
                f"Unknown spell: `{spell_name}`\n"
                f"Available: {', '.join(SPELLS.keys())}"
            )
            return

        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        player_name = update.effective_user.first_name.lower()
        char = cs.character_for(player_name)
        if char is None and cs.characters:
            char = list(cs.characters.values())[0]

        if char is None:
            await update.message.reply_text(
                "No character found. Use /join to create one first."
            )
            return

        spell_data = SPELLS[spell_name]
        cs.pending_spell = {
            "caster_name": char.name,
            "spell_name": spell_name,
            "target_name": target,
            "caster_level": char.level,
            "spell_data": spell_data,
        }
        chat_data["_hermes_state"] = cs

        desc = spell_data.get("description", "")
        await update.message.reply_text(
            f"✨ *Spell Queued*\n"
            f"{char.name} casts *{spell_name.upper()}* on {target}.\n"
            f"_{desc}_\n"
            f"Use /roll to resolve.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        log.exception("cmd_cast error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_skill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /skill <skill_name> <dc>."""
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /skill <skill_name> <dc> [adv|dis]\n"
                f"Skills: {', '.join(sorted(ALL_SKILLS))}"
            )
            return

        skill = args[0].lower().replace(" ", "_")
        try:
            dc = int(args[1])
        except ValueError:
            await update.message.reply_text(f"Invalid DC: `{args[1]}`")
            return

        advantage = "adv" in args
        disadvantage = "dis" in args

        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        player_name = update.effective_user.first_name.lower()
        char = cs.character_for(player_name)
        if char is None and cs.characters:
            char = list(cs.characters.values())[0]

        if char is None:
            await update.message.reply_text(
                "No character found. Use /join to create one first."
            )
            return

        if skill not in ALL_SKILLS:
            await update.message.reply_text(f"Unknown skill: `{skill}`")
            return

        cs.pending_skill_check = {
            "character": char,
            "skill": skill,
            "dc": dc,
            "advantage": advantage,
            "disadvantage": disadvantage,
        }
        chat_data["_hermes_state"] = cs

        await update.message.reply_text(
            f"🎲 *Skill Check Queued*\n"
            f"{char.name} attempts *{skill}* vs DC {dc}.\n"
            f"Use /roll to resolve.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        log.exception("cmd_skill error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status — show character summary."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        if not cs.characters:
            await update.message.reply_text(
                "No characters in this campaign. Use /join to add one."
            )
            return

        lines = ["*Party Status*\n"]
        for char in cs.characters.values():
            hp_line = f"{char.hp.current}/{char.hp.max}" + (
                f" (+{char.hp.temp} temp)" if char.hp.temp > 0 else ""
            )
            lines.append(
                f"  {char.name} — {char.player_class.capitalize()} Lv{char.level} | "
                f"HP: {hp_line} | AC: {char.ac}"
            )

        combat = _fmt_combat_summary(cs.combat_state)
        if combat != "No active combat.":
            lines.append(f"\n{combat}")

        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_status error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_hp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /hp — detailed HP info for the caller's character."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        player_name = update.effective_user.first_name.lower()
        char = cs.character_for(player_name)
        if char is None and cs.characters:
            char = list(cs.characters.values())[0]

        if char is None:
            await update.message.reply_text(
                "No character found. Use /join to create one first."
            )
            return

        hp_info = (
            f"*HP Report — {char.name}*\n"
            f"Current: {char.hp.current} / {char.hp.max}\n"
            f"Temp HP: {char.hp.temp}\n"
        )
        if char.hp.current == 0:
            ds = char.death_saves
            hp_info += (
                f"\n*Death Saves*\n"
                f"Successes: {'✓ ' * ds.successes}{(3 - ds.successes) * '_ '}\n"
                f"Failures: {'✗ ' * ds.failures}{(3 - ds.failures) * '_ '}"
            )

        await update.message.reply_text(hp_info, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_hp error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /inventory — view inventory of the caller's character."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        player_name = update.effective_user.first_name.lower()
        char = cs.character_for(player_name)
        if char is None and cs.characters:
            char = list(cs.characters.values())[0]

        if char is None:
            await update.message.reply_text(
                "No character found. Use /join to create one first."
            )
            return

        if not char.inventory:
            await update.message.reply_text(
                f"*Inventory — {char.name}*\n(empty)"
            )
            return

        lines = [f"*Inventory — {char.name}* ({len(char.inventory)}/{char.inventory_slots})\n"]
        for item in char.inventory:
            eq = " [EQUIPPED]" if item.equipped else ""
            lines.append(f"  • {item.name} x{item.quantity}{eq}")
            if item.description:
                lines.append(f"    _{item.description[:60]}_")

        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_inventory error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /talk <npc_name> <message>."""
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /talk <npc_name> <message>\n"
                "Use /campaign to see available NPCs."
            )
            return

        npc_name = args[0].lower().replace(" ", "_")
        message = " ".join(args[1:])

        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        if not cs.active_campaign:
            await update.message.reply_text(
                "No active campaign. Use /newgame first."
            )
            return

        state = load_state(cs.active_campaign)
        if state is None:
            await update.message.reply_text("Campaign not found.")
            return

        npc_key = None
        for key in state.get("npcs", {}):
            if key == npc_name or state["npcs"][key]["name"].lower().replace(" ", "_") == npc_name:
                npc_key = key
                break

        if npc_key is None:
            npc_list = ", ".join(n["name"] for n in state.get("npcs", {}).values())
            await update.message.reply_text(
                f"NPC not found. Available: {npc_list or 'none'}"
            )
            return

        npc = state["npcs"][npc_key]
        player_name = update.effective_user.first_name.lower()
        char = cs.character_for(player_name)
        speaker = char.name if char else "Unknown"

        # Simple disposition-based response (the DM would narrate this in a full implementation)
        disp = npc.get("disposition_value", 0)
        if disp > 50:
            response_tone = "warm and friendly"
        elif disp < -50:
            response_tone = "cold and hostile"
        else:
            response_tone = "cautious and neutral"

        reply = (
            f"*You say to {npc['name']}:* \"{message}\"\n\n"
            f"*{npc['name']} ({npc['role']}) responds* — {response_tone}:\n"
            f"_{npc.get('dialogue_style', 'They look at you curiously.')}_"
        )

        # Record in history
        state["history"].append({
            "session": state["history"][-1]["session"] if state["history"] else 1,
            "event": f"{speaker} talked to {npc['name']}: {message}",
        })
        save_state(cs.active_campaign, state)

        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_talk error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_map(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /map — show current location details."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        if not cs.active_campaign:
            await update.message.reply_text(
                "No active campaign. Use /newgame first."
            )
            return

        state = load_state(cs.active_campaign)
        if state is None:
            await update.message.reply_text("Campaign not found.")
            return

        location = state["campaign"].get("current_location", "Unknown")
        loc_data = state.get("world", {}).get("locations", {}).get(location, {})
        desc = loc_data.get("description", "No description available.")
        npc_ids = loc_data.get("npcs", [])

        npc_names = [
            state["npcs"].get(nid, {}).get("name", nid)
            for nid in npc_ids
            if nid in state["npcs"]
        ]

        lines = [
            f"*📍 {location}*",
            f"\n_{desc[:300]}_",
        ]
        if npc_names:
            lines.append(f"\n*NPCs here:* {', '.join(npc_names)}")
        else:
            lines.append("\n*NPCs here:* none")

        factions = state.get("world", {}).get("factions", {})
        if factions:
            fact_lines = [f"  {k}: {v}" for k, v in factions.items()]
            lines.append("\n*Factions:*\n" + "\n".join(fact_lines))

        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_map error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_quests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quests — show active and completed quests."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        if not cs.active_campaign:
            await update.message.reply_text(
                "No active campaign. Use /newgame first."
            )
            return

        state = load_state(cs.active_campaign)
        if state is None:
            await update.message.reply_text("Campaign not found.")
            return

        active = state.get("quests", {}).get("active", [])
        completed = state.get("quests", {}).get("completed", [])

        lines = ["*Quests*\n"]
        if active:
            lines.append("*Active:*")
            for q in active:
                lines.append(f"  • {q}")
        else:
            lines.append("*Active:* none")

        if completed:
            lines.append("\n*Completed:*")
            for q in completed:
                lines.append(f"  ✓ {q}")

        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_quests error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_recap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /recap — story recap from campaign history."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        if not cs.active_campaign:
            await update.message.reply_text(
                "No active campaign. Use /newgame first."
            )
            return

        state = load_state(cs.active_campaign)
        if state is None:
            await update.message.reply_text("Campaign not found.")
            return

        history = state.get("history", [])
        if not history:
            await update.message.reply_text("No story history yet.")
            return

        lines = ["*Story Recap*\n"]
        for entry in history[-10:]:  # last 10 entries
            event = entry.get("event", str(entry))
            session = entry.get("session", "?")
            lines.append(f"[Session {session}] {event[:200]}")

        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_recap error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /resume — resume the last campaign."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        if cs.active_campaign and campaign_exists(cs.active_campaign):
            state = load_state(cs.active_campaign)
        else:
            # Find most recent campaign
            campaigns = list_campaigns()
            if not campaigns:
                await update.message.reply_text(
                    "No campaigns found. Use /newgame to create one."
                )
                return
            latest = campaigns[0]
            cs.active_campaign = latest["id"]
            state = load_state(cs.active_campaign)

        if state is None:
            await update.message.reply_text("Campaign not found.")
            return

        camp = state["campaign"]
        lines = [
            "*Campaign Resumed*\n",
            f"*{camp['name']}* ({camp['setting']})\n",
            f"Location: {camp.get('current_location', 'Unknown')}\n",
            f"World: {state['world'].get('main_threat', 'Unknown threat')}\n",
        ]

        npcs = state.get("npcs", {})
        if npcs:
            lines.append(f"Known NPCs: {', '.join(n['name'] for n in npcs.values())}")

        chat_data["_hermes_state"] = cs
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_resume error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_endturn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /endturn — advance combat to the next turn."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        if cs.combat_state is None or not cs.combat_state.active:
            await update.message.reply_text("No active combat. Start one with /attack.")
            return

        result = next_turn(cs.combat_state)
        if "error" in result:
            cs.combat_state = None
            await update.message.reply_text(
                f"Combat ended: {result.get('error', 'No combatants')}"
            )
            return

        chat_data["_hermes_state"] = cs
        summary = _fmt_combat_summary(cs.combat_state)
        await update.message.reply_text(summary, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_endturn error")
        await update.message.reply_text(f"Error: {e}")


async def cmd_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /campaign — show active campaign details."""
    try:
        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        if not cs.active_campaign:
            await update.message.reply_text(
                "No active campaign. Use /newgame first."
            )
            return

        state = load_state(cs.active_campaign)
        if state is None:
            await update.message.reply_text("Campaign not found.")
            return

        camp = state["campaign"]
        world = state.get("world", {})
        npcs = state.get("npcs", {})

        lines = [
            f"*Campaign: {camp['name']}*",
            f"Setting: {camp['setting'].capitalize()}",
            f"Location: {camp.get('current_location', 'Unknown')}",
            f"Threat: {world.get('main_threat', 'Unknown')}",
        ]

        if npcs:
            lines.append(f"Known NPCs: {', '.join(n['name'] for n in npcs.values())}")

        chars = cs.characters
        if chars:
            lines.append(f"\n*Party ({len(chars)}):*")
            for char in chars.values():
                lines.append(f"  • {char.name} ({char.player_class.capitalize()} Lv{char.level})")

        factions = world.get("factions", {})
        if factions:
            lines.append("\n*Factions:*")
            for name, status in factions.items():
                lines.append(f"  {name}: {status}")

        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.exception("cmd_campaign error")
        await update.message.reply_text(f"Error: {e}")


# ------------------------------------------------------------------
# Save command handler (saving throw)
# ------------------------------------------------------------------


async def cmd_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /save <stat> <dc> [adv|dis] — saving throw."""
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /save <str|dex|con|int|wis|cha> <dc> [adv|dis]"
            )
            return

        stat = args[0].lower()[:3]
        try:
            dc = int(args[1])
        except ValueError:
            await update.message.reply_text(f"Invalid DC: `{args[1]}`")
            return

        advantage = "adv" in args
        disadvantage = "dis" in args

        chat_data = context.chat_data
        cs: ChatState = chat_data.get("_hermes_state", ChatState())

        player_name = update.effective_user.first_name.lower()
        char = cs.character_for(player_name)
        if char is None and cs.characters:
            char = list(cs.characters.values())[0]

        if char is None:
            await update.message.reply_text(
                "No character found. Use /join to create one first."
            )
            return

        cs.pending_save = {
            "character": char,
            "stat": stat,
            "dc": dc,
            "advantage": advantage,
            "disadvantage": disadvantage,
        }
        chat_data["_hermes_state"] = cs

        await update.message.reply_text(
            f"🛡️ *Saving Throw Queued*\n"
            f"{char.name} attempts a *{stat.upper()}* save vs DC {dc}.\n"
            f"Use /roll to resolve.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        log.exception("cmd_save error")
        await update.message.reply_text(f"Error: {e}")


# ------------------------------------------------------------------
# Application builder & __main__
# ------------------------------------------------------------------


def build_app() -> Application:
    """Build and configure the Telegram bot application."""
    app = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("newgame", cmd_newgame))
    app.add_handler(CommandHandler("join", cmd_join))
    app.add_handler(CommandHandler("roll", cmd_roll))
    app.add_handler(CommandHandler("attack", cmd_attack))
    app.add_handler(CommandHandler("cast", cmd_cast))
    app.add_handler(CommandHandler("skill", cmd_skill))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("hp", cmd_hp))
    app.add_handler(CommandHandler("inventory", cmd_inventory))
    app.add_handler(CommandHandler("talk", cmd_talk))
    app.add_handler(CommandHandler("map", cmd_map))
    app.add_handler(CommandHandler("quests", cmd_quests))
    app.add_handler(CommandHandler("recap", cmd_recap))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("endturn", cmd_endturn))
    app.add_handler(CommandHandler("campaign", cmd_campaign))
    app.add_handler(CommandHandler("save", cmd_save))

    # Catch-all message handler to prevent unknown command errors
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, _echo_handler)
    )

    return app


async def _echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch non-command text messages with a friendly nudge."""
    try:
        await update.message.reply_text(
            "I didn't understand that. Type /help for available commands."
        )
    except Exception:
        log.exception("_echo_handler error")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    app = build_app()
    log.info("HermesDM bot starting...")
    app.run_polling(drop_pending_updates=True)
