"""
world_builder.py — Generate a new campaign world on /newgame.
Creates setting, starting location, and 2-3 NPCs.
No game mechanics here — pure world generation.
"""
import random
import uuid
from datetime import datetime

from state.state_manager import new_state, save_state

# ---- World templates ----

SETTINGS = {
    "fantasy": {
        "name": "The Kingdom of Valdris",
        "description": (
            "A realm scarred by a war that ended a decade ago. The old king's death "
            "remains shrouded in mystery, and whispers of a returning dragon "
            "have begun to spread from the northern settlements."
        ),
        "starting_location": "The Rusty Anchor Tavern",
        "starting_location_desc": (
            "A weathered tavern at the edge of the capital. Firelight flickers "
            "across worn wooden tables, and the smell of ale and woodsmoke fills the air. "
            "A hooded stranger nurses a drink in the corner."
        ),
        "factions": {
            "royal_guard": "SHADOWED",
            "thieves_guild": "RISING",
            "templars": "DOMINANT"
        },
        "main_threat": "Unknown — rumors of dragon attacks in the north"
    },
    "scifi": {
        "name": "Nexus Station",
        "description": (
            "A massive space station at the crossroads of three trade routes. "
            "Corporate factions compete for control while smuggler crews "
            "slip through the station's labyrinthine docking bays."
        ),
        "starting_location": "The Drift Bar",
        "starting_location_desc": (
            "A dimly lit bar spinning in the station's outer ring. "
            "Holographic ads flicker above the counter, and the hum of "
            "the station's life support is a constant reminder of the void outside."
        ),
        "factions": {
            "megacorp": "DOMINANT",
            "syndicate": "RISING",
            "free_merchants": "WEEKEND"
        },
        "main_threat": "Corporate espionage and missing cargo shipments"
    },
    "horror": {
        "name": "Ravenhollow Manor",
        "description": (
            "A fog-shrouded coastal town where the locals speak in whispers. "
            "The old manor on the hill has been abandoned for fifty years, "
            "but lately its windows glow at night."
        ),
        "starting_location": "The Sailor's Rest Inn",
        "starting_location_desc": (
            "A cramped inn near the harbor. The floorboards creak with each step, "
            "and the fireplace casts long, shifting shadows. The innkeeper "
            "refuses to look out the window after dark."
        ),
        "factions": {
            "town_council": "CORRUPT",
            "cultists": "HIDDEN",
            "fishermen": "FRIGHTENED"
        },
        "main_threat": "Something in the manor — unknown and growing"
    }
}


NPC_TEMPLATES = [
    {
        "name": "Captain Vorn",
        "role": "Retired soldier",
        "disposition": "Cautious",
        "location": "tavern",
        "race": "human",
        "appearance": "Grizzled man with a scarred jaw and watchful eyes",
        "secret": "Deserted the royal guard after the old king's death",
        "goals": ["Protect the innocent", "Find the truth about the old king"]
    },
    {
        "name": "Mira the Wise",
        "role": "Scholar",
        "disposition": "Friendly",
        "location": "tavern",
        "race": "elf",
        "appearance": "Silver-haired elf with ancient eyes and ink-stained fingers",
        "secret": "Knows what really happened to the old king",
        "goals": ["Protect ancient knowledge", "Guide worthy adventurers"]
    },
    {
        "name": "Jax the Quick",
        "role": "Thief",
        "disposition": "Sarcastic",
        "location": "tavern",
        "race": "halfling",
        "appearance": "Quick-footed halfling with a grin that's always calculating",
        "secret": "Owes a debt to the thieves guild — dangerous to be seen with her",
        "goals": ["Survive", "Get rich", "Pay off the debt"]
    },
    {
        "name": "Brother Aldric",
        "role": "Templar priest",
        "disposition": "Righteous",
        "location": "town",
        "race": "dwarf",
        "appearance": "Broad-shouldered dwarf in temple armor, holy symbol visible",
        "secret": "His order is corrupt — he's the only honest one left",
        "goals": ["Serve the light", "Reform his order from within"]
    },
    {
        "name": "Sera Nightshade",
        "role": "Mysterious stranger",
        "disposition": "Enigmatic",
        "location": "tavern",
        "race": "tiefling",
        "appearance": "Pale tiefling with dark eyes and a serpentine smile",
        "secret": "Works for the thieves guild — sent to assess the party",
        "goals": ["Complete her mission", "Keep her employers happy"]
    }
]


