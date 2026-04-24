# SPEC — Campaign Generation Quality Fix

## Status: PROPOSED

---

## 1. CONTEXTO Y PROBLEMA

### Problema actual

Cuando el usuario pide una campaña (ej: "vampiros estilo Castlevania"), el output
presenta:

| Síntoma | Ejemplo real |
|---|---|
| **Género ignorado** | Input: vampiros Castlevania. Output: "A realm of ancient forests..." en inglés |
| **main_threat genérico** | "La amenaza de una fuerza desconocida" — aplica a cualquier campaña |
| **NPCs intercambiables** | "Despiadado eremita", "Despiadado erudito" — misma personalidad, diferente título |
| **Dialogues placeholder** | "He visto cosas que no te contaría ni bajo tortura" — genérico, sin relación al género |
| **Milestone descriptions placeholder** | "Milestone hook — avanza la trama principal" |
| **Sensory details hardcoded** | Siempre: "las sombras se aferran a cada superficie" — sin importar el género |

### Causas raíz identificadas

1. **Prompt sin constraints duros**: El prompt Layer 1 dice "inventá todo" pero no verifica
   que el género aparezca en el output.
2. **Sin validación post-generación**: `_is_echo()` detecta copia literal pero no detecta
   irrelevancia (el modelo ignora "vampiros" y pasa el check).
3. **`create_default_story_arc` usa placeholders**: `f"Milestone {spec[0]} — avanza la trama principal"`
   se usa como fallback Y cuando el LLM retorna descripciones placeholder.
4. **`narrative_generator._build_context` hardcodea sensory_details**: No lee del setup
   real del campaign.

---

## 2. ARQUITECTURA DE LA SOLUCIÓN

### Flujo corregido

```
generate_setup_with_ai(description, tone, setting)
    │
    ├─► Layer 1: AI prompt V2 (con constraints duros + few-shot)
    │       │
    │       ├─► _validate_genre_presence() ← NUEVO
    │       │       Si falla → Layer 2
    │       │
    │       └─► _validate_milestone_quality() ← NUEVO
    │               Si falla → Layer 2
    │
    ├─► Layer 2: AI fallback prompt (simplificado, más directive)
    │       │
    │       └─► Validación igual
    │
    └─► Layer 3: Template fallback (NUNCA generically named milestones)
```

### Archivos a modificar

```
hermesdm/
├── dm/
│   ├── world_builder.py          # Refactor generate_setup_with_ai
│   └── story_arc.py              # Fix create_default_story_arc
├── dm/narrative_generator.py     # _build_context — usa setup real
└── state/state_manager.py        # Opcional: derivar sensory_details del setup
```

---

## 3. CAMBIOS CONCRETOS

### 3.1 world_builder.py — Reforzar prompt Layer 1

**Cambio: Prompt V2 con constraints duros**

Reemplazar el prompt actual (sección "CRÍTICO — Reglas de oro") por:

