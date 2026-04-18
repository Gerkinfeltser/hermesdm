"""
skill_checks.py — Ability checks, saving throws, skill resolution.
No narrative — pure mechanics.
"""
from bot.character_sheet import ALL_SKILLS, SKILL_BY_STAT
from bot.dice_engine import roll

# 6 abilities + their related skills
ABILITIES = {
    "str": "Strength",
    "dex": "Dexterity",
    "con": "Constitution",
    "int": "Intelligence",
    "wis": "Wisdom",
    "cha": "Charisma"
}

# Difficulty Classes (standard)
DC_TABLE = {
    "trivial": 5,
    "easy": 10,
    "medium": 15,
    "hard": 20,
    "very_hard": 25,
    "nearly_impossible": 30
}


def get_dc(dc_name_or_value) -> int:
    if isinstance(dc_name_or_value, int):
        return dc_name_or_value
    return DC_TABLE.get(str(dc_name_or_value).lower(), 15)


def resolve_skill_check(
    character,
    skill: str,
    dc: int,
    advantage: bool = False,
    disadvantage: bool = False
) -> dict:
    """
    Resolve a skill check.
    Returns {success, margin, total, roll, note}
    """
    skill = skill.lower().replace(" ", "_")

    if skill not in ALL_SKILLS:
        return {"error": f"Unknown skill: {skill}"}

    stat = None
    for s, skills in SKILL_BY_STAT.items():
        if skill in skills:
            stat = s
            break

    stat_mod = character.mod(stat)
    prof = character.is_proficient(skill)
    prof_bonus = character.proficiency_bonus if prof else 0

    # Roll d20
    roll_result = roll("d20")
    total = roll_result["total"] + stat_mod + prof_bonus

    if advantage:
        roll2 = roll("d20")["total"]
        total = max(total, roll_result["total"] + stat_mod + prof_bonus,
                    roll2 + stat_mod + prof_bonus)
    elif disadvantage:
        roll2 = roll("d20")["total"]
        total = min(total, roll_result["total"] + stat_mod + prof_bonus,
                    roll2 + stat_mod + prof_bonus)

    margin = total - dc
    success = total >= dc

    note_parts = [f"{character.name} uses {skill} ({stat[:3].upper()} {stat_mod:+d})"]
    if prof:
        note_parts.append(f"+ prof {prof_bonus:+d}")
    note_parts.append(f"= {total} vs DC {dc}")
    note_parts.append("-> SUCCESS" if success else "-> FAILURE")

    return {
        "success": success,
        "margin": margin,
        "total": total,
        "roll": roll_result["rolls"][0],
        "dc": dc,
        "stat": stat,
        "stat_mod": stat_mod,
        "proficient": prof,
        "note": " ".join(note_parts)
    }


def resolve_save(
    character,
    stat: str,
    dc: int,
    advantage: bool = False,
    disadvantage: bool = False
) -> dict:
    """
    Resolve a saving throw.
    Returns {success, margin, total, note}
    """
    stat = stat.lower()[:3]
    stat_map = {"str": "str", "dex": "dex", "con": "con",
                "int": "int", "wis": "wis", "cha": "cha"}
    stat_key = stat_map.get(stat, stat)

    stat_mod = character.mod(stat_key)
    save_prof = character.is_proficient(stat_key)
    prof_bonus = character.proficiency_bonus if save_prof else 0

    roll_result = roll("d20")

    if advantage and not disadvantage:
        roll2 = roll("d20")["total"]
        total = max(roll_result["total"], roll2) + stat_mod + prof_bonus
    elif disadvantage and not advantage:
        roll2 = roll("d20")["total"]
        total = min(roll_result["total"], roll2) + stat_mod + prof_bonus
    else:
        total = roll_result["total"] + stat_mod + prof_bonus

    margin = total - dc
    success = total >= dc

    return {
        "success": success,
        "margin": margin,
        "total": total,
        "roll": roll_result["rolls"][0],
        "dc": dc,
        "stat": stat_key,
        "note": f"{character.name} SAVE vs {stat_key.upper()} {stat_mod:+d}{(f'+ {prof_bonus:+d}') if save_prof else ''} = {total} vs DC {dc} -> {'SUCCESS' if success else 'FAILURE'}"
    }


def describe_check(skill: str, context: str = "") -> str:
    """Get a flavor description of what a check means in-universe."""
    descriptions = {
        "athletics": "jumping, climbing, swimming, breaking things",
        "acrobatics": "balancing, escaping bonds, landing gracefully",
        "sleight_of_hand": "picking pockets, palming objects, card tricks",
        "arcana": "recalling magical lore, identifying spells",
        "history": "recalling historical events, lore, legends",
        "investigation": "finding hidden clues, analyzing evidence",
        "nature": "knowledge of terrain, beasts, plants, weather",
        "religion": "knowledge of gods, rites, holy symbols",
        "animal_handling": "calming beasts, riding, sensing animal intent",
        "insight": "reading intentions, detecting lies, sensing motives",
        "medicine": "healing wounds, diagnosing illness, stabilizing",
        "perception": "noticing details, spotting hidden things",
        "survival": "tracking, foraging, navigation, weather prediction",
        "deception": "lying convincingly, disguising, fast talk",
        "intimidation": "threatening, compelling, swaying through fear",
        "performance": "entertaining, music, acting, public speaking",
        "persuasion": "convincing, arguing fairly, negotiating"
    }
    base = descriptions.get(skill.lower().replace(" ", "_"), skill)
    return f"{context}: {base}" if context else base


if __name__ == "__main__":
    from bot.character_sheet import create_character
    c = create_character("Valdric", "fighter")
    c.proficiencies = ["athletics", "intimidation"]

    result = resolve_skill_check(c, "athletics", 15)
    print(result)

    result = resolve_save(c, "con", 12)
    print(result)
