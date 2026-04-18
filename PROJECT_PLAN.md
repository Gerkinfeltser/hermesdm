# HermesDM — AI Dungeon Master Multiplayer
## HACKATHON PROJECT — Hermes Agent Creative Hackathon ($25k, 16 días)

---

## 1. CONCEPTO

**Nombre:** HermesDM
**Pitch:** "Un Dungeon Master narrativo persistente que existe en un grupo de Telegram donde hasta 6 jugadores juegan por turnos, tiran dados reales, y el mundo responde y evoluciona sin que nadie lo maneje."
**Diferenciación:** Único AI DM con mecánicas de juego reales + dados + multiplayer + persistencia + narrativa procedural + generación de imágenes en momentos clave.
**Stack base:** Hermes Agent + Python + Telegram Bot + SQLite/JSON + MiniMax Image Gen

---

## 2. ARQUITECTURA GENERAL

```
┌──────────────────────────────────────────────────────┐
│              TELEGRAM (interfaz jugador)              │
│  /newgame /roll /attack /status /talk /inventory     │
└─────────────────────┬────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────┐
│              GAME ENGINE (Python)                     │
│  ├── dice_engine.py       → roll, resolve_check      │
│  ├── combat_engine.py     → resolve_attack, spells   │
│  ├── skill_checks.py      → ability/skill resolution │
│  ├── character_sheet.py   → HP, stats, inventory     │
│  ├── turn_manager.py      → whose_turn, timer        │
│  ├── state_validator.py   → previene state drift     │
│  └── state_manager.py     → load/save campaign JSON  │
└─────────────────────┬────────────────────────────────┘
                      │ JSON state (source of truth)
┌─────────────────────▼────────────────────────────────┐
│           HERMES DM (LLM Brain)                       │
│  ├── system_prompt.md      → identity + rules + style│
│  ├── narrative_generator.py → scene → prose          │
│  ├── world_builder.py      → generate setting/NPCs  │
│  ├── scene_classifier.py   → detecta momento visual  │
│  └── image_prompt_builder.py → state → SD prompt     │
└──────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────┐
│           IMAGE PIPELINE (async)                      │
│  MiniMax image gen → genera en background            │
│  → manda al grupo 30-90s después sin bloquear juego  │
└──────────────────────────────────────────────────────┘
```

---

## 3. MÓDULOS DEL GAME ENGINE

### 3.1 dice_engine.py
```python
roll("2d6+3") → {total, rolls[], modifier, natural, is_crit, is_fumble}
resolve_check(roll, dc, advantage, disadvantage) → {success, margin}
```

### 3.2 combat_engine.py
```python
resolve_attack(attacker, defender, attack_roll) → {hit, crit, damage, effect}
apply_damage(character, damage) → update HP, check death saves
resolve_spell(caster, spell, targets) → area effect resolution
```

### 3.3 skill_checks.py
```python
# 6 stats: STR DEX CON INT WIS CHA
# Skills por stat (5e-style)
resolve_skill_check(player, skill, dc, advantage, disadvantage) → {success, narrative_cue}
resolve_save(player, stat, dc) → {success}
```

### 3.4 character_sheet.py
```python
# Stats: STR DEX CON INT WIS CHA (cada una 1-20, 10=human baseline)
# HP: max_hp, current_hp, temp_hp
# AC: armor + dex modifier
# Death saves: 3 successes, 3 failures
# Conditions: [prone, stunned, poisoned, etc]
# Inventory: [{item, quantity, description}]
# Proficiencies: [skills[], saving_throws[], tools[]]
```

### 3.5 turn_manager.py
```python
start_combat(participants[]) → initiative order
next_turn() → whose turn, timer countdown
player_action(player, action, target) → validate → execute
npc_action(npc) → DM decides → execute
```

### 3.6 state_manager.py
```python
# Archivo JSON por campaign en ~/.hermes/hermesdm/campaigns/{id}/
save_state(campaign_id, state)
load_state(campaign_id) → full state
apply_world_change(event) → update world state
get_active_npcs() → with memory + disposition
get_party_status() → all characters HP/conditions
```

