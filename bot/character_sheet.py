"""
character_sheet.py — Player character definition.
Stats, HP, AC, inventory, conditions, death saves.
"""
from dataclasses import dataclass, field

# D&D 5e stat array (1-20, 10=human baseline)
STATS = ["str", "dex", "con", "int", "wis", "cha"]

SKILL_BY_STAT = {
    "str": ["athletics"],
    "dex": ["acrobatics", "sleight_of_hand", "stealth"],
    "con": [],
    "int": ["arcana", "history", "investigation", "nature", "religion"],
    "wis": ["animal_handling", "insight", "medicine", "perception", "survival"],
    "cha": ["deception", "intimidation", "performance", "persuasion"]
}

ALL_SKILLS = []
for skills in SKILL_BY_STAT.values():
    ALL_SKILLS.extend(skills)


@dataclass
class HP:
    max: int = 10
    current: int = 10
    temp: int = 0

    def apply_damage(self, dmg: int) -> int:
        """Apply damage. Returns actual HP lost (accounts for temp)."""
        total = self.current + self.temp
        remaining = total - dmg
        if remaining < 0:
            remaining = 0
        actual_loss = total - remaining
        # Distribute: temp absorbs first, then current
        original_temp = self.temp
        self.temp = max(0, self.temp - dmg)
        excess = max(0, dmg - original_temp)  # damage that exceeded original temp
        self.current = max(0, self.current - excess)
        return actual_loss

    def heal(self, amount: int) -> int:
        if self.current >= self.max:
            return 0
        old = self.current
        self.current = min(self.max, self.current + amount)
        return self.current - old

    def apply_temp_hp(self, amount: int) -> None:
        self.temp = max(self.temp, amount)


@dataclass
class DeathSaves:
    successes: int = 0
    failures: int = 0

    def reset(self) -> None:
        self.successes = 0
        self.failures = 0


# Valid conditions
VALID_CONDITIONS = {
    "blinded", "charmed", "deafened", "frightened", "grappled",
    "incapacitated", "invisible", "paralyzed", "petrified", "poisoned",
    "prone", "restrained", "stunned", "unconscious", "exhaustion"
}


@dataclass
class Item:
    name: str
    quantity: int = 1
    description: str = ""
    equipped: bool = False


@dataclass
class Character:
    name: str
    player_class: str  # fighter, wizard, rogue, cleric, ranger, barbarian
    level: int = 1
    stats: dict = field(default_factory=lambda: {
        "str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10
    })
    hp: HP = field(default_factory=HP)
    ac: int = 10
    proficiencies: list = field(default_factory=list)  # skills[] + saving_throws[]
    inventory: list = field(default_factory=list)  # Item[]
    conditions: list = field(default_factory=list)  # condition names
    death_saves: DeathSaves = field(default_factory=DeathSaves)
    proficiency_bonus: int = 2
    inventory_slots: int = 10
    equipped_weapon: str | None = None
    equipped_armor: str | None = None

    def mod(self, stat: str) -> int:
        """Modifier for a stat (floor((stat-10)/2))."""
        return (self.stats.get(stat, 10) - 10) // 2

    def mod_str(self, stat: str) -> str:
        m = self.mod(stat)
        return f"{m:+d}"

    def ac_with_dex(self) -> int:
        """AC = 10 + dex mod (basic, no armor)."""
        return 10 + self.mod("dex")

    def is_proficient(self, skill_or_save: str) -> bool:
        return skill_or_save in self.proficiencies

    def attack_bonus(self) -> int:
        """Base attack bonus = strength/dex mod + proficiency (if weapon is proficient)."""
        return self.mod("str")  # Simplified: uses STR for all weapons

    def save_dc(self) -> int:
        """Spell save DC = 8 + prof + mod."""
        return 8 + self.proficiency_bonus + self.mod("int")

    def add_condition(self, cond: str) -> None:
        if cond.lower() in VALID_CONDITIONS:
            self.conditions.append(cond.lower())

    def remove_condition(self, cond: str) -> None:
        if cond.lower() in self.conditions:
            self.conditions.remove(cond.lower())

    def add_item(self, item: Item) -> None:
        # Stack if exists
        for existing in self.inventory:
            if existing.name == item.name:
                existing.quantity += item.quantity
                return
        if len(self.inventory) < self.inventory_slots:
            self.inventory.append(item)

    def remove_item(self, name: str, qty: int = 1) -> bool:
        for item in self.inventory:
            if item.name == name:
                item.quantity -= qty
                if item.quantity <= 0:
                    self.inventory.remove(item)
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "class": self.player_class,
            "level": self.level,
            "stats": self.stats,
            "hp": {"max": self.hp.max, "current": self.hp.current, "temp": self.hp.temp},
            "ac": self.ac,
            "proficiencies": self.proficiencies,
            "inventory": [{"name": i.name, "qty": i.quantity, "desc": i.description} for i in self.inventory],
            "conditions": self.conditions,
            "death_saves": {"successes": self.death_saves.successes, "failures": self.death_saves.failures},
            "equipped_weapon": self.equipped_weapon,
            "equipped_armor": self.equipped_armor
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        hp = HP(max=data["hp"]["max"], current=data["hp"]["current"], temp=data["hp"].get("temp", 0))
        ds = DeathSaves(
            successes=data.get("death_saves", {}).get("successes", 0),
            failures=data.get("death_saves", {}).get("failures", 0)
        )
        inv = [Item(name=i["name"], quantity=i["qty"], description=i.get("desc", "")) for i in data.get("inventory", [])]
        c = cls(
            name=data["name"],
            player_class=data["class"],
            level=data["level"],
            stats=data["stats"],
            hp=hp,
            ac=data["ac"],
            proficiencies=data.get("proficiencies", []),
            inventory=inv,
            conditions=data.get("conditions", []),
            death_saves=ds,
            equipped_weapon=data.get("equipped_weapon"),
            equipped_armor=data.get("equipped_armor")
        )
        return c


