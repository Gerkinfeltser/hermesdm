# 🎲 HermesDM — AI Dungeon Master via Telegram

> Tu Dungeon Master con IA corre directo en Telegram. Dados reales, hojas de personaje, combate por turnos, continuidad del mundo, narración con LLM, y generación de imágenes contextuales.

![D&D 5e](https://img.shields.io/badge/D%26D-5e-960020?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
[![Tests](https://img.shields.io/badge/Tests-274%20%E2%9C%85-brightgreen?style=flat-square)](tests/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square)](https://t.me/)

---

## ⚡ TL;DR

```
Vos: /create Valdric Wizard
Bot: ⚔️ Valdric creado! HP: 6 | AC: 13 | Slots: 4/4/3/3/3

Vos: /j attack dragon
Bot: 🎲 Tiras ataque... [d20+5 → 19+5=24] ¡GOLPE CRÍTICO!
     🔥 "Valdric atraviesa el corazón del dragón anciano..."
     🖼️ [Imagen generada automáticamente]

Vos: /cast fireball goblins
Bot: ✨ Fireball! [8d6=38 daño] ¡3 goblins eliminados!
     🧙 Slots consumidos: Lv3 → 2 restantes
```

**No necesitás Roll20, D&D Beyond, ni ninguna otra app. Solo Telegram.**

---

## 🎮 Demo en Vivo

```
⏱️ Sesión real — Campaign: "The Dragon's Lair"

🧙 Sherman → /join
⚔️ COMBATE INICIADO: Valdric vs Ancient Dragon (HP: 180, AC: 19)

🧙 Sherman → /j attack dragon (Ventaja)
🎲 [2d20+7 → 18, 19+7=26] ¡NATURAL 20! 💥
🔥 "Valdric delivers a devastating blow, the dragon crashing
   down from the sky in flames — dramatic cinematic battle scene"
🖼️ [MiniMax image → grupo de Telegram]

💀 Sherman → HP: 12/68 (-56)
⚔️ Dragon's Turn → Breath Weapon [54 daño]
💀 Sherman → HP: 0/68 — ¡CAE AL SUELO!
☠️  VALDRIC ESTÁ MUERTO
🖼️ [Imagen de muerte enviada]

🎲 Death Save: 2 successes, 1 failure
💀 Valdric stabilized... barely.
```

---

## ✨ Features

| Feature | Status |
|---------|--------|
| 🎲 Dados reales (1d4 → 1d20+, ventaja, desventaja, saves) | ✅ |
| 📋 Hojas de personaje (HP, XP, inventario, condiciones) | ✅ |
| 🧙 Sistema de spell slots (Wizard, Cleric, Warlock...) | ✅ |
| 💀 Death saves que sobreviven reinicios del bot | ✅ |
| 🧙 NPCs persistentes con memoria | ✅ |
| ⚔️ Motor de combate por turnos | ✅ |
| 📖 Narración LLM y diálogo de NPCs | ✅ |
| 🖼️ Generación automática de imágenes (Pollinations/MiniMax/Flux) | ✅ |
| 💾 Estado de campaña en JSON (persiste entre sesiones) | ✅ |
| 🏰 5 géneros de campaña (fantasy, dungeon, horror, tavern, scifi) | ✅ |
| 💬 100% Telegram — ninguna app externa | ✅ |

---

## 🚀 Quick Start

```bash
# 1. Clonar e instalar
git clone https://github.com/sebaunsa-collab/hermesdm.git
cd hermesdm
pip install -e .

# 2. Configurar tokens
cp .env.example .env
# Editar TELEGRAM_BOT_TOKEN y MINIMAX_API_KEY en .env

# 3. Ejecutar
hermesdm
# O: python -m bot.telegram_handler
```

Listo. Abrí Telegram, buscá tu bot, y escribí `/start`.

---

## 🎯 Guía de Comandos

### 🏠 Inicio de Partida
| Comando | Descripción |
|---------|-------------|
| `/start` | Lanzar el wizard de nueva campaña |
| `/campaign` | Ver info de la campaña activa |
| `/newgame` | Reiniciar y empezar campaña fresca |
| `/end` | Terminar sesión — genera epílogo + imagen |
| `/settings` | Cambiar dificultad, tono, provider de imágenes |

### 👤 Personajes
| Comando | Descripción |
|---------|-------------|
| `/create <nombre> <clase>` | Crear personaje (Nv 1, standard array) |
| `/delete <nombre>` | Eliminar personaje |
| `/chars` | Listar todos los personajes |
| `/char <nombre>` | Hoja de personaje completa |
| `/hp <nombre> [valor]` | Ver o modificar HP |
| `/xp <nombre> [valor]` | Ver o modificar XP |
| `/levelup <nombre>` | Subir de nivel (recalcula HP automático) |
| `/conditions <nombre> [add/remove]` | Condiciones (poisoned, stunned...) |
| `/deathsave <nombre> [success/fail]` | Saving throw de muerte |
| `/rest` | Descanso largo (recupera todo) |
| `/shortrest` | Descanso corto (1 hit die + MOD CON) |

### 🎒 Inventario
| Comando | Descripción |
|---------|-------------|
| `/inventory <nombre>` | Mostrar inventario |
| `/item <nombre> <item>` | Agregar item |
| `/give <nombre> <item>` | Alias para `/item` |
| `/drop <nombre> <item>` | Remover item |
| `/equip <nombre> <item>` | Equipar item |
| `/unequip <nombre> [item]` | Desequipar item(s) |

### 🎲 Dados & Chequeos
| Comando | Descripción |
|---------|-------------|
| `/roll <dado>` | Tirar dados (ej: `2d6+3`, `1d20+5`) |
| `/r <dado>` | Alias corto |
| `/flip` | Moneda (1d2) |
| `/check <stat> [adv/dis]` | Chequeo de skill (str, dex, con...) |
| `/save <stat> [dc]` | Saving throw (default DC 10) |

### ✨ Magia & Spellcasting
| Comando | Descripción |
|---------|-------------|
| `/cast <nombre> <spell> [target]` | Lanzar hechizo (consume slot si aplica) |
| `/spells` | Listar hechizos disponibles por nivel |

**Spells disponibles:**
- **Cantrips:** Fire Bolt, Sacred Flame, Shocking Grasp, Mind Sliver, Thaumaturgy
- **Nv 1:** Magic Missile, Guiding Bolt, Healing Word, Thunderwave, Shield, Sleep
- **Nv 2:** Scorching Ray, Spiritual Weapon, Hold Person, Misty Step
- **Nv 3:** Fireball, Counterspell, Mass Healing Word
- **Nv 4:** Polymorph, Wall of Fire
- **Nv 5:** Cone of Cold, Flame Strike

**Sistema de Spell Slots:**
| Clase | Nv1 | Nv2 | Nv3 | Nv4 | Nv5 |
|-------|-----|-----|-----|-----|-----|
| Wizard | 4 | 3 | 3 | 3 | 3 |
| Cleric/Druid/Bard | 4 | 3 | 3 | 3 | 3 |
| Paladin/Ranger | 4 | 3 | 3 | 2 | 2 |
| Warlock | Pact slot (short rest) | — | — | — | — |

### ⚔️ Combate
| Comando | Descripción |
|---------|-------------|
| `/combat` | Estado del combate activo |
| `/join` | Unirse al combate |
| `/attack <target>` | Atacar (alias: `/j`) |
| `/endturn` | Terminar tu turno |
| `/flee` | Huir del combate |
| `/status` | HP, AC, condiciones del grupo |
| `/summon <nombre> [tipo]` | Invocar monstruo genérico |
| `/monster <nombre> [HP] [AC]` | Invocar monstruo custom |
| `/remove <nombre>` | Remover criatura del combate |
| `/monsters` | Listar monstruos en combate |

### 🧙 NPCs
| Comando | Descripción |
|---------|-------------|
| `/npc <nombre>` | Consultar o crear NPC |
| `/npcs` | Listar NPCs activos |
| `/npcnote <nombre> <nota>` | Agregar nota del DM sobre NPC |
| `/talk <npc> <mensaje>` | Hablar con un NPC (diálogo LLM) |
| `/npcsearch <query>` | Buscar NPCs por nombre/título |
| `/npcmemory <nombre> <key> <valor>` | Registrar memoria sobre NPC |

### 🖼️ Narración & Imágenes
| Comando | Descripción |
|---------|-------------|
| `/act <accion>` | Narrar una acción en el mundo |
| `/scene <descripcion>` | Describir la escena actual |
| `/image <prompt>` | Generar imagen manualmente |
| `/sceneimage` | Auto-generar imagen de la escena actual |

---

## 🌍 Géneros de Campaña

Cuando ejecutás `/newgame`, elegís un género. Cada uno tiene system prompts únicos para el LLM:

| Género | Vibe | Descripción |
|--------|------|-------------|
| `fantasy` | 🏰 | Aventuras medievales de alta fantasía |
| `dungeon` | 🗝️ | Exploración de mazmorras, puzzles, trampas |
| `tavern` | 🍺 | Intriga política, misiones desde la taberna |
| `horror` | 👻 | Horror psicológico, supervivencia |
| `scifi` | 🚀 | Sci-fi, space opera, cyberpunk |

---

## 🖼️ Cómo Funcionan las Imágenes Automáticas 📸

El DM genera imágenes **automáticamente** en momentos narrativamente importantes — sin que lo pidas.

### 🎯 Eventos que Disparan Imágenes
| Evento | Imagen? |
|--------|---------|
| Natural 20 (golpe crítico) | ✅ |
| Natural 1 (pifia) | ✅ |
| Muerte de personaje (HP = 0) | ✅ |
| Combate contra boss | ✅ |
| Nueva ubicación/NPC descubierta | ✅ |
| Fin de sesión | ✅ |
| HP baja del 25% | ✅ |
| Turno normal | ❌ |

### 🔌 Providers Soportados
| Provider | Calidad | Velocidad | Costo |
|----------|---------|------------|-------|
| Pollinations | Buena | ~1s | Gratis |
| MiniMax | Excelente | ~10s | API key |
| Flux | Alta | Variable | Local |

### ⚙️ Configuración
```yaml
# config.yaml
image_provider: "pollinations"   # default
minimax_api_key: "tu-key"        # opcional
```

O en runtime via `/settings`.

---

## 🏗️ Arquitectura

```
hermesdm/
├── bot/
│   ├── telegram_handler.py      # Entry point, command routing
│   ├── character_sheet.py       # HP, XP, inventory, conditions, death saves
│   ├── combat_engine.py         # Initiative, attack resolution, crits
│   ├── diceRoller.py            # Dice parsing, rolling, formatted output
│   ├── skill_checks.py          # Skill checks, saving throws
│   ├── spell_manager.py         # Spellcasting, damage, saves
│   └── monsters.py              # Monster definitions, summon
├── dm/
│   ├── narrative_generator.py   # LLM narration, NPC dialogue
│   ├── world_builder.py         # World/NPC generation per genre
│   ├── image_provider.py        # ABC + Pollinations/MiniMax/Flux
│   └── image_event_handler.py   # Auto-trigger logic + cooldown
├── adapters/mode_b/
│   └── action_router.py         # /j action routing, ActionResult
├── state/
│   └── state_manager.py         # Campaign state, JSON persistence
└── tests/                       # 274 tests
    ├── test_combat_engine.py
    ├── test_character_sheet.py
    ├── test_diceRoller.py
    └── ...
```

### 🔄 Flujo de Acción (Ejemplo: Combate)

```
/j attack dragon
  → action_router.route()         # Parsear acción, determinar tipo
  → combat_engine.resolve()        # Tirar dados, calcular daño
  → narrative_generator.generate_scene()  # Narración LLM
  → image_event_handler.maybe_generate()  # ¿Generamos imagen?
  → telegram_handler._maybe_send_scene_image()  # Enviar si corresponde
```

### 🖼️ Flujo de Generación de Imágenes

```
NarrativeGenerator.generate_scene()
  → Result { narrative, triggered_image, scene_type }
      ↓ triggered_image = True
ImageEventHandler.maybe_generate()
  → Check cooldown (5 min default)
  → Check trigger rules (nat_20, death, boss, etc.)
      ↓ allowed
ImageProvider.generate()
  → build_scene_prompt()        # Context + genre → prompt
  → Pollinations / MiniMax / Flux  # API call
  → /tmp/hermesdm_*.png        # Archivo local
      ↓
TelegramBot.send_photo()
  → Imagen al grupo
```

---

## 💾 Estado de Campaña

Todo el estado vive en `~/.hermes/hermesdm_state.json`:

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
  "characters": { ... },
  "npcs": { ... },
  "timeline": [ ... ],
  "combat": { ... }
}
```

---

## 🛠️ Desarrollo

```bash
# Correr todos los tests
python -m pytest tests/ -v

# Con coverage
python -m pytest tests/ --cov=bot --cov=dm --cov=adapters

# Validar campaign state
python -c "from state.state_manager import validate_state; validate_state()"

# Lint
ruff check bot dm adapters

# Type check
mypy bot dm --ignore-missing-imports
```

---

## 📚 Especificaciones Detalladas

- [SPEC_SPELL_SLOTS.md](SPEC_SPELL_SLOTS.md) — Sistema de spell slots D&D 5e
- [SPEC_NPC_PERSISTENCE.md](SPEC_NPC_PERSISTENCE.md) — NPCs persistentes con memoria
- [SPEC_IMAGE_GENERATION.md](SPEC_IMAGE_GENERATION.md) — Sistema de imágenes automáticas
- [SPEC_DEATH_SAVES_PERSISTENCE.md](SPEC_DEATH_SAVES_PERSISTENCE.md) — Death saves entre reinicios
- [SPEC_DICE_ANIMATION.md](SPEC_DICE_ANIMATION.md) — Renderizado animado de dados
- [SPEC_PLAN_B.md](SPEC_PLAN_B.md) — Plan B: Hermes Agent como DM
- [PROJECT_PLAN.md](PROJECT_PLAN.md) — Roadmap completo del proyecto

---

## 🤝 Autor

**Sherman** — [@TheShugarBoy](https://twitter.com/TheShugarBoy)

Desarrollado con Python 🐍, Telegram Bots API, y MiniMax LLM.

¿Encontraste un bug? Abrí un issue o mandame un DM en Twitter.