### 3.7 state_validator.py
```python
# Previene inconsistencies del LLM
validate_action(action, current_state) → allowed/blocked
enforce_world_consistency(narrative) → corrige contradictions
```

---

## 4. WORLD STATE STRUCTURE

```json
{
  "campaign": {
    "id": "valdris_001",
    "name": "El Reino de Valdris",
    "setting": "medieval fantasy",
    "created": "2026-04-17",
    "current_location": "Darkwood Forest",
    "world_timeline": ["killed_king aldric", "dragon_attack_north"]
  },
  "world": {
    "king": "DEAD",
    "main_threat": "Dragon assault Northern settlements",
    "factions": {
      "royal_guard": "DISBANDED",
      "thieves_guild": "RISING"
    }
  },
  "npcs": {
    "captain_vorn": {
      "status": "ALIVE",
      "location": "capital",
      "disposition": "HOSTILE",
      "relationship_to_party": "sworn_enemies",
      "memory": ["session_3: party stole from him", "session_5: valdric attacked him"],
      "goals": ["protect_capital", "arrest_valdric"],
      "mood": "furious"
    },
    "mira_the_wise": {
      "status": "ALIVE",
      "location": "darkwood_shrine",
      "disposition": "FRIENDLY",
      "relationship_to_party": "grateful",
      "memory": ["session_2: party saved her from bandits"],
      "goals": ["protect_ancient_knowledge"],
      "mood": "grateful"
    }
  },
  "characters": {
    "valdric": {
      "id": "player_1",
      "class": "fighter",
      "level": 3,
      "hp": { "current": 24, "max": 30 },
      "ac": 18,
      "stats": { "str": 16, "dex": 12, "con": 14, "int": 10, "wis": 13, "cha": 8 },
      "skills": ["athletics", "intimidation"],
      "inventory": [{ "name": "Longsword +1", "quantity": 1 }],
      "conditions": [],
      "death_saves": { "successes": 0, "failures": 0 }
    }
  },
  "combat": {
    "active": true,
    "round": 3,
    "initiative": ["valdric", "goblin_chief", "mira_the_wise"],
    "current_turn": "goblin_chief"
  },
  "quests": {
    "active": [
      { "id": "recover_princess", "status": "in_progress", "objective": "Find Princess in dragon's lair" }
    ],
    "completed": ["save_mira", "escape_prison"]
  },
  "history": [
    { "session": 1, "summary": "Party met in tavern, accepted quest to find Princess" },
    { "session": 2, "summary": "Saved Mira from bandits in Darkwood" }
  ],
  "generated_images": [
    { "session": 2, "prompt": "fighter_and_elf...", "timestamp": "..." }
  ]
}
```

---

## 5. NARRATIVE SYSTEM

### 5.1 DM System Prompt Structure
```
[SYSTEM IDENTITY]
You are HermesDM, an expert AI Dungeon Master running a D&D 5e campaign.
Personality: vivid describer, dramatic timing, rules-aware, collaborative.

[GAME RULES]
- State DC before asking for rolls
- When player rolls, state result AND consequence
- Track HP changes explicitly
- Apply advantage/disadvantage

[WORLD STATE — inject from JSON]
[Current location, NPCs present, party status]

[CHARACTER SHEETS — all players]
[Each player's stats, HP, inventory, conditions]

[INSTRUCTION]
Describe in 2-4 sentences. End with an open question or situation.
Do NOT ask "what do you want to do?" — instead present a SITUATION.
```

### 5.2 Scene Types
```
EXPLORATION → Player describes action → skill check → consequence
COMBAT → Turn-based → attack/skill/spell → damage → next turn
DIALOGUE → Player interacts with NPC → social check → NPC response
STORY_BEAT → DM narrates revelation → party reacts → consequences
REST → Downtime → heal, shop, train → world time advances
```

### 5.3 Drama Management (STAGE Framework)
```
Tension Arc: picos de tensión + valles de respiro
Beat Sheet: Setup → Inciting Incident → Midpoint → Crisis → Climax → Resolution
Player Modeling: si jugador es cauteloso → time pressure;
                 si es reckless → consequences severas
```

---

## 6. IMAGE GENERATION PIPELINE

