# HermesDM — Your AI Dungeon Master on Telegram

<p align="center">
<img width="1248" height="756" alt="hermes DM" src="https://github.com/user-attachments/assets/f0c94921-81df-4b68-95cf-a4e28e6fce13" />

> **What if your tabletop sessions never ended — because your AI Dungeon Master never slept, never forgot a detail, and always had the perfect encounter ready?**

[![D&D 5e](https://img.shields.io/badge/D%26D-5e-960020?style=flat-square)](https://dnd.wizards.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=fff)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-274%20%E2%9C%85-brightgreen?style=flat-square)](tests/)
[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=flat-square&logo=telegram&logoColor=fff)](https://t.me/)
[![Twitter](https://img.shields.io/badge/Author-@TheShugarBoy-1DA1F2?style=flat-square&logo=twitter&logoColor=fff)](https://twitter.com/TheShugarBoy)

</p>

---

## HermesDM is in advanced beta

The AI narrative engine, NPC system, and campaign infrastructure are production-ready. The complete D&D 5e mechanical layer is being actively finalized — we're building the foundation for an intelligent DM, not rushing out an incomplete game.

---

## TL;DR — What a Real Session Looks Like

```
🧙 Sherman → /create Valdric Wizard
⚔️ Valdric created! HP: 6 | AC: 13 | Slots: 4/4/3/3/3

🧙 Sherman → /j attack dragon
🎲 Attack roll... [d20+5 → 19+5=24] CRITICAL HIT!
   🔥 "Valdric pierces the ancient dragon's heart..."
   🖼️ [Auto-generated image]

🧙 Sherman → /cast fireball goblins
✨ Fireball! [8d6=38 damage] 3 goblins eliminated!
   🧙 Slots consumed: Lv3 → 2 remaining
```

**No Roll20, no D&D Beyond, no other apps. Just Telegram.** 📱

---

## Why HermesDM?

| | Roll20 | D&D Beyond | **HermesDM** |
|---|:---:|:---:|:---:|
| 💰 Cost | ~$10/mo | ~$15/mo | **Free** |
| 🎲 Real Dice | ⚠️ Manual | ⚠️ Manual | **Automatic** |
| 🧙 Spell Slots | ⚠️ Manual | ✅ Automatic | **✅ Automatic** |
| 🖼️ Images | ❌ None | ❌ None | **✅ Auto-generated** |
| 📱 On Telegram | ❌ No | ❌ No | **✅ 100% Telegram** |
| 💾 Persistence | ⚠️ Session | ⚠️ Session | **✅ Cross-session** |
| 🧠 LLM Narration | ❌ No | ❌ No | **✅ Yes** |

> **Spoiler:** HermesDM doesn't replace a table of friends. But if you play solo or with people who don't look like dice enthusiasts, it's a different story. 👀

---

## 🎮 Live Demo — Campaign: "The Dragon's Lair"

```
⏱️ Real session — Ancient Dragon combat (HP: 180, AC: 19)

🧙 Sherman → /join
⚔️ COMBAT STARTED: Valdric vs Ancient Dragon

🧙 Sherman → /j attack dragon (Advantage)
🎲 [2d20+7 → 18, 19+7=26] NATURAL 20! 💥
🔥 "Valdric delivers a devastating blow, the dragon crashing
   down from the sky in flames — dramatic cinematic battle scene"
🖼️ [MiniMax image → Telegram group]

💀 Sherman → HP: 12/68 (-56)
⚔️ Dragon's Turn → Breath Weapon [54 damage]
💀 Sherman → HP: 0/68 — GOES DOWN!
☠️  VALDRIC IS DEAD
🖼️ [Death image sent]

🎲 Death Save: 2 successes, 1 failure
💀 Valdric stabilized... barely.
```

---

## 🧠 How It Works — General Architecture

```
┌─────────────────────────────────────────────────────┐
│                    TELEGRAM                          │
│   Sherman types: /j attack dragon                  │
└─────────────────────┬───────────────────────────────┘
                      │ 📬 Polling (getUpdates)
                      ▼
┌─────────────────────────────────────────────────────┐
│              bot/telegram_handler.py                 │
│  1. Receives Telegram update                        │
│  2. Parses command (/j, /cast, /create...)        │
│  3. Delegates to corresponding module              │
└─────────────────────┬───────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌───────────┐
   │ combat_  │  │  spell_  │  │character_ │
   │ engine   │  │ manager  │  │  sheet    │
   └────┬────┘  └────┬─────┘  └─────┬─────┘
        │            │              │
        └────────────┼──────────────┘
                     ▼
        ┌────────────────────────┐
        │  adapters/mode_b/      │
        │  action_router.py      │
        │  → Classifies action   │
        │  → Unifies result      │
        └────────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐ ┌──────────┐ ┌──────────┐
   │  dice   │ │ narrative│ │ image_    │
   │ roller  │ │ generator│ │ event_h.. │
   └────┬────┘ └────┬────┘ └────┬─────┘
        │           │           │
        │           ▼           │
        │    ┌───────────┐      │
        │    │ LLM call  │      │
        │    │(narrative)│      │
        │    └─────┬─────┘      │
        │          │            │
        └──────────┴────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Image Provider         │
        │  (Pollinations/MiniMax/│
        │   Flux/NanoBanana/fal)  │
        └────────────┬───────────┘
                     │ ⏱️ +5 min cooldown
                     ▼
              ┌──────────────┐
              │  Telegram    │
              │  Bot sends   │
              │  photo       │
              └──────────────┘
```

---

## ✨ Features

| Feature | Status | Details |
|---------|:------:|---------|
| 🎲 **Real Dice** | ✅ | 1d4 → 1d20+, advantage, disadvantage, saves, crits |
| 📋 **Character Sheets** | ✅ | HP, XP, inventory, conditions, death saves |
| 🧙 **Spell Slots** | ✅ | Wizard, Cleric, Warlock, Paladin, Druid, Bard |
| 💀 **Persistent Death Saves** | ✅ | Survive bot restarts |
| 🧙 **NPCs with Memory** | ✅ | Notes, dialogue, cross-session memory |
| ⚔️ **Turn-based Combat** | ✅ | Initiative, attacks, damage, crits |
| 📖 **LLM Narration** | ✅ | Dynamic scenes based on genre |
| 🖼️ **Image Generation** | ✅ | Pollinations, MiniMax, Flux, NanoBanana, **fal.ai** |
| 💾 **JSON State** | ✅ | Persists across sessions in `~/.hermes/` |
| 🏰 **5 Campaign Genres** | ✅ | fantasy, dungeon, horror, tavern, scifi |
| 💬 **100% Telegram** | ✅ | No external apps needed |

---

## 🚀 Quick Start — Up in 2 Minutes

```bash
# 1. Clone and install
$ git clone https://github.com/Shugar03/hermesdm.git
$ cd hermesdm
$ pip install -e .

# 2. Configure tokens
$ cp .env.example .env
# ✏️  Edit .env and add:
#   TELEGRAM_BOT_TOKEN=***
#   MINIMAX_API_KEY=***  (optional, uses Pollinations if not set)

# 3. Run
$ hermesdm
# Or directly: python -m bot.telegram_handler

# 4. Open Telegram → search your bot → /start
```

### 🌐 Web Companion (optional)

Visual dashboard to view the game in a browser. Installed with a flag:

```bash
# Install bot + web companion
$ python3 scripts/install.py --group-id -1003916745496 --with-web

# Start bot
$ dm gateway start

# Start web (in another terminal)
$ hermesdm-web
# → http://localhost:8080
```

Or with Docker:

```bash
$ cd web && docker compose up -d
```

The web companion is **read-only** — shows characters, history, quests, and images in real time. It doesn't replace Telegram, it complements it.

### ⚙️ Requirements

| Requirement | Needed? | Where to get it |
|------------|:----------:|----------------|
| 🐍 **Python 3.12+** | ✅ Always | [python.org](https://www.python.org/) |
| 📱 **Telegram Bot Token** | ✅ Always | [@BotFather](https://t.me/BotFather) |
| 🎨 **MiniMax API Key** | ❌ Optional | [MiniMax](https://platform.minimaxi.com) — if not set, uses Pollinations (free) |
| 🔥 **fal.ai API Key** | ❌ Optional | [fal.ai/dashboard](https://fal.ai/dashboard) — FLUX.1 [dev], better quality/price |
| 🤖 **OpenAI Token** | ❌ Optional | [OpenAI](https://platform.openai.com/) — for richer LLM narration |

---

## 🎯 Command Guide

### 🏠 Setup & Start
| Command | Description |
|---------|-------------|
| `/start` | Welcome message and quick guide |
| `/setup <description>` | Create new campaign with AI (e.g.: `/setup dark fantasy in a corrupt port`) |
| `/newgame` | **DEPRECATED** — redirects to `/setup` |
| `/join <name> <class> [level]` | Create character and join campaign |
| `/begin` | **Start the adventure** — generates initial narrative scene |
| `/campaign` | View active campaign info |
| `/resume` | Resume last campaign |
| `/end` | End session — generates epilogue + image |
| `/quit` / `/exit` | Exit DM mode |
| `/audit [limit]` | View audit events (admin) |

### 👤 Character
| Command | Description |
|---------|-------------|
| `/status` | Your character summary (HP, AC, conditions) |
| `/hp` | Detailed HP info |
| `/inventory` | View inventory |
| `/give <character> <item> [qty]` | Transfer item to another player |

### ⚔️ Combat & Actions
| Command | Description |
|---------|-------------|
| `/j <action>` / `/attack <target> [adv\|dis]` | Attack or perform narrative action |
| `/cast <spell> [target]` | Cast spell (consumes slot) |
| `/skill <ability> <dc>` | Skill check |
| `/roll [dice]` | Roll dice (e.g.: `2d6+3`, `1d20+5`) |
| `/save` | Saving throw (delegated) |
| `/startcombat` / `/begincombat [enemy1] ...` | Start manual combat |
| `/endcombat` | End active combat |
| `/endturn` | Pass turn (with countdown) |

### 🧙 World & NPCs
| Command | Description |
|---------|-------------|
| `/talk <npc> <message>` | Talk to an NPC |
| `/npcs` | List persistent NPCs |
| `/npcsearch <query>` | Search NPCs by name/title |
| `/npcnote <name> <note>` | Add DM note about NPC |
| `/npcmemory <name> <key> <value>` | Register memory about NPC |
| `/map` | View current location |
| `/quests` | View active and completed quests |
| `/recap` | Story summary |

### 🖼️ Narration & Images
| Command | Description |
|---------|-------------|
| `/imagen` / `/image` | Generate image of current scene |
| `/me <action>` | Narrate action without rolling dice |
| `/countdown <seconds> <character>` | Countdown demo with progress bar |

### ❓ Help
| Command | Description |
|---------|-------------|
| `/help` | Full command list |

**Correct start flow:**
```
1. DM: /setup "I want a dark fantasy campaign..."
2. DM: "perfecto" (or "let's go", "yes", "ok")
3. Players: /join Valdric fighter 3
4. DM: /begin  ← Adventure starts with initial narrative!
5. Players: /j attack goblin
```

---

## 🌍 Campaign Genres

When you run `/newgame`, you choose a genre. Each has unique system prompts for the LLM:

| Genre | Vibe | Description |
|--------|------|-------------|
| 🏰 `fantasy` | Medieval | High fantasy adventures — dragons, magic, epic quests |
| 🗝️ `dungeon` | Exploration | Dungeons, puzzles, traps, hidden treasures |
| 🍺 `tavern` | Intrigue | Political missions from the tavern, social RPG |
| 👻 `horror` | Horror | Psychological horror, survival, dark creatures |
| 🚀 `scifi` | Space Opera | Sci-fi, cyberpunk, spaceships, rebel AIs |

---

## 🖼️ Automatic Image Generation

The DM generates images **automatically** at narratively important moments — without you asking.

### 🎯 Image Trigger Events

| Event | Image? | Why? |
|--------|:-------:|----------|
| 🎲 **Natural 20** (crit) | ✅ | Epic moment — it must be shown |
| 💀 **Natural 1** (fumble) | ✅ | Chaos and humor — LLM narrates the embarrassment |
| ☠️ **Character Death** | ✅ | Maximum emotional impact |
| 🐉 **Boss Combat** | ✅ | Every major hit is visually narrated |
| 🗺️ **New Location/NPC** | ✅ | Contextualizes the discovery |
| 🏁 **Session End** | ✅ | Visual epilogue of the moment |
| ❤️ **HP < 25%** | ✅ | Tension — moment of danger |
| 🎲 Normal Turn | ❌ | No spam — 5 min cooldown |

### 🔌 Supported Providers

| Provider | Quality | Speed | Cost | Notes |
|----------|:------:|:----------:|:-----:|-------|
| 🌸 **Pollinations** | Good ⭐⭐⭐ | ~1s | Free | Default, no API key needed |
| 🎨 **MiniMax** | Excellent ⭐⭐⭐⭐⭐ | ~10s | API key | Recommended for serious campaigns |
| ⚡ **Flux** | High ⭐⭐⭐⭐ | Variable | Local | Requires local server |
| 🍌 **NanoBanana** | ??? | ??? | ??? | Experimental |
| 🔥 **fal.ai** | High ⭐⭐⭐⭐⭐ | ~2-5s | API key | FLUX.1 [dev], best quality/price |

### ⚙️ Configuration

```yaml
# config.yaml
image_provider: "pollinations"   # default (free)
minimax_api_key: "your-key"    # optional
flux_endpoint: "http://localhost:7860"  # optional
fal_key: "your-fal-key"       # optional — https://fal.ai/dashboard
```

Or at runtime via `/settings image_provider fal`.

---

## 💾 Campaign State — Persistence

All state lives in `~/.hermes/hermesdm_state.json`:

```json
{
  "campaign_id": "uuid",
  "name": "The Dragon's Lair",
  "genre": "fantasy",
  "status": "active",
  "difficulty": "normal",
  "tone": "serious",
  "current_location": "Dark Forest",
  "image_provider": "pollinations",
  "auto_image_triggers": {
    "nat_20": true,
    "death": true,
    "boss_combat": true,
    "discovery": true,
    "session_end": true
  },
  "characters": {
    "Valdric": {
      "class": "Wizard",
      "level": 5,
      "hp": 28,
      "max_hp": 34,
      "ac": 13,
      "xp": 6500,
      "spell_slots": { "1": 4, "2": 3, "3": 3, "4": 1 },
      "inventory": ["Spellbook", "Staff"],
      "conditions": [],
      "death_saves": { "successes": 0, "failures": 0 }
    }
  },
  "npcs": {
    "Eldara": {
      "title": "The Witch",
      "description": "Ancient sorceress living in the swamp",
      "memory": { "met": "2024-03-15", "quest_given": "Find the crystal orb" }
    }
  },
  "combat": {
    "active": true,
    "turn": 2,
    "entities": []
  }
}
```

**Important:** If the bot crashes or restarts, state is recovered automatically. Death saves, HP, NPCs, and combat position are preserved. 💾

---

## 🏗️ Project Structure

```
hermesdm/
├── bot/                          # 🎮 Game logic (Telegram side)
│   ├── telegram_handler.py       # 🚪 Entry point — receives messages, routing
│   ├── character_sheet.py       # 📋 HP, XP, inventory, conditions, death saves
│   ├── combat_engine.py         # ⚔️ Initiative, attack, damage, crits
│   ├── diceRoller.py            # 🎲 Dice parsing and rolling
│   ├── skill_checks.py          # 🎯 Skill checks, saving throws
│   ├── spell_manager.py         # ✨ Spellcasting, damage, saves
│   └── monsters.py              # 👹 Monster definitions
│
├── dm/                           # 🧠 AI Engine (DM brain)
│   ├── narrative_generator.py   # 📖 LLM calls — narration and dialogue
│   ├── world_builder.py         # 🌍 World/NPC generation by genre
│   ├── image_provider.py        # 🖼️ ABC + Pollinations/MiniMax/Flux/NanoBanana
│   └── image_event_handler.py   # 🎬 Trigger logic + cooldown
│
├── adapters/mode_b/              # 🔀 Action abstraction layer
│   └── action_router.py         # → Classifies /j attack dragon → ActionResult
│
├── state/                        # 💾 Persistence
│   └── state_manager.py         # Read/write JSON, validate_state()
│
├── web/                          # 🌐 Visual dashboard (optional)
│   ├── server.py                # FastAPI — reads state.json, exposes API + SSE
│   ├── static/index.html        # UI vanilla JS — dark fantasy theme
│   ├── docker-compose.yml       # Docker one-liner
│   └── requirements.txt         # fastapi, uvicorn, sse-starlette
│
├── config.yaml                   # ⚙️ Bot configuration
├── .env.example                  # 🔑 Environment variables template
├── requirements.txt              # 📦 Python dependencies
│
└── tests/                        # 🧪 274 tests
    ├── test_combat_engine.py
    ├── test_character_sheet.py
    └── test_diceRoller.py
```

---

## 🛠️ Development

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=bot --cov=dm --cov=adapters

# Validate campaign state
python -c "from state.state_manager import validate_state; validate_state()"

# Lint with ruff
ruff check bot dm adapters

# Type check with mypy
mypy bot dm --ignore-missing-imports

# Verify config syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### 🔄 Contribution Flow

```
1. Fork → branch feat/my-feature
2. Hack away
3. ruff check + mypy --ignore-missing-imports
4. pytest tests/ -v (all green ✅)
5. PR → reviewers
6. Merge → CI runs ruff + mypy + pytest
```

---

## 🤝 Author

<p align="center">
<strong>Sherman</strong> — [@TheShugarBoy](https://twitter.com/TheShugarBoy) 🐦
<br/>

Built with Python 🐍, Telegram Bots API, and Kimi k2.6.
</p>

<p align="center">
Found a bug? 🐛 Open an [issue](https://github.com/Shugar03/hermesdm/issues) or DM me on [Twitter](https://twitter.com/TheShugarBoy).

---

## 📜 License

MIT — use it, modify it, share it. If you use it for something cool, send me a message and tell me about it. 🎲
