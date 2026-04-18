# HermesDM — Production Ready Specification

## Resumen
HermesDM es un AI Dungeon Master multiplayer via Telegram. Los jugadores tiran dados reales, tienen character sheets completos, y un LLM narra como DM. El mundo persiste entre sesiones.

## Arquitectura Final

```
Telegram User
    │
    ▼
┌─────────────────────────────────────────────────────┐
│            telegram_handler.py                      │
│  • Command routing (/roll, /attack, /newgame…)     │
│  • Message parsing                                  │
│  • DM → Telegram output                            │
│  • Inline query support                             │
└────────────────────┬────────────────────────────────┘
                     │ calls
         ┌───────────┼────────────┐
         ▼           ▼            ▼
   Game Engine   DM System    State
   (pure logic)  (pure LLM)   Manager
         │           │            │
         └───────────┴────────────┘
                     │
              ┌──────▼──────┐
              │ Image Queue  │
              │ (async, 30-90s)│
              └─────────────┘
```

## Fases de Implementación

---

### FASE 1: Telegram Bot Handler
**Archivos:** `bot/telegram_handler.py`
**Tests:** `tests/test_telegram_handler.py`

#### R1: Command Router
- Decorator `@handler.command("/roll")` registra commands
- Commands: `/newgame`, `/join`, `/roll`, `/attack`, `/cast`, `/skill`, `/status`, `/hp`, `/inventory`, `/talk`, `/map`, `/quests`, `/recap`, `/resume`, `/endturn`, `/help`
- Cada command tiene help text
- Unknown commands devuelven "Unknown command. Type /help."

#### R2: Dice Integration
- `/roll 2d6+3` → `dice_engine.roll()` → formato Telegram (🎲)
- `/roll` solo → d20 por defecto
- Formato de respuesta: "🎲 Rolling 2d6+3... [4, 2] + 3 = 9"

#### R3: Combat Flow
- `/attack goblin` → interactive: bot pide AC → player tira d20 → bot resuelve con combat_engine
- Advantage/disadvantage: `/roll 1d20 advantage`
- Crit/fumble especiales con formato dramático

#### R4: Character Sheet Display
- `/status` → formateado como card Telegram con stats, HP bar, AC, conditions
- `/hp` → HP actual con death saves
- `/inventory` → lista de items con descripciones
- `/recap` → último history entry

#### R5: Campaign Management
- `/newgame fantasy` → `world_builder.create_campaign()` → guarda session
- `/join campaign_id` → registra player en campaign
- `/resume` → continúa última campaign activa
- Cada chat de Telegram = una campaign

#### R6: Multiplayer Support
- Grupo de Telegram = game table
- Bot responde con @username para identificar jugadores
- Turn tracker visible: "It's Valdric's turn (Round 3)"
- `/endturn` → avanza al siguiente

---

### FASE 2: DM Narrative System
**Archivos:** `dm/narrative_generator.py`, `dm/scene_classifier.py`, `dm/image_prompt_builder.py`
**Tests:** `tests/test_narrative.py`

#### R7: Narrative Generator
- `generate_scene(state, scene_type, context)` → texto narrativo
-scene_types: EXPLORATION, COMBAT, DIALOGUE, STORY_BEAT, REST
- Inyecta system prompt + current state + character sheets
- 2-4 oraciones, termina con situación abierta (no pregunta)
- Llamadas Tool.use para resolver mecánicas

#### R8: Scene Classifier
- `classify_scene(game_event)` → bool (generar imagen o no)
- Triggers: boss kill, nat 20, first time location, NPC intro, story revelation
- Debounce: no más de 1 imagen cada 60s

#### R9: Image Prompt Builder
- `build_prompt(state, scene)` → dict con style, subject, mood, composition, negative
- Estilo: "D&D 5e official art, cinematic, 4k, highly detailed"
- Subject construido desde: characters presentes + enemies + location
- Mood del scene_type: combat=tense, exploration=mysterious, dialogue=intimate

---

### FASE 3: Full Test Suite
**Tests:** `tests/test_*.py` (completar coverage)

#### R10: Unit Tests Completos
- coverage ≥ 80% en bot/, dm/, state/
- Tests de edge cases: crits, fumbles, death saves, temp HP
- Tests de state serialization roundtrip

#### R11: Integration Tests
- `test_newgame_flow`: /newgame → world created → state persisted
- `test_combat_flow`: start → attack → damage → next turn → end
- `test_character_sheet_roundtrip`: create → save → load → verify
- `test_npc_memory`: NPC relationship changes persist

---

### FASE 4: Production Infrastructure
**Archivos:** `pyproject.toml`, `.env.example`, `Makefile`, CI/CD

#### R12: Config & Env
- `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `MINIMAX_API_KEY` en `.env`
- `pydantic-settings` para config validation
- `loguru` para logging estructurado

#### R13: CI Pipeline
- GitHub Actions: `pytest -v --cov` en cada push
-lint: `ruff check` + `mypy` (type checking)
- Tests pasan en CI antes de merge

#### R14: README & Docs
- README.md: setup, usage, commands, architecture
- docs/ con diagramas de arquitectura
- CHANGELOG.md

---

### FASE 5: Repo & Deploy
**Repos:** GitHub repo en `sebaunsa-collab/hermesdm`

#### R15: Git Repo
- `.gitignore` limpio (sin .pyc, __pycache__, .env)
- Commits semánticos: `feat:`, `fix:`, `test:`, `docs:`, `chore:`
- Tags para releases

---

## Tech Stack
- Python 3.12+
- python-telegram-bot v20+
- pydantic v2+
- loguru
- pytest + pytest-cov
- ruff + mypy
- httpx (async HTTP client)
- aiohttp (async image queue)

## Edge Cases
- Jugador hace /roll fuera de campaign → "Start a campaign first with /newgame"
- Campaign no existe en /resume → prompt para /newgame
- HP llega a 0 → death saves, marcar unconscious
- Temp HP no se stacking (máximo entre actual y nuevo)
- 6 jugadores máximo por campaign
- Image gen falla → silently skip, no bloquea juego

## Out of Scope
- Voice input / TTS output
- Mapas visuales generados
- Campaign export/import
- Servidor web de admin
- Webhook para远处的updates