### 6.1 Trigger Points (no en cada escena — solo momentos clave)
```
- Combat kill (boss o enemy importante)
- Critical hits (nat 20)
- Story revelations (plot twist)
- New location (primera vez en dungeon/ciudad)
- NPC importante aparece por primera vez
- Momentos de decisión (crossroads)
```

### 6.2 Image Prompt Builder
```python
# Entrada: game state + scene context
# Salida: prompt optimizado para Stable Diffusion

build_image_prompt(state, scene) → {
    "style": "D&D 5e official art, cinematic, 4k",
    "subject": "valdric (human fighter, plate armor, longsword) "
               "fighting goblin_chief (green skin, scarred, waraxe) "
               "in darkwood forest (twisted trees, fog, torchlight)",
    "mood": "dark, intense, battle-scene",
    "composition": "dynamic action shot, valdric mid-swing",
    "negative": "cartoon, anime, low quality, deformed"
}
```

### 6.3 Async Flow
```
Scene generated → classify_if_dramatic() →
if dramatic → queue image_gen() → send to MiniMax →
send to Telegram after 30-90s →
game continues WITHOUT waiting
```

---

## 7. TELEGRAM COMMANDS

| Command | Description |
|---|---|
| `/newgame [setting] [--players N] [--level N]` | Crea campaña nueva |
| `/join [campaign_id]` | Join existente |
| `/roll [dice]` | Tira dados (2d6+3, 1d20+5, etc) |
| `/attack [target]` | Ataque melee/ranged |
| `/cast [spell] [target]` | Lanza hechizo |
| `/skill [skill] [dc]` | Skill check (/DC override) |
| `/status` | Tu character sheet |
| `/hp` | HP actual + death saves |
| `/inventory` | Lista de items |
| `/talk [npc_name]` | Hablar con NPC |
| `/map` | Ubicación actual + descripción |
| `/quests` | Misiones activas |
| `/recap` | Resumen de lo que pasó |
| `/resume` | Reanuda última sesión |
| `/endturn` | Pasar turno (en combate) |

---

## 8. MULTIPLAYER DESIGN

```
- Grupo de Telegram = game table
- Bot responde a commands
- Cada jugador tiene DM para su character sheet privado
- Turnos: turno manager pista cuyo es
- Timer opcional: 2 min por turno, nudge si pasa
- Async: si un jugador no actúa, pasa al siguiente
- El mundo NO espera — si todos pasan, el tiempo avanza
```

---

## 9. CHARACTER CLASSES (D&D 5e simplificado)

```
FIGHTER: STR-based, +2 attacks at level 5, Action Surge
WIZARD: INT-based, spellcasting (Magic Missile, Fireball, Shield)
ROGUE: DEX-based, Sneak Attack, Cunning Action
CLERIC: WIS-based, healing spells, Turn Undead
RANGER: DEX/WIS, Favoured Enemy, Hunter's Mark
BARBARIAN: STR/CON, Rage, Reckless Attack
```

---

## 10. FEATURES PRIORITARIAS (para hackathon)

### MUST HAVE (MVP)
```
- /newgame + generación de world
- /roll con resolución de combat básico
- Character sheets con HP + stats
- 3-4 skills checks funcionales
- DM narrativo con world state
- Persistencia de campaign entre sesiones
- Multiplayer (hasta 6 jugadores)
- /recap (resumen de historia)
```

### SHOULD HAVE (post-MVP)
```
- Image generation en momentos dramáticos
- Spell system completo
- Death saves + death mechanics
- NPC memory + relationships
- Skill Challenges (multi-check encounters)
- Timer por turno
- Múltiples settings (fantasy, sci-fi, horror)
```

### NICE TO HAVE (post-hackathon)
```
- Voice messages como input (TTS → acción)
- Mapas visuales generados
- Initiative tracker visual
- Sheet builder visual
- Multiple campaigns simultáneas
- Campaign export/import
```

---

## 11. STACK TÉCNICO

```
Lenguaje: Python 3.10+
Telegram: python-telegram-bot library
Game State: JSON files (campaigns/ UUID /state.json)
LLM: Hermes Agent (MiniMax) como DM narrativo
Image Gen: MiniMax image generation API
Persistence: ~/.hermes/hermesdm/campaigns/
Dependencies:
  - python-telegram-bot
  - aiohttp (para async image gen)
  - pydantic (validation)
  - pytest (testing)
```