```python
prompt = f"""Eres un DM creativo de D&D 5e con 20 años de experiencia.

GÉNERO SOLICITADO: {setting.upper()}
TONO: {tone.upper()}

REGLAS ABSOLUTAS (si violás aunque sea una, el output se rechaza):
R1. La palabra "{setting}" o sinónimos específicos del género DEBEN aparecer
   en main_threat, premise o starting_location_desc.
   Ejemplo para genre=vampire: "El Conde Drakov, señor vampiro de la región..."
   → INCUMPLO si pongo: "Una fuerza oscura se cierne" sin mencionar vampiros.
R2. Cada NPC debe tener un dialogue que haga referencia AL GÉNERO, no genérico.
   Para genre=vampire: "Aldric se cruza de brazos: 'Esos malditos no duermen. Nunca duermen.'"
   → INCUMPLO si pongo: "He visto cosas que no te contaría."
R3. main_threat DEBE ser un párrafo de 1-2 oraciones CON NOMBRE PROPIO del antagonista
   o fuerza antagonista específica del género. No vale "una amenaza desconocida".
   → INCUMPLO si pongo: "Una amenaza de origen incierto."
R4. starting_location DEBE tener nombre propio que refleje el género.
   Para genre=vampire: "El Púlpito de Cristal" (castillo en ruinas)
   → INCUMPLO si pongo: "un lugar olvidado"
R5. Cada milestone.description debe tener >= 15 palabras y describir UNA ESCENA CONCRETA.
   → INCUMPLO si pongo: "Milestone hook — avanza la trama principal"

EJEMPLOS OBLIGATORIOS POR GÉNERO:

genre=vampire:
{{
  "main_threat": "El Conde Drakov, un vampiro que ha dominado la región por tres siglos,
   ha comenzado a convertir a la nobleza en sus siervos.",
  "starting_location": "Las Catacumbas de San Adrián",
  "npcs": [{{
    "name": "Drago",
    "role": "Cazador de vampiros caído",
    "dialogue": "Drago escupe sangre: 'Pensé que podía cazarlos. Fue mi error. Ahora '
  }}]
}}

genre=scifi:
{{
  "main_threat": "La Hegemonía de Cygnus ha cortado todas las rutas de escape del sector.",
  "starting_location": "El Puerto de Nómada",
  "npcs": [{{
    "name": "Kira",
    "role": "Contrabandista de información",
    "dialogue": "'La Hegemonía no deja testigos. Pero yo sí — por el precio correcto.'"
  }}]
}}

genre=horror:
{{
  "main_threat": "La书院 de Ashworth ha despertado. Sus muros tienen hambre.",
  "starting_location": "El Pueblo de Piedra Negra",
  "npcs": [{{
    "name": "El Padre Malone",
    "role": "Sacerdote roto",
    "dialogue": "Sus manos tiemblan: 'Cerré las puertas de la iglesia. No fue suficiente.'"
  }}]
}}

--- 
IDEA DEL DM (para inspiración, NO para copiar palabras):
{description}

Generá la campaña completa en español. Respondé ÚNICAMENTE en JSON válido.
"""
```

### 3.2 world_builder.py — Agregar validaciones post-generación

```python
def _validate_genre_presence(setup: dict, genre: str) -> list[str]:
    """Verifica que el género aparezca en los campos clave.
    
    Returns: lista de errores (vacía = válido)
    """
    errors = []
    genre_keywords = _GENRE_KEYWORDS.get(genre, set())
    
    # Check main_threat
    threat = setup.get("lore", {}).get("main_threat", "").lower()
    if not any(kw in threat for kw in genre_keywords):
        errors.append(
            f"main_threat no contiene ninguna palabra del género {genre}: "
            f"found='{threat[:60]}'"
        )
    
    # Check premise
    premise = setup.get("premise", "").lower()
    if not any(kw in premise for kw in genre_keywords):
        errors.append(f"premise no menciona el género: '{premise[:60]}'")
    
    # Check NPCs reference genre
    npcs = setup.get("lore", {}).get("npcs", [])
    for npc in npcs:
        dialogue = npc.get("dialogue", "").lower()
        if len(dialogue) < 20:  # Too generic
            errors.append(f"NPC {npc.get('name')} tiene dialogue demasiado corto o genérico")
    
    return errors

_GENRE_KEYWORDS = {
    "vampire": {"vampiro", "vampira", "sangre", "nocturno", "inmortal", "colmillo", "castillo", "drácula"},
    "fantasy": {"dragón", "mago", "reino", "hechizo", "elfo", "orco", "taberna", "espada"},
    "horror": {"oscuridad", "maldito", "demonio", "sangre", "muerte", "pueblo", "maldito"},
    "scifi": {"nave", "cyborg", "estación", "tecnología", "espacio", "dato", "código", "holo"},
    "zombie": {"muerte viviente", "cadáver", "pandemia", "supervivencia", "mordida", "infectado"},
    "pirates": {"pirata", "barco", "mar", "tesoro", "capitán", "tripulación", "corona", "código"},
}
```

