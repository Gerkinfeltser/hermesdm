"""
turn_manager.py — Combat initiative and turn tracking.
Manages initiative order, current turn, round counter.
"""
from dataclasses import dataclass, field

from bot.dice_engine import roll


@dataclass
class Combatant:
    name: str
    initiative: int
    is_player: bool
    is_active: bool = True
    delayed: bool = False
    held: bool = False  # Delay action


@dataclass
class CombatState:
    active: bool = False
    round: int = 0
    initiative_order: list = field(default_factory=list)  # list[Combatant]
    current_index: int = 0
    current_turn: str | None = None
    started: bool = False

    def current_combatant(self) -> Combatant | None:
        if 0 <= self.current_index < len(self.initiative_order):
            return self.initiative_order[self.current_index]
        return None

    def next_index(self) -> int:
        return (self.current_index + 1) % len(self.initiative_order)

    def is_last_turn(self) -> bool:
        return self.current_index == len(self.initiative_order) - 1


def roll_initiative(name: str, dex_mod: int) -> int:
    """Roll initiative: d20 + dex mod."""
    r = roll("d20")
    total = r["rolls"][0] + dex_mod
    return total


def start_combat(participants: list[dict]) -> CombatState:
    """
    Start combat. participants: list of {name, is_player, dex_mod}.
    Returns CombatState with initiative ordered high -> low.
    """
    combatants = []
    for p in participants:
        initiative = roll_initiative(p["name"], p.get("dex_mod", 0))
        combatants.append(Combatant(
            name=p["name"],
            initiative=initiative,
            is_player=p.get("is_player", True),
            is_active=True
        ))

    # Sort high -> low
    combatants.sort(key=lambda c: c.initiative, reverse=True)

    state = CombatState(
        active=True,
        round=1,
        initiative_order=combatants,
        current_index=0,
        current_turn=combatants[0].name if combatants else None,
        started=True
    )
    return state


def next_turn(state: CombatState) -> dict:
    """
    Advance to next turn. Handles round increment.
    Returns {who, next_up, round, note}
    """
    if not state.active:
        return {"error": "Combat not active", "state": state}

    # Check if we're done with current combatant (handles held/delayed)
    current = state.current_combatant()
    if current and current.held:
        current.held = False

    # Move to next active combatant
    max_iterations = len(state.initiative_order)
    for _ in range(max_iterations):
        state.current_index = state.next_index()
        next_c = state.current_combatant()
        if next_c and next_c.is_active and not next_c.delayed:
            state.current_turn = next_c.name
            break
    else:
        # All delayed or inactive — end combat
        state.active = False
        state.current_turn = None
        return {"error": "No active combatants", "state": state}

    # Check if we wrapped around to round 1
    new_round = state.round
    note = f"{state.current_turn}'s turn (Initiative: {state.current_combatant().initiative})"

    if state.is_last_turn():
        new_round = state.round + 1
        state.round = new_round
        note += f" -- Round {new_round} begins!"

    return {
        "who": state.current_turn,
        "round": state.round,
        "note": note,
        "state": state
    }


def delay(state: CombatState, name: str) -> dict:
    """
    Delay: current combatant delays, re-rolls initiative at lower priority.
    Re-inserts at current position - 1.
    """
    current = state.current_combatant()
    if not current or current.name != name:
        return {"error": f"{name} is not the current combatant"}

    current.delayed = True
    old_index = state.current_index

    # Remove from current position
    state.initiative_order.remove(current)
    # Re-insert at end of round
    state.initiative_order.append(current)

    if old_index >= len(state.initiative_order):
        state.current_index = len(state.initiative_order) - 1
    else:
        # Stay at same index (next in order advances)
        pass

    return {
        "note": f"{name} delays. Re-inserted at end of round.",
        "state": state
    }


def remove_combatant(state: CombatState, name: str) -> dict:
    """Remove a combatant (dead/unconscious)."""
    for i, c in enumerate(state.initiative_order):
        if c.name == name:
            c.is_active = False
            state.initiative_order.remove(c)
            if state.current_index >= i and state.current_index > 0:
                state.current_index -= 1
            return {"note": f"{name} removed from combat.", "state": state}
    return {"error": f"{name} not found in combat", "state": state}


def end_combat(state: CombatState) -> CombatState:
    state.active = False
    state.round = 0
    state.current_turn = None
    state.initiative_order = []
    state.current_index = 0
    return state


def combat_summary(state: CombatState) -> str:
    """Text summary of current combat state."""
    if not state.active:
        return "No active combat."

    lines = [f"Round {state.round} — {state.current_turn}'s turn"]
    lines.append("Initiative order:")
    for i, c in enumerate(state.initiative_order):
        marker = " <<" if i == state.current_index else ""
        status = " (inactive)" if not c.is_active else ""
        lines.append(f"  {c.initiative:3d} — {c.name}{marker}{status}")

    return "\n".join(lines)


if __name__ == "__main__":
    participants = [
        {"name": "Valdric", "is_player": True, "dex_mod": 1},
        {"name": "Mira", "is_player": True, "dex_mod": 2},
        {"name": "Goblin Chief", "is_player": False, "dex_mod": 2},
    ]
    state = start_combat(participants)
    print(combat_summary(state))
    print("---")
    for _ in range(6):
        r = next_turn(state)
        print(r["note"])