---

## 12. ESTRUCTURA DE REPO

```
hermesdm/
├── bot/
│   ├── __init__.py
│   ├── telegram_handler.py    # entry point, command routing
│   ├── dice_engine.py         # roll() + resolve_check()
│   ├── combat_engine.py       # attack, damage, spells
│   ├── skill_checks.py        # skill resolution
│   ├── character_sheet.py     # Player/Character class
│   ├── turn_manager.py        # combat initiative + turns
│   └── state_validator.py     # consistency enforcement
├── dm/
│   ├── __init__.py
│   ├── system_prompt.md       # DM identity + rules + style
│   ├── narrative_generator.py # scene → narrative text
│   ├── world_builder.py       # generate world on /newgame
│   ├── scene_classifier.py    # detecta momento visual
│   └── image_prompt_builder.py# state → SD prompt
├── state/
│   ├── __init__.py
│   ├── state_manager.py       # load/save campaign state
│   └── templates/            # starting world templates
├── tests/
│   ├── test_dice_engine.py
│   ├── test_combat_engine.py
│   ├── test_skill_checks.py
│   ├── test_state_manager.py
│   └── test_integration.py
├── data/
│   └── campaigns/.gitkeep
├── skill/
│   └── SKILL.md               # Hermes skill for loading
├── requirements.txt
├── README.md
└── main.py                    # bot entry point
```

---

## 13. CALENDARIO HACKATHON (16 días)

```
DÍA 1-2:   Setup repo + bot básico + /newgame + world builder
DÍA 3-4:   Game engine (dice, combat, skills, character sheets)
DÍA 5-6:   DM narrativo + state persistence + /recap
DÍA 7-8:   Multiplayer (grupo Telegram) + turn manager
DÍA 9-10:  /status, /inventory, skill system completo
DÍA 11-12: Image generation pipeline (async, triggers)
DÍA 13-14: Polish + NPC memory + world continuity
DÍA 15:    Video demo + README + Testing con usuarios
DÍA 16:    Buffer + submission
```

---

## 14. DIFERENCIACIÓN FRENTE A COMPETIDORES

| Feature | AI Dungeon | TavernAI | FoundryVTT | HermesDM |
|---|---|---|---|---|
| Dados reais con mecânicas | ✗ | ✗ | ✓ | ✓ |
| Multiplayer real | ✗ | ✗ | ✓ | ✓ |
| Persistencia cross-session | △ | △ | ✓ | ✓ |
| NPCs con memoria | △ | △ | ✗ | ✓ |
| Game mechanics (HP/combat/skills) | ✗ | ✗ | ✓ | ✓ |
| Sistema de turnos | ✗ | ✗ | ✓ | ✓ |
| Narrativa procedural | ✓ | ✓ | ✗ | ✓ |
| Asynchronous play | ✗ | ✗ | △ | ✓ |
| Acceso via Telegram | ✗ | ✗ | ✗ | ✓ |
| Image generation | ✗ | ✗ | ✗ | ✓ |

---

## 15. SKILL APPROACH

**Repo:** github.com/sebaunsa-collab/hermesdm
**Skill:** SKILL.md carga el bot commands en Hermes
**Deploy:** Bot corriendo en server para demo live

Cuando Sherman dice "Hermes, quiero jugar D&D":
→ Hermes detecta intent → usa /newgame + /roll + /attack commands
→ Bot responde como DM
→ Integración seamless con Hermes Agent existente

---

## 16. CONSIDERACIONES IMPORTANTES

- **Python + LLM separation:** Python = mecánicas puras (sin narrativa), LLM = narrativa pura (sin mecânicas). Python le dice al LLM qué pasó, LLM describe qué significa.
- **State como source of truth:** LLM SIEMPRE consulta state antes de narrar. No generar contradicciones.
- **Image async:** No bloquear juego esperando imagen. Cola en background.
- **Async por diseño:** No se necesita scheduled sessions. DM propone, jugadores tiran cuando pueden.
- **Reglas simplificadas:** D&D 5e base pero simplificado para que quepa en timeline de hackathon.