### 3.3 world_builder.py — Fallback Layer 2 mejorado

Si Layer 1 falla validación, Layer 2 usa:

```python
# Genre-aware template expansion con elementos específicos
fallback_prompt = f"""Género: {setting.upper()}
Tono: {tone.upper()}

Inventá una campaña de D&D 5e donde:
- La amenaza central (main_threat) es específica de {setting}
- La location inicial refleja {setting}
- Los NPC tienen diálogos quereferencean elementos del género

JSON solo. Sin campos vacíos. Sin "una amenaza".
"""
```

### 3.4 story_arc.py — Fix create_default_story_arc

```python
def create_default_story_arc(pacing_level: str = "medium", genre: str = "fantasy") -> StoryArc:
    """Fallback arc when AI generation fails.
    
    NO usa placeholder descriptions. Cada milestone tiene una descripción
    concreta y no-genérica.
    """
    config = PACING_CONFIG.get(pacing_level, PACING_CONFIG["medium"])
    
    # Descriptions por género, específicas y no intercambiables
    DESCRIPTIONS_BY_GENRE = {
        "vampire": {
            "hook": "Los PJ despiertan en un pueblo donde alguien ha sido encontrado sin一滴 de sangre. La这个消息 se extiende como fuego.",
            "rising_action_1": "Una investigación lleva a los PJ a las catacumbas bajo la iglesia. Algo huele la luz del sol.",
            "rising_action_2": "UnPj es abordado por un extraño que afirma ser cazador. Su motives no están claros.",
            "midpoint": "Los PJ descubren la tumba del primer vampiro. Una inscripción alerta: 'Quien lo despierte, se unirpa a su causa.'",
            "climax": "El siege al castillo del señor vampiro. Turnos simultáneos: combat y puzzle para sellar la tumba.",
            "resolution": "El vampiro es destruido. El pueblo recupera la luz. Las siguientes generaciones no sabrán lo que pasó aquí.",
        },
        "fantasy": {
            "hook": "Los PJ se conocen en una taberna cuando un messenger interrumpe con noticias del rey.",
            "rising_action_1": "El camino al castillo está bloqueado por criaturas que no deberían existir.",
            "rising_action_2": "Un traidor en la corte ha revelado los planes del grupo.",
            "midpoint": "Los PJ descubren que el rey no es la víctima — es el autor del conflicto.",
            "climax": "El enfrentamiento final en el salón del trono. Political y blades.",
            "resolution": "El reino tiene nuevo rumbo. Los PJ deciden su lugar en él.",
        },
        "horror": {
            "hook": "Los PJ llegan a un pueblo donde las puertas están cerrada from inside. Nadie duerme.",
            "rising_action_1": "Los cuerpos aparecen sin wounds visibles. La criatura no deja rastro.",
            "rising_action_2": "Un PJ es possed by something que no puede shake off.",
            "midpoint": "La verdadero horror se revela: el pueblo entero es una granja de cuerpos.",
            "climax": "Escape del pueblo antes del amanecer. Todo burning behind.",
            "resolution": "Los PJ escapan, pero algo viene con ellos.",
        },
        "scifi": {
            "hook": "Los PJ despiertan en una estación derelicta. La Última broadcast fue hace 3 días.",
            "rising_action_1": "La station tiene signals de vida — pero la crews está muerta.",
            "rising_action_2": "UnPj recibe un signal privado. No es de esta station.",
            "midpoint": "La station es una trampa. El agresor quiere algo específico — y es uno de los PJ.",
            "climax": "La nave de escape es una. Los PJ deben decidir: quién vive.",
            "resolution": "Los supervivientes escapan. La corporación ahora los busca.",
        },
        "_default": {
            "hook": "Un evento打破日常生活 de los PJ los une en una búsqueda.",
            "rising_action_1": "El camino se complica con un obstacle que no esperaban.",
            "rising_action_2": "Una traición o secreto emerge del grupo.",
            "midpoint": "La verdadera naturaleza del conflicto se revela.",
            "climax": "Todo está en juego. La decisión final debe tomarse.",
            "resolution": "Las consecuencias de la decisión se unfold.",
        }
    }
    
    defaults = DESCRIPTIONS_BY_GENRE.get(genre, DESCRIPTIONS_BY_GENRE["_default"])
    
    milestones = []
    for spec in config["milestone_specs"]:
        desc = defaults.get(spec[0], f"Momento crítico {spec[0]} — nada es lo que parecía.")
        milestones.append(
            Milestone(
                id=spec[0],
                type=spec[1],
                description=desc,
                min_scenes=spec[2],
                max_scenes=spec[3],
            )
        )
    
    return StoryArc(
        pacing_level=pacing_level,
        total_sessions=config["total_sessions"],
        milestones=milestones,
    )
```

