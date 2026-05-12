# AGENTS.md — HermesDM

AI Dungeon Master multiplayer via Telegram. D&D 5e game engine with LLM narration.

## Build & Run Commands

```bash
make install         # Install deps
make install-dev     # Install deps + dev tools (pytest, ruff, mypy)
make run             # Start the Telegram bot (python -m bot.telegram_handler)
make test            # Run all tests (pytest tests/ -v)
make cov             # Run tests with coverage (fails if <80%)
make lint            # Ruff check bot dm state
make typecheck       # Mypy bot dm state
make clean           # Remove caches and build artifacts
```

### Single test / specific module

```bash
PYTHONPATH="" python3 -m pytest tests/test_combat_engine.py -v
PYTHONPATH="" python3 -m pytest tests/test_combat_engine.py::TestResolveAttack::test_hit -v
PYTHONPATH="" python3 -m pytest tests/ -k "world_builder" -v
PYTHONPATH="" python3 -m pytest tests/ -v --tb=short -x   # stop on first failure
```

### Local REPL (no Telegram)

```bash
python main.py
```

## CI

CI runs on push/PR to main: ruff check → mypy → pytest with 80% coverage gate.
Python 3.10, 3.11, 3.12 matrix. See `.github/workflows/ci.yml`.

## Architecture

```
bot/              Game logic (Telegram side)
  telegram_handler.py   Entry point, command routing (5000+ lines, BE CAREFUL)
  combat_engine.py      Attack, damage, crits — pure mechanics
  character_sheet.py    HP, XP, inventory, conditions, death saves
  dice_engine.py        Dice parsing and rolling
  spell_manager.py      Spellcasting, damage, saves
  skill_checks.py       Skill checks, saving throws
  turn_manager.py       Turn order, countdown

dm/               AI Engine (DM brain)
  narrative_generator.py  LLM calls — narration and dialogue
  world_builder.py        World/NPC generation by genre (fragile, 3-layer fallback)
  image_provider.py       ABC + Pollinations/MiniMax/Flux/NanoBanana/fal
  image_event_handler.py  Auto-image trigger logic + cooldown
  provider_client.py      API wrapper — changes affect everything
  encounter_engine.py     Encounter generation
  monster_manual.py       Monster stat blocks
  npc_director.py         NPC management
  spell_engine.py         Spell resolution engine

adapters/mode_b/  Action abstraction layer
  action_router.py        Classifies /j commands → ActionResult

state/            Persistence
  state_manager.py        Read/write campaign JSON in ~/.hermes/hermesdm/campaigns/
  state_validator.py      State shape validation
  npc_store.py            Persistent NPC data

web/              Optional FastAPI read-only dashboard (separate deployment)
scripts/          Utility scripts (install, audit viewer, analytics)
tests/            43 test files, ~274 tests
```

## Code Style

- **Python 3.10+** with `from __future__ import annotations`
- **Line length:** 88 (ruff default, E501 ignored)
- **Ruff rules:** E, F, W, I, N, UP
- **Type hints:** mypy with `warn_return_any`, `warn_unused_ignores`, `ignore_missing_imports`
- **Imports:** stdlib → third-party → local, grouped with blank lines
- **Docstrings:** triple-quoted module-level docstrings on every file (2-3 lines explaining purpose)
- **Comments:** mixed Spanish/English in comments — both are fine
- **Naming:** snake_case for functions/variables, PascalCase for classes
- **No logging in production code** — trust the framework
- **Dict-based return values** from game functions (not dataclasses/pydantic for internal APIs)

## Critical Files (Read Before Touching)

These files are fragile. Read the full flow and check test coverage before modifying:

| File | Risk | Why |
|------|------|-----|
| `bot/telegram_handler.py` | HIGH | 5000+ lines, single entry point for all commands |
| `dm/world_builder.py` | HIGH | 3-layer fallback, genre validation, echo detection, JSON parsing |
| `state/state_manager.py` | HIGH | Core persistence — any change can corrupt campaign state |
| `dm/narrative_generator.py` | MEDIUM | LLM calls — can break without visible errors |
| `dm/provider_client.py` | MEDIUM | API wrapper — changes propagate to all providers |

## Development Rules

Source: `.github/WORKFLOW.md` — read it in full for the complete protocol.

1. **Check repo state first** — `git status`, `git log --oneline -10` before ANY code change
2. **One bug = one hypothesis = one scope = one fix** — never touch 5 files "to see which works"
3. **Write a failing test first** — reproduce the bug in a test before fixing code
4. **Test suite MUST pass before committing** — `make test` or don't commit
5. **Always have a rollback** — `git stash` or feature branch before changes
6. **Refactoring is a separate commit** — never mix refactor with bug fix
7. **Document decisions** — commit messages explain WHY, not just WHAT

### Commit message format

```
fix: <concise description of what was fixed>
test: <what test was added/changed>
refactor: <what was restructured>
feat: <what was added>
```

## Environment

- `TELEGRAM_BOT_TOKEN` — required, from @BotFather
- `MINIMAX_API_KEY` — optional, image generation (Pollinations is free default)
- `FAL_KEY` — optional, fal.ai image generation
- Config: `config.yaml` (copy from `config.yaml.example`)
- State persisted at `~/.hermes/hermesdm/campaigns/`

## Test Conventions

- `conftest.py` provides `roll_dice_dict()` helper and auto-resets telegram_handler globals
- `PYTHONPATH=""` is intentional — prevents local imports from shadowing installed packages
- Unit tests use mocks for LLM/API calls (`test_world_builder.py`)
- Integration tests (`test_*_echo.py`) hit real APIs — expected to fail without keys
- `pytest-asyncio` with `asyncio_mode = "auto"` — async tests work without decorators
- Coverage threshold: 80% (`--cov-fail-under=80`)
