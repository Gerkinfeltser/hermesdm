"""
state_manager.py — Campaign state persistence.
Saves/loads world state as JSON in ~/.hermes/hermesdm/campaigns/{id}/state.json
"""
import json
from pathlib import Path

CAMPAIGNS_DIR = Path.home() / ".hermes" / "hermesdm" / "campaigns"


def _ensure_dir(campaign_id: str) -> Path:
    campaign_dir = CAMPAIGNS_DIR / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    return campaign_dir


def _state_path(campaign_id: str) -> Path:
    return _ensure_dir(campaign_id) / "state.json"


def new_state(campaign_id: str, name: str, setting: str) -> dict:
    """
    Create a fresh campaign state.
    """
    state = {
        "campaign": {
            "id": campaign_id,
            "name": name,
            "setting": setting,
            "created": "",
            "current_location": None
        },
        "world": {},
        "npcs": {},
        "characters": {},
        "combat": {
            "active": False,
            "round": 0,
            "initiative": [],
            "current_turn": None
        },
        "quests": {
            "active": [],
            "completed": []
        },
        "history": [],
        "generated_images": []
    }
    return state


def save_state(campaign_id: str, state: dict) -> None:
    """
    Persist state to JSON file. Creates campaign dir if needed.
    """
    path = _state_path(campaign_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_state(campaign_id: str) -> dict | None:
    """
    Load campaign state from JSON. Returns None if not found.
    """
    path = _state_path(campaign_id)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def campaign_exists(campaign_id: str) -> bool:
    return _state_path(campaign_id).exists()


def list_campaigns() -> list[dict]:
    """
    List all campaigns (id, name, setting) sorted by most recent.
    """
    campaigns = []
    if not CAMPAIGNS_DIR.exists():
        return campaigns

    for campaign_dir in CAMPAIGNS_DIR.iterdir():
        if campaign_dir.is_dir():
            state_file = campaign_dir / "state.json"
            if state_file.exists():
                try:
                    with open(state_file, encoding="utf-8") as f:
                        data = json.load(f)
                    campaigns.append({
                        "id": data.get("campaign", {}).get("id", campaign_dir.name),
                        "name": data.get("campaign", {}).get("name", "Unnamed"),
                        "setting": data.get("campaign", {}).get("setting", "unknown")
                    })
                except Exception:
                    campaigns.append({
                        "id": campaign_dir.name,
                        "name": "Unnamed",
                        "setting": "unknown"
                    })

    # Sort by id descending (most recent first)
    campaigns.sort(key=lambda x: x["id"], reverse=True)
    return campaigns


def apply_world_change(campaign_id: str, key_path: str, value) -> dict:
    """
    Apply a world state change.
    key_path like "npcs.captain_vorn.status" or "world.main_threat"
    Returns updated state.
    """
    state = load_state(campaign_id)
    if state is None:
        raise ValueError(f"Campaign {campaign_id} not found")

    parts = key_path.split(".")
    current = state
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value

    save_state(campaign_id, state)
    return state


if __name__ == "__main__":
    print("=== state_manager sanity test ===")
    # Test new state
    state = new_state("test_001", "Test Campaign", "fantasy")
    print(f"New state created: {state['campaign']['id']}")

    save_state("test_001", state)
    print(f"Saved to {state['campaign']['id']}")

    loaded = load_state("test_001")
    print(f"Loaded: {loaded['campaign']['name']}")

    print(f"Campaigns: {list_campaigns()}")