### 3.5 narrative_generator.py — Sensory details del setup real

En `_build_context()`, después de construir el context base, agregar:

```python
def _build_context(self, state: dict, overrides: dict) -> dict:
    context = { ... }  # existing code
    
    # SOBRESCRIBIR sensory details con datos REALES del campaign setup
    setup = state.get("setup", {})
    lore = setup.get("lore", {})
    
    # Usar la descripción del setup como sensory_detail principal
    if lore.get("starting_location_desc"):
        context["sensory_detail"] = lore["starting_location_desc"]
        context["environmental_detail"] = lore["starting_location_desc"]
    
    # Usar la main_threat real como ambient_threat
    if lore.get("main_threat"):
        context["ambient_threat"] = lore["main_threat"]
    
    # Usar la premise como revelation si no hay eventos recientes
    if setup.get("premise") and not overrides.get("recent_events"):
        context["revelation"] = setup["premise"]
    
    # Usar starting_location real
    if lore.get("starting_location"):
        context["location"] = lore["starting_location"]
    
    return context
```

### 3.6 world_builder.py — Wiring completo

En `generate_setup_with_ai()`:

```python
def generate_setup_with_ai(description: str, tone: str = "serious", 
                            setting: str = "fantasy", pacing_level: str = "medium") -> dict:
    
    # ... existing Layer 1 ...
    
    # ── Post-validación obligatoria ──
    errors = _validate_genre_presence(setup, setting)
    if errors:
        log.warning(f"[WORLD_BUILDER] Genre validation failed: {errors}")
        # Retry with Layer 2
        setup = _generate_setup_fallback_v2(description, tone, setting, pacing_level)
        errors2 = _validate_genre_presence(setup, setting)
        if errors2:
            log.error(f"[WORLD_BUILDER] Layer 2 also failed: {errors2}")
            # Last resort: build_world() template (not AI)
            setup = _generate_setup_template_fallback(setting, tone, pacing_level)
    
    return setup
```

---

## 4. CASOS DE TEST

```python
def test_vampire_genre_presence():
    """El output debe contener palabras de género vampire."""
    setup = generate_setup_with_ai(
        description="vampiros y cazadores estilo castlevania, serio y oscuro",
        tone="dark",
        setting="vampire"
    )
    threat = setup["lore"]["main_threat"].lower()
    assert any(kw in threat for kw in ["vampiro", "colmillo", "nocturno", "inmortal"]), \
        f"main_threat no menciona vampiros: {threat}"

def test_npc_dialogue_not_generic():
    """NPCs no pueden tener diálogos genéricos de placeholder."""
    setup = generate_setup_with_ai(
        description="piratas en el Caribe",
        tone="serious",
        setting="pirates"
    )
    for npc in setup["lore"]["npcs"]:
        dialogue = npc.get("dialogue", "")
        # No generic placeholders
        assert "cosas que no te contaría" not in dialogue.lower()
        assert len(dialogue) >= 30, f"Dialogue too short: {dialogue}"

def test_milestone_not_placeholder():
    """Milestone descriptions no pueden ser placeholder."""
    # Force fallback (no API key scenario)
    import os
    orig = os.environ.get("MINIMAX_API_KEY")
    os.environ.pop("MINIMAX_API_KEY", None)
    try:
        arc = create_default_story_arc("medium", genre="vampire")
        for m in arc.milestones:
            assert "avanza la trama principal" not in m.description.lower(), \
                f"Placeholder in milestone {m.id}: {m.description}"
            assert len(m.description) >= 20, \
                f"Milestone {m.id} too short: {m.description}"
    finally:
        if orig:
            os.environ["MINIMAX_API_KEY"] = orig

def test_fallback_has_genre():
    """Template fallback para vampire debe tener contenido específico."""
    arc = create_default_story_arc("medium", genre="vampire")
    hook = arc.milestones[0].description
    assert "vampiro" in hook.lower() or "sangre" in hook.lower() or "catacumba" in hook.lower(), \
        f"Genre not present in vampire fallback hook: {hook}"
```

