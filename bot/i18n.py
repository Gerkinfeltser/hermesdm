"""Internationalization module — language-aware UI strings for HermesDM.

Provides get() and get_for_campaign() to look up translated strings
from a central TRANSLATIONS dict. Falls back to EN then raw key.
"""

from __future__ import annotations

import os
from typing import Any

from campaign_settings import Language

_DEFAULT_LANG = Language(os.environ.get("DEFAULT_LANGUAGE", "en"))

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "error_generic": "Error: {e}",
        "campaign_not_found": "Campaign not found.",
        "no_active_campaign": "No active campaign. Use /setup to create one.",
        "no_active_campaign_newgame": "No active campaign. Use /newgame first.",
        "no_character_found": "No character found. Use /join to create one first.",
        "no_character_found_join": "No character found. Use /join first.",
        "no_characters_in_campaign": "No characters in this campaign. Use /join to add one.",
        "combat_no_active": "No active combat.",
        "combat_ended": "Combat ended: {reason}",
        "combat_turn_countdown": "⏱️ {character}'s turn — Round {round}\n`[{bar}] {seconds}s`",
        "combat_time_expired": "⏰ Time's up!\n🎯 {character}'s turn — moving to next.",
        "combat_has_ended": "⛔ Combat has ended.",
        "combat_has_ended_alt": "⚔️ Combat has ended.",
        "combat_need_two": "⚠️ Need at least 2 combatants to start combat.",
        "combat_started_header": "⚔️ *COMBAT STARTED!*",
        "combat_round_label": "_Round {round}_",
        "combat_initiative_order": "*Initiative order:*",
        "combat_first_to_act": "🎯 *{name}* is first to act.",
        "combat_ended_message": "🛑 *Combat ended.*\nAll participants have left combat mode.",
        "cmd_start_welcome": (
            "🎲 *HermesDM — AI Dungeon Master*\n\n"
            "Welcome, adventurer! I am your AI-powered dungeon master,\n"
            "ready to run epic tabletop RPG campaigns right here in Telegram.\n\n"
            "*Quick Start:*\n"
            "1. /setup — Create a new campaign\n"
            "2. /join — Add your character to the campaign\n"
            "3. /campaign — View campaign details\n"
            "4. /help — Full command list\n\n"
            "May fortune favor the bold!"
        ),
        "cmd_help_header": "🎲 *HermesDM — Commands*",
        "cmd_help_section_campaign": "*🎭 Campaign*",
        "cmd_help_section_character": "*👤 Character*",
        "cmd_help_section_combat": "*⚔️ Combat*",
        "cmd_help_section_world": "*🗺️ World*",
        "cmd_help_section_other": "*🎨 Other*",
        "cmd_version_error": "Error showing version.",
        "cmd_newgame_deprecated": (
            "⚠️ This command is deprecated.\n"
            "Use `/setup` to create a new campaign with free-form description and AI generation.\n"
            "Example: `/setup dark fantasy in a corrupt port city`"
        ),
        "cmd_setup_already_active": "⚠️ There is already an active campaign. Close it with /end before creating a new one.",
        "cmd_setup_usage": (
            "⚠️ *Campaign Setup*\n\n"
            "Usage: `/setup <description>`\n\n"
            "Examples:\n"
            "- `/setup dark fantasy in a corrupt port city`\n"
            "- `/setup horror one-shot in an abandoned mansion`\n\n"
            "Duration options:\n"
            "- `--short` → ~5 sessions (one-shot)\n"
            "- `--medium` → ~10 sessions (default)\n"
            "- `--long` → ~20 sessions (epic campaign)\n\n"
            "Include: tone, setting, adventure type."
        ),
        "cmd_setup_generating": "🎲 Generating with AI...",
        "cmd_setup_preview_instructions": (
            "📋 *Preview generated.*\n\n"
            "Edit fields with:\n"
            "`edit premise: ...`\n"
            "`edit hook: ...`\n"
            "`edit tone: dark`\n\n"
            "When ready: `/perfecto` / `/arrancamos`\n"
            "To cancel: `/cancel`"
        ),
        "cmd_setup_generation_error": (
            "⚠️ Error in setup generation.\n\n"
            "Description: {description}\n"
            "Error: {ai_err}\n\n"
            "Check the API key and try again with /setup."
        ),
        "setup_field_unknown": "Unknown field: `{field}`. Editable fields: premise, hook, tone, setting",
        "setup_field_updated": "✅ `{field}` updated to: {value}",
        "setup_canceled": "❌ Setup canceled.",
        "setup_edit_approve_group": "_Edit or approve from the group_",
        "setup_preview_generated": (
            "📋 *Preview generated.*\n\n"
            "Edit: `edit premise: ...`, `edit tone: dark`\n"
            "Approve: `perfecto` / `arrancamos`\n"
            "Cancel: `cancel`"
        ),
        "setup_ai_connection_error": "⚠️ Could not connect to AI: {ai_err}",
        "setup_no_active_setup": "No active setup. Use /setup to start one.",
        "setup_no_active_to_cancel": "No active setup to cancel.",
        "setup_no_pending": "❌ No pending setup to approve.",
        "setup_campaign_published": "✅ *Campaign published!* Players use /join to register.\nWhen everyone is ready, the DM uses /start to begin the adventure.",
        "setup_approve_error": "Error approving setup: {e}",
        "setup_preview_header": "🎭 *CAMPAIGN PREVIEW*",
        "setup_preview_description": "📝 *Description:*",
        "setup_preview_premise": "📖 *Premise:*",
        "setup_preview_hook": "🎯 *Hook:*",
        "setup_preview_location": "🌍 *Location:*",
        "setup_preview_tone": "⚔️ *Tone:*",
        "setup_preview_setting": "*Setting:*",
        "setup_preview_threat": "🚨 *Threat:*",
        "setup_preview_factions": "⚡ *Factions:*",
        "setup_preview_npcs": "👥 *NPCs:*",
        "setup_preview_equipment": "🎒 *Starting equipment:*",
        "setup_preview_story_arc": "📜 *Story arc*",
        "setup_preview_classes": "🎭 *Classes:*",
        "setup_published_characters": "👥 *Characters*\nRegister your character with `/join <name> <class>`",
        "setup_published_config": "⚙️ *Config*\n🌐 Language: {lang} | 🗣️ Tone: {tone} | ⚔️ Setting: {setting}",
        "setup_published_dm_start": "_The DM will use /start to begin the adventure_",
        "cmd_begin_no_campaign": "⚠️ No active campaign. Use /setup to create one.",
        "cmd_begin_still_in_setup": "⚠️ The campaign is still in setup. Approve it with `perfecto` first.",
        "cmd_begin_already_started": "🎭 The adventure has already begun. Use /recap to remember or /j to act.",
        "cmd_begin_no_characters": "⚠️ No characters registered. Use /join first.",
        "cmd_begin_adventure_starts": "🎭 *The adventure begins!*\n\n{narrative}\n\n_Use /j to describe your action._",
        "cmd_begin_error": "Error starting adventure: {e}",
        "cmd_join_not_ready": "⚠️ The campaign isn't ready yet.\nWait for the DM to configure and approve it.",
        "cmd_join_usage": "Usage: /join <name> <class> [level]\nExample: /join Valdric fighter 3\n{class_help}",
        "cmd_join_unknown_class": "❓ Unknown class: `{player_class}`\nAvailable: {classes}\nOr define with: `edit classes: Foo, Bar` in /setup",
        "cmd_join_success": "✅ Character Joined!\n\n{character_sheet}",
        "cmd_join_error": "Error joining: {e}",
        "roll_attack_result": "🎯 *Attack Result*\n{note}",
        "roll_character_died": "\n💀 {name} has DIED! {status}",
        "roll_character_stabilized": "\n✨ {name} has STABILIZED! {status}",
        "roll_death_save_status": "\n🫀 Death save: {status}",
        "roll_tpk_message": (
            "\n\n☠️ *TOTAL PARTY KILL!*\n"
            "All party members have fallen...\n"
            "The campaign has ended.\n\n"
            "Use /end to close the campaign or /resume to try again."
        ),
        "roll_enemy_defeated": "\n💀 {name} defeated!",
        "roll_narrative_addition": "\n\n📝 {narrative}",
        "roll_spell_result": "✨ *Spell Result*\n{note}",
        "roll_unknown_skill": "Unknown skill: {skill}",
        "roll_error": "Roll error: {roll_err}",
        "cmd_attack_usage": "Usage: /attack <target_name> [adv|dis]\nThen use /roll to resolve the attack.",
        "cmd_attack_queued": "⚔️ *Attack queued*\n{attacker} attacks {target}{adv_note} with {weapon}.\nUse /roll <dice> (e.g. /roll d20+5) to resolve.{combatStarted}",
        "cmd_cast_usage": "Usage: /cast <spell_name> [target]\n\n{spell_list}",
        "cmd_cast_unknown_spell": "Unknown spell: `{spell_name}`\nAvailable: {spells}",
        "cmd_skill_usage": "Usage: /skill <skill_name> <dc> [adv|dis]\nSkills: {skills}",
        "cmd_skill_invalid_dc": "Invalid DC: `{dc}`",
        "cmd_skill_unknown_skill": "Unknown skill: `{skill}`",
        "cmd_skill_queued": "🎲 *Skill Check Queued*\n{character} attempts *{skill}* vs DC {dc}.\nUse /roll to resolve.",
        "cmd_status_no_characters": "No characters in this campaign. Use /join to add one.",
        "cmd_status_header": "*Party Status*\n",
        "cmd_hp_report": (
            "*HP Report — {name}*\n"
            "Current: {current} / {max}\n"
            "Temp HP: {temp}\n\n"
            "*Death Saves*\n"
            "Successes: {successes}\n"
            "Failures: {failures}"
        ),
        "cmd_inventory_empty": "*Inventory — {name}*\n(empty)",
        "cmd_inventory_header": "*Inventory — {name}* ({used}/{max})\n💰 {gold} gp | ⚖️ {weight}/{capacity} lbs\n",
        "cmd_give_usage": (
            "🎁 *Item Transfer*\n\n"
            "Usage: /give <character> <item> [quantity]\n"
            "Example: /give Valdric Longsword\n"
            "Use /inventory to see your inventory."
        ),
        "cmd_give_no_campaign": "⚠️ No active campaign. Use /newgame first.",
        "cmd_give_character_not_found": "⚠️ Character '{name}' not found in the party.\nAvailable: {available}",
        "cmd_give_giver_not_found": "⚠️ Your character was not found. Use /join to register.",
        "cmd_give_no_item": "⚠️ You must specify which item to give.\nExample: /give Valdric Longsword",
        "cmd_give_dont_have_item": "⚠️ You don't have '{item}' in your inventory.\nUse /inventory to see your items.",
        "cmd_give_insufficient_quantity": "⚠️ You only have {qty}x '{name}'.\nYou can't give {requested}.",
        "cmd_give_inventory_full": "⚠️ {receiver}'s inventory is full ({slots}/{slots}).",
        "cmd_give_success": (
            "🎁 *Transfer complete*\n\n"
            "{giver} gives {item} to {receiver}.\n"
            "{giver}'s inventory: {used_g}/{max_g}\n"
            "{receiver}'s inventory: {used_r}/{max_r}"
        ),
        "cmd_talk_usage": "Usage: /talk <npc_name> <message>\nUse /campaign to see available NPCs.",
        "cmd_talk_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_talk_npc_not_found": "NPC not found. Available: {npcs}",
        "cmd_npcs_no_campaign": "No active campaign.",
        "cmd_npcsearch_usage": "Usage: /npcsearch <query>",
        "cmd_npcsearch_no_results": "No NPCs found matching: {query}",
        "cmd_npcsearch_results_header": '**NPCs matching "{query}"**\n',
        "cmd_npcnote_usage": "Usage: /npcnote <npc_name> <note text>\nExample: /npcnote Gorin He betrayed the party last session.",
        "cmd_npcnote_not_found": "NPC '{name}' not found. Use /npcs to see all NPCs.",
        "cmd_npcnote_saved": "Note saved for **{name}**.\n_Note: {note}_",
        "cmd_npcmemory_usage": "Usage: /npcmemory <npc_name> <key> <value>\nExample: /npcmemory Gorin secret_weakness Afraid of fire",
        "cmd_npcmemory_added": "Memory added to **{name}**.\n**{key}**: {value}",
        "cmd_map_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_map_location_header": "*📍 {location}*",
        "cmd_map_no_npcs": "\n*NPCs here:* none",
        "cmd_map_factions_header": "\n*Factions:*\n",
        "cmd_quests_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_quests_header": "*Quests*\n",
        "cmd_quests_active": "*Active:*",
        "cmd_quests_no_active": "*Active:* none",
        "cmd_quests_completed": "\n*Completed:*",
        "cmd_recap_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_recap_no_history": "No story history yet.",
        "cmd_recap_header": "*Story Recap*\n",
        "cmd_resume_no_campaigns": "No campaigns found. Use /newgame to create one.",
        "cmd_resume_header": "*Campaign Resumed*\n",
        "cmd_spells_header": "📖 **Spells** ({class})\n\n",
        "cmd_prepare_not_prepared_caster": "Your class doesn't use spell preparation.",
        "cmd_prepare_all_known_available": "Your class doesn't require preparation. All known spells are always available.",
        "cmd_prepare_not_in_spellbook": "Spell '{spell}' not in your spellbook.",
        "cmd_prepare_success": "✅ Prepared **{spell}** (Level {level})",
        "cmd_prepare_already_prepared": "Already prepared or not in spellbook.",
        "cmd_remember_npc_not_found": "NPC '{name}' not found.",
        "cmd_disengage_taken": "🛡 **{name}** takes the **Disengage** action.\nNo opportunity attacks until your next turn.",
        "cmd_disengage_not_in_combat": "Disengage is a combat action. Start combat first.",
        "cmd_endturn_no_combat": "No active combat. Start one with /attack.",
        "cmd_campaign_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_campaign_header": "*Campaign: {name}*",
        "cmd_campaign_party_header": "\n*Party ({count}):*",
        "cmd_campaign_factions_header": "\n*Factions:*",
        "cmd_start_no_campaign": "No active campaign. Use /setup to create one.",
        "cmd_start_already_completed": "This campaign has already ended. Use /newgame to create a new one.",
        "cmd_start_no_players": "No players in the party yet. Use /join to register your character.",
        "cmd_start_adventure_begins": (
            "🎭 *THE ADVENTURE BEGINS!*\n\n"
            "_{narrative}_\n\n"
            "👥 Party: {party}\n\n"
            "What do the adventurers do?"
        ),
        "cmd_startcombat_no_characters": "⚠️ No characters registered. Use /join first.",
        "cmd_startcombat_already_active": "⚔️ There is already active combat. Use /endcombat to end it first.",
        "cmd_endcombat_no_combat": "⚠️ No active combat.",
        "cmd_quit_message": (
            "👋 *Leaving DM mode.*\n\n"
            "Until the next adventure!\n"
            "The bot will keep running in the group to accept commands.\n"
            "Use /newgame or /resume to play again."
        ),
        "cmd_quit_goodbye": "👋 Until next time!",
        "cmd_end_no_campaign": "⚠️ No active campaign. Use /newgame to start one.",
        "cmd_end_already_completed": "⚠️ This campaign has already been completed. Use /newgame to create a new one.",
        "cmd_epilogue_header": "🎭 *EPILOGUE — {name}*\n\n{narrative}",
        "cmd_end_closed_successfully": "✅ *Campaign closed successfully.*\n\nThanks for playing! Use /newgame to start a new adventure.",
        "cmd_end_error": "Error closing campaign: {e}",
        "cmd_audit_admin_only": "⛔ Only admins can view the audit log.",
        "cmd_imagen_no_campaign": "⚠️ No active campaign. Use /newgame to start one.",
        "cmd_imagen_disabled": "🎨 *Image generation disabled.*\n\nUse `/configuracion imagen on` to enable.",
        "cmd_imagen_generating": "🎨 Generating scene image...",
        "cmd_imagen_failed": "⚠️ Could not generate the image. The generation servers may be busy. Try again.",
        "cmd_imagen_not_saved": "⚠️ The generated image was not saved correctly.",
        "cmd_imagen_corrupted": "⚠️ The generated image appears to be corrupted. Try again.",
        "cmd_imagen_caption": "🎨 *{location}* — _{provider}_",
        "cmd_shortrest_no_campaign": "No active campaign.",
        "cmd_shortrest_no_character": "Your character was not found. Use /join first.",
        "cmd_shortrest_no_hit_dice": "😴 {name} has no hit dice available. Use /longrest for a long rest to recover them.",
        "cmd_shortrest_result": "🛌 *{name} takes a short rest...*\n\n❤️ +{hp_rec} HP ({hp_now}/{hp_max})\n🎲 Hit dice remaining: {hd_left}{warlock_note}",
        "cmd_longrest_result": (
            "🏕️ *{name} takes a long rest...*\n\n"
            "❤️ {old_hp} → {hp_now}/{hp_max} HP (full recovery)\n"
            "🎲 Hit dice restored: {hd_rec}\n"
            "🔮 Spell slots recovered\n\n"
            "✨ *Resources renewed!*"
        ),
        "cmd_conditions_no_character": "Your character was not found.",
        "cmd_conditions_no_active": "✅ *{name}*: no active conditions.",
        "cmd_conditions_header": "📋 *{name}'s conditions:*\n",
        "cmd_conditions_save_instruction": "  → Save: {stat} DC {dc} (end of turn)",
        "image_auto_caption": "🎨 *{provider}* — _Auto-generated_",
        "settings_image_activated": "🎨 Image generation: enabled (Pollinations)",
        "settings_image_deactivated": "🎨 Image generation: disabled",
        "settings_invalid_value": "Invalid value: {value}. Use 'on' or 'off'",
        "settings_difficulty_updated": "Difficulty: {label}",
        "settings_difficulty_invalid": "Use: easy, normal, hard",
        "settings_tone_updated": "Tone: {label}",
        "settings_tone_invalid": "Use: serious, funny, dark, epic",
        "settings_timer_negative": "Timer cannot be negative",
        "settings_timer_deactivated": "Timer deactivated",
        "settings_timer_updated": "Timer: {seconds}s per turn",
        "settings_timer_invalid": "Invalid value: {value}. Use a number (0=off)",
        "settings_luck_positive": "Luck: +{bonus} to all checks",
        "settings_luck_negative": "Luck: {bonus} to all checks",
        "settings_luck_invalid": "Invalid value: {value}. Use a number (e.g. +2, -1)",
        "settings_dramatic_dice_activated": "Dramatic dice: enabled",
        "settings_dramatic_dice_deactivated": "Dramatic dice: disabled",
        "settings_language_updated": "Language: {label}",
        "settings_language_invalid": "Use: es, pt, en",
        "settings_unknown_option": "Unknown option: {key}",
        "settings_summary_header": "⚙️ *Current settings*\n\n",
        "settings_summary_images": "  🎨 Images: {status}",
        "settings_summary_difficulty": "  ⚔️ Difficulty: {label}",
        "settings_summary_tone": "  🗣️ Tone: {label}",
        "settings_summary_language": "  🌐 Language: {label}",
        "settings_summary_timer": "  ⏱️ Timer: {seconds}",
        "settings_summary_dramatic_dice": "  🎲 Dramatic dice: {yes_no}",
        "settings_summary_luck": "  🍀 Luck: {bonus}",
        "game_attack_usage": "⚔️ Usage: `!attack [target] [AC] [weapon?] [--adv|--dis?]`\nExample: `!attack Orc 16 longsword --adv`\nDefault weapon: sword | Default AC: 10",
        "game_ac_must_be_number": "⚔️ AC must be a number. Example: `!attack Orc 16`",
        "game_attack_prepared": "🎯 *Attack Prepared!*\n\n{summary}\n\nReply with `!confirm {confirm_id}` to resolve, or `!cancel` to cancel.",
        "game_confirm_usage": "Usage: `!confirm <attack_id>`\nUse the attack ID shown when you created the attack.",
        "game_no_pending_attack": "❌ No pending attack found with ID `{id}`.\nUse `!attack <target>` to start a new attack.",
        "game_cancelled_attacks": "✅ Cancelled {count} pending attack(s).",
        "game_no_attacks_to_cancel": "No pending attacks to cancel.",
        "game_no_pending_attacks": "No pending attacks. Use `!attack <target>` to start one.",
        "game_pending_attacks_header": "⚔️ *Pending Attacks*",
        "game_attack_summary": "⚔️ *Pending Attack*\nAttacker: {attacker}\nTarget: {target}\nWeapon: {weapon}\nDefender AC: {ac}\nDice: {dice}{adv_note}\nID: `{id}`",
        "config_no_campaign": "No active campaign. Use /newgame to create one.",
        "config_unknown_option": "Unknown option: *{key}*\n\n{help_text}",
        "config_success": "✅ {message}",
        "config_error": "❌ {message}\n\n{help_text}",
        "language_set": "🌐 Language set to {lang}",
        "language_usage": "Usage: /language <es|en>",
        "language_unsupported": "Unsupported language: {lang}. Use: es, en",
    },
    "es": {
        "error_generic": "Error: {e}",
        "campaign_not_found": "⚠️ Campaña no encontrada.",
        "no_active_campaign": "⚠️ No hay campaña activa. Usá /setup para crear una.",
        "no_active_campaign_newgame": "⚠️ No hay campaña activa. Usa /newgame primero.",
        "no_character_found": "No character found. Use /join to create one first.",
        "no_character_found_join": "No character found. Use /join first.",
        "no_characters_in_campaign": "⚠️ No hay personajes registrados. Usa /join primero.",
        "combat_no_active": "No active combat.",
        "combat_ended": "Combat ended: {reason}",
        "combat_turn_countdown": "⏱️ Turno de *{character}* — Round {round}\n`[{bar}] {seconds}s`",
        "combat_time_expired": "⏰ ¡Tiempo agotado!\n🎯 Turno de *{character}* — pasando al siguiente.",
        "combat_has_ended": "⛔ El combate ha terminado.",
        "combat_has_ended_alt": "⚔️ El combate ha terminado.",
        "combat_need_two": "⚠️ Need at least 2 combatants to start combat.",
        "combat_started_header": "⚔️ *COMBATE INICIADO!*",
        "combat_round_label": "_Round {round}_",
        "combat_initiative_order": "*Orden de iniciativa:*",
        "combat_first_to_act": "🎯 *{name}* es el primero en actuar.",
        "combat_ended_message": "🛑 *Combate finalizado.*\nTodos los participantes han salido del modo combate.",
        "cmd_start_welcome": (
            "🎲 *HermesDM — AI Dungeon Master*\n\n"
            "Welcome, adventurer! I am your AI-powered dungeon master,\n"
            "ready to run epic tabletop RPG campaigns right here in Telegram.\n\n"
            "*Quick Start:*\n"
            "1. /setup — Create a new campaign (describe it in Spanish!)\n"
            "2. /join — Add your character to the campaign\n"
            "3. /campaign — View campaign details\n"
            "4. /help — Full command list\n\n"
            "May fortune favor the bold!"
        ),
        "cmd_help_header": "🎲 *HermesDM — Comandos*",
        "cmd_help_section_campaign": "*🎭 Campaña*",
        "cmd_help_section_character": "*👤 Personaje*",
        "cmd_help_section_combat": "*⚔️ Combate*",
        "cmd_help_section_world": "*🗺️ Mundo*",
        "cmd_help_section_other": "*🎨 Otros*",
        "cmd_version_error": "Error mostrando versión.",
        "cmd_newgame_deprecated": (
            "⚠️ Este comando está deprecated.\n"
            "Usá `/setup` para crear una nueva campaña con descripción libre y generación AI.\n"
            "Ejemplo: `/setup quiero una campaña dark fantasy en un puerto corrupto`"
        ),
        "cmd_setup_already_active": "⚠️ Ya hay una campaña activa. Cerrala con /end antes de crear una nueva.",
        "cmd_setup_usage": (
            "⚠️ *Setup de Campaña*\n\n"
            "Usá: `/setup <descripción>`\n\n"
            "Ejemplos:\n"
            "- `/setup dark fantasy en un puerto corrupto`\n"
            "- `/setup oneshot de terror en una mansión abandonada`\n\n"
            "Opciones de duración:\n"
            "- `--short` → ~5 sesiones (one-shot)\n"
            "- `--medium` → ~10 sesiones (default)\n"
            "- `--long` → ~20 sesiones (campaña épica)\n\n"
            "Incluí: tono, setting, tipo de aventura."
        ),
        "cmd_setup_generating": "🎲 Generando con AI...",
        "cmd_setup_preview_instructions": (
            "📋 *Preview generado.*\n\n"
            "Editá campos con:\n"
            "`edit premisa: ...`\n"
            "`edit hook: ...`\n"
            "`edit tono: dark`\n\n"
            "Cuando estés listo: `/perfecto` / `/arrancamos`\n"
            "Para cancelar: `/cancel`"
        ),
        "cmd_setup_generation_error": (
            "⚠️ Error en generación de setup.\n\n"
            "Descripción: {description}\n"
            "Error: {ai_err}\n\n"
            "Revisá la API key y volvé a intentar con /setup."
        ),
        "setup_field_unknown": "Campo no reconocido: `{field}`. Campos editables: premise, hook, tono, setting",
        "setup_field_updated": "✅ `{field}` actualizado a: {value}",
        "setup_canceled": "❌ Setup cancelado.",
        "setup_edit_approve_group": "_Editá o aprobá desde el grupo_",
        "setup_preview_generated": (
            "📋 *Preview generado.*\n\n"
            "Editá: `edit premisa: ...`, `edit tono: dark`\n"
            "Aprobá: `perfecto` / `arrancamos`\n"
            "Cancelá: `cancel`"
        ),
        "setup_ai_connection_error": "⚠️ No pude conectar con AI: {ai_err}",
        "setup_no_active_setup": "No hay un setup activo. Usá /setup para empezar.",
        "setup_no_active_to_cancel": "No hay un setup activo para cancelar.",
        "setup_no_pending": "❌ No hay setup pendiente para aprobar.",
        "setup_campaign_published": "✅ *Campaña publicada!* Los jugadores usan /join para registrarse.\nCuando todos estén listos, el DM usa /start para iniciar la aventura.",
        "setup_approve_error": "Error al aprobar setup: {e}",
        "setup_preview_header": "🎭 *PREVIEW DE CAMPAÑA*",
        "setup_preview_description": "📝 *Descripción:*",
        "setup_preview_premise": "📖 *Premise:*",
        "setup_preview_hook": "🎯 *Hook:*",
        "setup_preview_location": "🌍 *Ubicación:*",
        "setup_preview_tone": "⚔️ *Tono:*",
        "setup_preview_setting": "*Setting:*",
        "setup_preview_threat": "🚨 *Amenaza:*",
        "setup_preview_factions": "⚡ *Facciones:*",
        "setup_preview_npcs": "👥 *NPCs:*",
        "setup_preview_equipment": "🎒 *Equipo inicial:*",
        "setup_preview_story_arc": "📜 *Arco narrativo*",
        "setup_preview_classes": "🎭 *Clases:*",
        "setup_published_characters": "👥 *Personajes*\nRegistrá tu personaje con `/join <nombre> <clase>`",
        "setup_published_config": "⚙️ *Config*\n🌐 Idioma: {lang} | 🗣️ Tono: {tone} | ⚔️ Setting: {setting}",
        "setup_published_dm_start": "_El DM usará /start para iniciar la aventura_",
        "cmd_begin_no_campaign": "⚠️ No hay campaña activa. Usá /setup para crear una.",
        "cmd_begin_still_in_setup": "⚠️ La campaña aún está en setup. Aprobalá con `perfecto` primero.",
        "cmd_begin_already_started": "🎭 La aventura ya comenzó. Usá /recap para recordar o /j para actuar.",
        "cmd_begin_no_characters": "⚠️ No hay personajes registrados. Usá /join primero.",
        "cmd_begin_adventure_starts": "🎭 *¡La aventura comienza!*\n\n{narrative}\n\n_Usá /j para describir tu acción._",
        "cmd_begin_error": "Error al iniciar aventura: {e}",
        "cmd_join_not_ready": "⚠️ La campaña aún no está lista.\nEsperá a que el DM la configure y apruebe.",
        "cmd_join_usage": "Usage: /join <name> <class> [level]\nExample: /join Valdric fighter 3\n{class_help}",
        "cmd_join_unknown_class": "❓ Clase desconocida: `{player_class}`\nDisponibles: {classes}\nO definilas con: `edit clases: Foo, Bar` en /setup",
        "cmd_join_success": "✅ Character Joined!\n\n{character_sheet}",
        "cmd_join_error": "Error joining: {e}",
        "roll_attack_result": "🎯 *Attack Result*\n{note}",
        "roll_character_died": "\n💀 ¡{name} ha MUERTO! {status}",
        "roll_character_stabilized": "\n✨ ¡{name} se ha ESTABILIZADO! {status}",
        "roll_death_save_status": "\n🫀 Death save: {status}",
        "roll_tpk_message": (
            "\n\n☠️ *¡TOTAL PARTY KILL!*\n"
            "Todos los miembros del party han caído...\n"
            "La campaña ha terminado.\n\n"
            "Usá /end para cerrar la campaña o /resume para intentar de nuevo."
        ),
        "roll_enemy_defeated": "\n💀 {name} derrotado!",
        "roll_narrative_addition": "\n\n📝 {narrative}",
        "roll_spell_result": "✨ *Spell Result*\n{note}",
        "roll_unknown_skill": "Unknown skill: {skill}",
        "roll_error": "Roll error: {roll_err}",
        "cmd_attack_usage": "Usage: /attack <target_name> [adv|dis]\nThen use /roll to resolve the attack.",
        "cmd_attack_queued": "⚔️ *Attack queued*\n{attacker} attacks {target}{adv_note} with {weapon}.\nUse /roll <dice> (e.g. /roll d20+5) to resolve.{combatStarted}",
        "cmd_cast_usage": "Usage: /cast <spell_name> [target]\n\n{spell_list}",
        "cmd_cast_unknown_spell": "Unknown spell: `{spell_name}`\nAvailable: {spells}",
        "cmd_skill_usage": "Usage: /skill <skill_name> <dc> [adv|dis]\nSkills: {skills}",
        "cmd_skill_invalid_dc": "Invalid DC: `{dc}`",
        "cmd_skill_unknown_skill": "Unknown skill: `{skill}`",
        "cmd_skill_queued": "🎲 *Skill Check Queued*\n{character} attempts *{skill}* vs DC {dc}.\nUse /roll to resolve.",
        "cmd_status_no_characters": "No characters in this campaign. Use /join to add one.",
        "cmd_status_header": "*Party Status*\n",
        "cmd_hp_report": (
            "*HP Report — {name}*\n"
            "Current: {current} / {max}\n"
            "Temp HP: {temp}\n\n"
            "*Death Saves*\n"
            "Successes: {successes}\n"
            "Failures: {failures}"
        ),
        "cmd_inventory_empty": "*Inventory — {name}*\n(empty)",
        "cmd_inventory_header": "*Inventory — {name}* ({used}/{max})\n💰 {gold} gp | ⚖️ {weight}/{capacity} lbs\n",
        "cmd_give_usage": (
            "🎁 *Transferencia de item*\n\n"
            "Uso: /give <personaje> <item> [cantidad]\n"
            "Ejemplo: /give Valdric Espada Larga\n"
            "Usa /inventory para ver tu inventario."
        ),
        "cmd_give_no_campaign": "⚠️ No hay campaña activa. Usa /newgame primero.",
        "cmd_give_character_not_found": "⚠️ Personaje '{name}' no encontrado en la party.\nDisponibles: {available}",
        "cmd_give_giver_not_found": "⚠️ No se encontró tu personaje. Usa /join para registrarte.",
        "cmd_give_no_item": "⚠️ Debes especificar qué item quieres dar.\nEjemplo: /give Valdric Espada Larga",
        "cmd_give_dont_have_item": "⚠️ No tienes '{item}' en tu inventario.\nUsa /inventory para ver tus items.",
        "cmd_give_insufficient_quantity": "⚠️ Solo tienes {qty}x '{name}'.\nNo puedes dar {requested}.",
        "cmd_give_inventory_full": "⚠️ El inventario de {receiver} está lleno ({slots}/{slots}).",
        "cmd_give_success": (
            "🎁 *Transferencia realizada*\n\n"
            "{giver} le da {item} a {receiver}.\n"
            "Inventario de {giver}: {used_g}/{max_g}\n"
            "Inventario de {receiver}: {used_r}/{max_r}"
        ),
        "cmd_talk_usage": "Usage: /talk <npc_name> <message>\nUse /campaign to see available NPCs.",
        "cmd_talk_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_talk_npc_not_found": "NPC not found. Available: {npcs}",
        "cmd_npcs_no_campaign": "No active campaign.",
        "cmd_npcsearch_usage": "Usage: /npcsearch <query>",
        "cmd_npcsearch_no_results": "No NPCs found matching: {query}",
        "cmd_npcsearch_results_header": '**NPCs matching "{query}"**\n',
        "cmd_npcnote_usage": "Usage: /npcnote <npc_name> <note text>\nExample: /npcnote Gorin He betrayed the party last session.",
        "cmd_npcnote_not_found": "NPC '{name}' not found. Use /npcs to see all NPCs.",
        "cmd_npcnote_saved": "Note saved for **{name}**.\n_Note: {note}_",
        "cmd_npcmemory_usage": "Usage: /npcmemory <npc_name> <key> <value>\nExample: /npcmemory Gorin secret_weakness Afraid of fire",
        "cmd_npcmemory_added": "Memory added to **{name}**.\n**{key}**: {value}",
        "cmd_map_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_map_location_header": "*📍 {location}*",
        "cmd_map_no_npcs": "\n*NPCs here:* none",
        "cmd_map_factions_header": "\n*Factions:*\n",
        "cmd_quests_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_quests_header": "*Quests*\n",
        "cmd_quests_active": "*Active:*",
        "cmd_quests_no_active": "*Active:* none",
        "cmd_quests_completed": "\n*Completed:*",
        "cmd_recap_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_recap_no_history": "No story history yet.",
        "cmd_recap_header": "*Story Recap*\n",
        "cmd_resume_no_campaigns": "No campaigns found. Use /newgame to create one.",
        "cmd_resume_header": "*Campaign Resumed*\n",
        "cmd_spells_header": "📖 **Spells** ({class})\n\n",
        "cmd_prepare_not_prepared_caster": "Your class doesn't use spell preparation.",
        "cmd_prepare_all_known_available": "Your class doesn't require preparation. All known spells are always available.",
        "cmd_prepare_not_in_spellbook": "Spell '{spell}' not in your spellbook.",
        "cmd_prepare_success": "✅ Prepared **{spell}** (Level {level})",
        "cmd_prepare_already_prepared": "Already prepared or not in spellbook.",
        "cmd_remember_npc_not_found": "NPC '{name}' not found.",
        "cmd_disengage_taken": "🛡 **{name}** takes the **Disengage** action.\nNo opportunity attacks until your next turn.",
        "cmd_disengage_not_in_combat": "Disengage is a combat action. Start combat first.",
        "cmd_endturn_no_combat": "No active combat. Start one with /attack.",
        "cmd_campaign_no_campaign": "No active campaign. Use /newgame first.",
        "cmd_campaign_header": "*Campaign: {name}*",
        "cmd_campaign_party_header": "\n*Party ({count}):*",
        "cmd_campaign_factions_header": "\n*Factions:*",
        "cmd_start_no_campaign": "No hay campaña activa. Usa /setup para crear una.",
        "cmd_start_already_completed": "Esta campaña ya terminó. Usa /newgame para crear una nueva.",
        "cmd_start_no_players": "Aún no hay jugadores en la party. Usa /join para registrar tu personaje.",
        "cmd_start_adventure_begins": (
            "🎭 *¡LA AVENTURA COMIENZA!*\n\n"
            "_{narrative}_\n\n"
            "👥 Party: {party}\n\n"
            "¿Qué hacen los aventureros?"
        ),
        "cmd_startcombat_no_characters": "⚠️ No hay personajes registrados. Usa /join primero.",
        "cmd_startcombat_already_active": "⚔️ Ya hay combate activo. Usa /endcombat para terminarlo primero.",
        "cmd_endcombat_no_combat": "⚠️ No hay combate activo.",
        "cmd_quit_message": (
            "👋 *Saliendo del modo DM.*\n\n"
            "¡Hasta la próxima aventura!\n"
            "El bot seguirá corriendo en el grupo para recibir comandos.\n"
            "Usa /newgame o /resume para volver a jugar."
        ),
        "cmd_quit_goodbye": "👋 Hasta la próxima!",
        "cmd_end_no_campaign": "⚠️ No hay campaña activa. Usa /newgame para empezar.",
        "cmd_end_already_completed": "⚠️ Esta campaña ya fue completada. Usa /newgame para crear una nueva.",
        "cmd_epilogue_header": "🎭 *EPÍLOGO — {name}*\n\n{narrative}",
        "cmd_end_closed_successfully": "✅ *Campaña cerrada exitosamente.*\n\n¡Gracias por jugar! Usa /newgame para comenzar una nueva aventura.",
        "cmd_end_error": "Error cerrando campaña: {e}",
        "cmd_audit_admin_only": "⛔ Solo admins pueden ver el audit log.",
        "cmd_imagen_no_campaign": "⚠️ No hay campaña activa. Usa /newgame para empezar.",
        "cmd_imagen_disabled": "🎨 *Generación de imágenes desactivada.*\n\nUsa `/configuracion imagen on` para activar.",
        "cmd_imagen_generating": "🎨 Generando imagen de la escena...",
        "cmd_imagen_failed": "⚠️ No se pudo generar la imagen. Los servidores de generación pueden estar saturados. Intentá de nuevo.",
        "cmd_imagen_not_saved": "⚠️ La imagen generada no se guardó correctamente.",
        "cmd_imagen_corrupted": "⚠️ La imagen generada parece estar corrupta. Intentá de nuevo.",
        "cmd_imagen_caption": "🎨 *{location}* — _{provider}_",
        "cmd_shortrest_no_campaign": "No hay campaña activa.",
        "cmd_shortrest_no_character": "No encontré tu personaje. Usa /join primero.",
        "cmd_shortrest_no_hit_dice": "😴 {name} no tiene hit dice disponibles. Usa /longrest para descansar largo y recuperarlos.",
        "cmd_shortrest_result": "🛌 *{name} descansa brevemente...*\n\n❤️ +{hp_rec} HP ({hp_now}/{hp_max})\n🎲 Hit dice restantes: {hd_left}{warlock_note}",
        "cmd_longrest_result": (
            "🏕️ *{name} descansa largamente...*\n\n"
            "❤️ {old_hp} → {hp_now}/{hp_max} HP (recuperación completa)\n"
            "🎲 Hit dice restaurados: {hd_rec}\n"
            "🔮 Spell slots recuperados\n\n"
            "✨ *Recursos renovados!*"
        ),
        "cmd_conditions_no_character": "No encontré tu personaje.",
        "cmd_conditions_no_active": "✅ *{name}*: sin condiciones activas.",
        "cmd_conditions_header": "📋 *Condiciones de {name}:*\n",
        "cmd_conditions_save_instruction": "  → Save: {stat} DC {dc} (end of turn)",
        "image_auto_caption": "🎨 *{provider}* — _Generada automaticamente_",
        "settings_image_activated": "🎨 Generación de imágenes: activada (Pollinations)",
        "settings_image_deactivated": "🎨 Generación de imágenes: desactivada",
        "settings_invalid_value": "Valor inválido: {value}. Usa 'on' u 'off'",
        "settings_difficulty_updated": "Dificultad: {label}",
        "settings_difficulty_invalid": "Usa: easy, normal, hard",
        "settings_tone_updated": "Tono: {label}",
        "settings_tone_invalid": "Usa: serious, funny, dark, epic",
        "settings_timer_negative": "El timer no puede ser negativo",
        "settings_timer_deactivated": "Timer desactivado",
        "settings_timer_updated": "Timer: {seconds}s por turno",
        "settings_timer_invalid": "Valor inválido: {value}. Usa un número (0=off)",
        "settings_luck_positive": "Suerte: +{bonus} a todos los checks",
        "settings_luck_negative": "Suerte: {bonus} a todos los checks",
        "settings_luck_invalid": "Valor inválido: {value}. Usa un número (ej: +2, -1)",
        "settings_dramatic_dice_activated": "Dados dramáticos: activados",
        "settings_dramatic_dice_deactivated": "Dados dramáticos: desactivados",
        "settings_language_updated": "Idioma: {label}",
        "settings_language_invalid": "Usa: es, pt, en",
        "settings_unknown_option": "Opción desconocida: {key}",
        "settings_summary_header": "⚙️ *Configuración actual*\n\n",
        "settings_summary_images": "  🎨 Imágenes: {status}",
        "settings_summary_difficulty": "  ⚔️ Dificultad: {label}",
        "settings_summary_tone": "  🗣️ Tono: {label}",
        "settings_summary_language": "  🌐 Idioma: {label}",
        "settings_summary_timer": "  ⏱️ Timer: {seconds}",
        "settings_summary_dramatic_dice": "  🎲 Dados dramáticos: {yes_no}",
        "settings_summary_luck": "  🍀 Suerte: {bonus}",
        "game_attack_usage": "⚔️ Uso: `!attack [objetivo] [CA] [arma?] [--adv?--dis?]`\nEjemplo: `!attack Orco 16 longsword --adv`\nArma default: sword | CA default: 10",
        "game_ac_must_be_number": "⚔️ CA debe ser un número. Ejemplo: `!attack Orco 16`",
        "game_attack_prepared": "🎯 *Attack Prepared!*\n\n{summary}\n\nReply with `!confirm {confirm_id}` to resolve this attack, or `!cancel` to cancel.",
        "game_confirm_usage": "Usage: `!confirm <attack_id>`\nUse the attack ID shown when you created the attack.",
        "game_no_pending_attack": "❌ No pending attack found with ID `{id}`.\nUse `!attack <target>` to start a new attack.",
        "game_cancelled_attacks": "✅ Cancelled {count} pending attack(s).",
        "game_no_attacks_to_cancel": "No pending attacks to cancel.",
        "game_no_pending_attacks": "No pending attacks. Use `!attack <target>` to start one.",
        "game_pending_attacks_header": "⚔️ *Pending Attacks*",
        "game_attack_summary": "⚔️ *Pending Attack*\nAttacker: {attacker}\nTarget: {target}\nWeapon: {weapon}\nDefender AC: {ac}\nDice: {dice}{adv_note}\nID: `{id}`",
        "config_no_campaign": "No hay campaign activa. Usa /newgame para crear una.",
        "config_unknown_option": "Opción desconocida: *{key}*\n\n{help_text}",
        "config_success": "✅ {message}",
        "config_error": "❌ {message}\n\n{help_text}",
        "language_set": "🌐 Idioma configurado a {lang}",
        "language_usage": "Uso: /language <es|en>",
        "language_unsupported": "Idioma no soportado: {lang}. Usa: es, en",
    },
}


