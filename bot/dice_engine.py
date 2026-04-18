"""
dice_engine.py — Pure dice rolling and check resolution.
No narrative, no LLM — pure game mechanics.
"""
import random
import re


class DiceError(Exception):
    pass


def roll(dice_str: str) -> dict:
    """
    Roll dice from string notation like "2d6+3", "1d20+5", "d20", "4d6".
    Returns {total, rolls, modifier, natural, is_crit, is_fumble}
    """
    dice_str = dice_str.strip().lower()

    # Default to d20 if just a number or nothing
    if not dice_str:
        dice_str = "d20"

    # Parse modifier
    modifier = 0
    mod_match = re.search(r'([+-]\d+)$', dice_str)
    if mod_match:
        modifier = int(mod_match.group(1))
        dice_str = dice_str[:mod_match.start()]

    # Parse dice count and sides
    match = re.match(r'^(\d*)d(\d+)$', dice_str)
    if not match:
        raise DiceError(f"Invalid dice notation: '{dice_str}'")

    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))

    if count < 1 or count > 100:
        raise DiceError(f"Dice count must be 1-100, got {count}")
    if sides < 2 or sides > 100:
        raise DiceError(f"Sides must be 2-100, got {sides}")

    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + modifier

    natural = None
    is_crit = False
    is_fumble = False

    if count == 1 and sides == 20:
        natural = rolls[0]
        is_crit = (natural == 20)
        is_fumble = (natural == 1)

    return {
        "total": total,
        "rolls": rolls,
        "modifier": modifier,
        "natural": natural,
        "is_crit": is_crit,
        "is_fumble": is_fumble,
        "notation": dice_str,
        "str": str(dice_str) + (f"{modifier:+d}" if modifier else "")
    }


def resolve_check(
    roll_result: dict,
    dc: int,
    advantage: bool = False,
    disadvantage: bool = False
) -> dict:
    """
    Resolve a check/roll against a Difficulty Class.
    Returns {success, margin, roll, dc, rolls, note}
    """
    if advantage and disadvantage:
        advantage = False
        disadvantage = False

    rolls = roll_result["rolls"]
    total = roll_result["total"]

    if advantage and len(rolls) == 1:
        # Roll twice, take higher
        r1, r2 = rolls[0], random.randint(1, 20)
        total = max(r1, r2) + roll_result["modifier"]
        rolls = [r1, r2]
    elif disadvantage and len(rolls) == 1:
        r1, r2 = rolls[0], random.randint(1, 20)
        total = min(r1, r2) + roll_result["modifier"]
        rolls = [r1, r2]

    margin = total - dc
    success = total >= dc

    note = ""
    if roll_result.get("is_crit"):
        note = "NATURAL 20! Critical success!"
    elif roll_result.get("is_fumble"):
        note = "NATURAL 1! Critical failure!"
    elif success and margin >= dc:
        note = f"Success by {margin}"
    elif success:
        note = f"Success by {margin}"
    else:
        note = f"Failure by {abs(margin)}"

    return {
        "success": success,
        "margin": margin,
        "total": total,
        "dc": dc,
        "rolls": rolls,
        "note": note
    }


if __name__ == "__main__":
    # Quick sanity test
    print("=== dice_engine sanity test ===")
    r = roll("2d6+3")
    print(f"Roll 2d6+3: {r}")

    r20 = roll("1d20+5")
    print(f"Roll 1d20+5: {r20}")

    check = resolve_check(r20, dc=15)
    print(f"Resolve vs DC15: {check}")

    check_adv = resolve_check(r20, dc=15, advantage=True)
    print(f"Resolve vs DC15 with advantage: {check_adv}")