# ---- Class definitions ----

CLASS_DEFINITIONS = {
    "fighter": {
        "hit_die": 10,
        "primary_stat": "str",
        "skills": ["athletics", "history", "insight", "perception", "survival"],
        "num_skills": 2,
        "proficiency_bonus": 2,
        "features": ["Fighting Style", "Second Wind (1d10+level extra HP)"],
        "spellcasting": False
    },
    "wizard": {
        "hit_die": 6,
        "primary_stat": "int",
        "skills": ["arcana", "history", "insight", "medicine", "religion"],
        "num_skills": 2,
        "proficiency_bonus": 2,
        "features": ["Spellcasting (INT)", "Arcane Recovery"],
        "spellcasting": True
    },
    "rogue": {
        "hit_die": 8,
        "primary_stat": "dex",
        "skills": ["acrobatics", "athletics", "deception", "insight", "intimidation", "investigation", "perception", "performance", "persuasion", "sleight_of_hand", "stealth"],
        "num_skills": 4,
        "proficiency_bonus": 2,
        "features": ["Sneak Attack (1d6)", "Cunning Action"],
        "spellcasting": False
    },
    "cleric": {
        "hit_die": 8,
        "primary_stat": "wis",
        "skills": ["history", "insight", "medicine", "persuasion", "religion"],
        "num_skills": 2,
        "proficiency_bonus": 2,
        "features": ["Spellcasting (WIS)", "Divine Domain"],
        "spellcasting": True
    },
    "ranger": {
        "hit_die": 10,
        "primary_stat": "dex",
        "secondary_stat": "wis",
        "skills": ["animal_handling", "athletics", "insight", "investigation", "nature", "perception", "stealth", "survival"],
        "num_skills": 3,
        "proficiency_bonus": 2,
        "features": ["Favored Enemy", "Natural Explorer"],
        "spellcasting": True
    },
    "barbarian": {
        "hit_die": 12,
        "primary_stat": "str",
        "secondary_stat": "con",
        "skills": ["animal_handling", "athletics", "insight", "intimidation", "nature", "perception", "survival"],
        "num_skills": 2,
        "proficiency_bonus": 2,
        "features": ["Rage (2/resting, +2 damage)", "Reckless Attack"],
        "spellcasting": False
    }
}


def create_character(name: str, player_class: str, level: int = 1, stat_array: dict | None = None) -> Character:
    """Factory: create a level-1 character with standard array or provided stats."""
    cls_def = CLASS_DEFINITIONS.get(player_class.lower(), CLASS_DEFINITIONS["fighter"])
    hp = HP(max=cls_def["hit_die"], current=cls_def["hit_die"])

    stats = stat_array or {
        "str": 15, "dex": 14, "con": 13, "int": 12, "wis": 10, "cha": 8
    }

    char = Character(
        name=name,
        player_class=player_class.lower(),
        level=level,
        stats=stats,
        hp=hp,
        ac=10,  # Will be recalculated with armor
        proficiencies=[],  # User picks skills
        inventory_slots=10 + (level // 2)
    )
    char.proficiency_bonus = 2 + (level - 1) // 4
    return char


if __name__ == "__main__":
    c = create_character("Valdric", "fighter", level=1)
    print(f"Character: {c.name} ({c.player_class})")
    print(f"HP: {c.hp.current}/{c.hp.max}")
    print(f"AC: {c.ac_with_dex()}")
    print(f"Stats: { {s: c.mod_str(s) for s in STATS} }")
    print(f"Attack bonus: {c.attack_bonus():+d}")