def get(key: str, language: str | Language | None = None, **kwargs: Any) -> str:
    """Look up a translated string by key.

    Args:
        key: Translation key (e.g. 'error_generic').
        language: Target language code. Falls back to DEFAULT_LANGUAGE, then 'en'.
        **kwargs: Format parameters interpolated into the string.

    Returns:
        The translated (and interpolated) string, or the raw key if not found.
    """
    if language is None:
        lang_code = _DEFAULT_LANG.value
    elif isinstance(language, Language):
        lang_code = language.value
    else:
        lang_code = language

    lang_dict = TRANSLATIONS.get(lang_code, {})
    text = lang_dict.get(key)

    if text is None:
        en_dict = TRANSLATIONS.get("en", {})
        text = en_dict.get(key, key)

    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass

    return text


def get_for_campaign(campaign_id: str, key: str, **kwargs: Any) -> str:
    """Look up a translated string using a campaign's language setting.

    Loads campaign state → CampaignSettings.language → translates key.
    Falls back to DEFAULT_LANGUAGE if campaign not found.
    """
    try:
        from state.state_manager import get_settings

        settings = get_settings(campaign_id)
        if settings:
            return get(key, settings.language, **kwargs)
    except Exception:
        pass

    return get(key, _DEFAULT_LANG, **kwargs)