---

## 5. CRITERIOS DE ACEPTACIÓN

```
═══════════════════════════════════════════════════
CG1: Género aparece en main_threat
═══════════════════════════════════════════════════
  [ ] Input "vampiros castlevania" → main_threat contiene "vampiro" o sinónimos
  [ ] Input "piratas" → main_threat contiene "pirata" o "mar" o "barco"
  [ ] Input "horror" → main_threat no es "una fuerza oscura"

═══════════════════════════════════════════════════
CG2: NPC diálogos son específicos del género
═══════════════════════════════════════════════════
  [ ] Diálogos referencia elementos del género, no placeholders genéricos
  [ ] NPC name + role + dialogue son consistentes (un NPC vampírico no menciona tecnología)

═══════════════════════════════════════════════════
CG3: Milestones con descripciones concretas
═══════════════════════════════════════════════════
  [ ] create_default_story_arc (fallback) no genera "avanza la trama principal"
  [ ] Cada milestone tiene >= 15 palabras describing una escena específica
  [ ] Fallback vampire genera escenas de catacumbas, no de tabernas genéricas

═══════════════════════════════════════════════════
CG4: Sensory details del setup real
═══════════════════════════════════════════════════
  [ ] narrative_generator._build_context() usa starting_location_desc real
  [ ] atmospheric threat usa main_threat real, no "un gruñido distante"
  [ ] Para campaña vampire: "la sangre mancha el altar de piedra fría"
  [ ] Para campaña scifi: "el zumbido del reactor es lo único que mantiene el aire"

═══════════════════════════════════════════════════
CG5: Validación automática
═══════════════════════════════════════════════════
  [ ] Si Layer 1 falla validación → Layer 2 se ejecuta automáticamente
  [ ] Si Layer 2 falla → template fallback se ejecuta
  [ ] Nunca se guarda un setup con "avanza la trama principal" en producción
  [ ] Los logs contienen la razón de fallback (genre mismatch, milestone placeholder, etc.)
```

---

## 6. PLAN DE IMPLEMENTACIÓN

```
PASO 1 — Validación
  → Agregar _validate_genre_presence() en world_builder.py
  → Agregar _GENRE_KEYWORDS dict
  → Test: validar que un prompt vampire falla la validación actual

PASO 2 — Prompt V2
  → Reemplazar prompt Layer 1 con constraints R1-R5 + few-shot examples
  → Test: generar con "vampiros castlevania" y verificar genre en output

PASO 3 — Fallback V2
  → Implementar Layer 2 con género específico
  → Test: con API key pero output malo → Layer 2 se activa

PASO 4 — story_arc fallback fix
  → Crear DESCRIPTIONS_BY_GENRE en story_arc.py
  → Reemplazar create_default_story_arc placeholder con descripciones reales
  → Test: sin API key → arc tiene descripciones específicas por género

PASO 5 — _build_context fix
  → Modificar _build_context() para usar lore real del setup
  → Test: generar campaña vampire → sensory_detail menciona castillos, no "bosque"

PASO 6 — Wiring + logs
  → Conectar validación → fallback en generate_setup_with_ai()
  → Agregar log.warning con razón específica de fallback
  → Test e2e: cadena completa genera output válido
```