def generate_npcs(count: int = 3) -> dict:
    """Generate N random NPCs from templates."""
    chosen = random.sample(NPC_TEMPLATES, min(count, len(NPC_TEMPLATES)))
    npcs = {}
    for tmpl in chosen:
        npc_id = tmpl["name"].lower().replace(" ", "_")
        npcs[npc_id] = {
            "name": tmpl["name"],
            "role": tmpl["role"],
            "status": "ALIVE",
            "location": tmpl["location"],
            "disposition": tmpl["disposition"],
            "race": tmpl["race"],
            "disposition_value": 0,  # -100 hostile to +100 friendly
            "relationship_to_party": "stranger",
            "memory": [],
            "goals": tmpl["goals"],
            "mood": tmpl["disposition"].lower(),
            "appearance": tmpl["appearance"],
            "secret": tmpl["secret"],
            "dialogue_style": _get_dialogue_style(tmpl["disposition"])
        }
    return npcs


def _get_dialogue_style(disposition: str) -> str:
    styles = {
        "Cautious": "Speaks carefully, answers questions with questions",
        "Friendly": "Warm and open, asks about the party's travels",
        "Sarcastic": "Quick with a joke, never takes anything seriously",
        "Righteous": "Speaks with conviction, judges actions",
        "Enigmatic": "Talks in riddles, reveals only what serves her"
    }
    return styles.get(disposition, "Normal and direct")


def build_world(setting: str = "fantasy") -> dict:
    """
    Generate a complete new campaign world.
    Returns a full state dict ready to be saved.
    """
    if setting not in SETTINGS:
        setting = "fantasy"

    tmpl = SETTINGS[setting]
    campaign_id = f"campaign_{uuid.uuid4().hex[:8]}"
    created = datetime.now().strftime("%Y-%m-%d")

    # Base state
    state = new_state(campaign_id, tmpl["name"], setting)
    state["campaign"]["created"] = created
    state["campaign"]["current_location"] = tmpl["starting_location"]

    # World
    state["world"] = {
        "main_threat": tmpl["main_threat"],
        "factions": tmpl["factions"],
        "description": tmpl["description"],
        "timeline": []
    }

    # Location
    state["world"]["locations"] = {
        tmpl["starting_location"]: {
            "description": tmpl["starting_location_desc"],
            "NPCs": [],
            "visited": True
        }
    }

    # NPCs
    npcs = generate_npcs(count=3)
    state["npcs"] = npcs

    # Link NPCs to starting location
    for npc_id in npcs:
        if npcs[npc_id]["location"] == "tavern":
            if tmpl["starting_location"] not in state["world"]["locations"]:
                state["world"]["locations"][tmpl["starting_location"]] = {"description": tmpl["starting_location_desc"], "NPCs": [], "visited": True}
            state["world"]["locations"][tmpl["starting_location"]]["NPCs"].append(npc_id)

    # Starting history entry
    state["history"].append({
        "session": 1,
        "event": f"Campaign created: {tmpl['name']}. Party meets at {tmpl['starting_location']}.",
        "timestamp": created
    })

    return state


def create_campaign(setting: str = "fantasy") -> dict:
    """
    High-level function: build world + persist to disk.
    Returns the campaign_id and state.
    """
    state = build_world(setting)
    campaign_id = state["campaign"]["id"]
    save_state(campaign_id, state)
    return {"campaign_id": campaign_id, "state": state}


if __name__ == "__main__":
    print("=== world_builder sanity test ===")
    result = create_campaign("fantasy")
    cid = result["campaign_id"]
    state = result["state"]
    print(f"Campaign: {cid}")
    print(f"Name: {state['campaign']['name']}")
    print(f"Setting: {state['campaign']['setting']}")
    print(f"Location: {state['campaign']['current_location']}")
    print(f"NPCs: {list(state['npcs'].keys())}")
    print(f"Factions: {state['world']['factions']}")
