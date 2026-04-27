# SPEC — Genre-Free Setup Generation

## Status: DRAFT

---

## 1. Problema

El sistema actual de validación de género es keyword-based y frágil:

```
Usuario:    "samurais en el Japón feudal"
Genre detection → "fantasy" (samurai no tiene keyword propio)
AI genera → contenido SAMURAI (correcto)
Genre validation → FALLA porque contenido no tiene {dragon,mago,reino}
Layer 3 fallback → regenera contenido GENÉRICO
Error final → "Layer 3: AI returned invalid JSON"
```

Cada género que no está en `_GENRE_KEYWORDS` rompe el flujo. Agregar keywords
es una cola sin fin: samurai, hombres lobo, vaqueros, cyberpunk...

**Raíz del problema:** la validación de género compara el contenido generado contra
una lista hardcodeada de palabras. Esto es fundamentalmente incorrecto.

---

## 2. Goal

Reemplazar la validación keyword-based con un sistema donde:

- El input del usuario es el contexto de género primario
- La AI genera contenido coerente con lo pedido sin necesidad de keywords
- No hay lista de keywords a mantener
- El sistema funciona con cualquier género que el usuario invente

---

## 3. Arquitectura propuesta

### 3.1 Flujo actual (roto)

```
Input → detect_genre → setting → prompt con setting
                                          ↓
                              Layer 1: AI genera
                                          ↓
                              _validate_genre_presence ← valida contra keywords hardcodeadas
                                          ↓ (si falla)
                              Layer 3: fallback
                                          ↓
                              Error: "invalid JSON"
```

### 3.2 Flujo propuesto (sin genre validation)

```
Input → detect_genre → solo para TEMPLATE/CLASSES
                  ↓
         Layer 1: AI genera con CONTEXTO del input original
                  ↓
         ¿Parse OK? → YES → return setup
                  ↓ NO
         Layer 2: _try_close_json → reparsing
                  ↓ (si falla)
         Layer 3: fallback con input original + sin genre validation
                  ↓
         Error real (JSON o API)
```

**Cambio clave:** la validación de género NO existe más como gate.
El genre detection solo se usa para:
1. Seleccionar template de world-building (fantasy, horror, scifi)
2. Generar classes del setting
3. Filtrar NPCs temáticos

Si el usuario pide "samurais en Japón feudal", la AI recibe el input completo
como contexto y genera contenido samurai. No hay keyword checking.

---

## 4. Qué se elimina

### 4.1 `_validate_genre_presence`

```python
# ELIMINADO — demasiado frágil, keyword-based
def _validate_genre_presence(setup: dict, genre: str) -> list[str]:
    ...
```

Ya no se llama en ningún layer. Se elimina completamente.

### 4.2 `_GENRE_KEYWORDS`

```python
# ELIMINADO — mantenimiento manual insostenible
_GENRE_KEYWORDS = {
    "fantasy": {"dragon", "mago", ...},
    "horror": {"oscuridad", ...},
    ...
}
```

### 4.3 Genre validation en Layer 1

Las líneas ~448-458 de `world_builder.py` se eliminan:

```python
# DELETE THIS BLOCK:
genre_errors = _validate_genre_presence(setup, setting)
if genre_errors:
    raise ValueError(f"Genre validation failed for '{setting}': ...")
```

---

## 5. Qué se modifica

### 5.1 `generate_setup_with_ai`

**Firma:** sin cambios (mantener backwards compatibility)

**Parámetros:** `description`, `tone`, `setting`, `pacing_level`

**Capas:**
- **Layer 1:** AI generation con prompt que incluye el input del usuario como contexto de género
- **Layer 2:** JSON repair con `_try_close_json`
- **Layer 3:** Simplified fallback, SIN genre validation, usa el mismo prompt base

**Ya no se valida género contra keywords en ningún layer.**

### 5.2 Genre detection (para templates)

Se mantiene `_detect_genre_from_description` para seleccionar el template de world-building.

Este genre detection es DIFERENTE de la validación eliminada:
- Se usa SOLO para elegir qué template usar (fantasy vs horror vs scifi)
- Si no matchea ninguno → usa "fantasy" como default
- No bloquea nada — solo categoriza

### 5.3 `build_world` y templates

Sin cambios. Los templates de world-building (npcs, locations, quests) siguen
funcionando con setting types (fantasy, horror, scifi, etc).

---

## 6. Compatibilidad hacia atrás

El parámetro `setting` de `generate_setup_with_ai` se mantiene:
- Valores aceptados: "fantasy", "horror", "scifi", "zombie", "pirates", o cualquier string
- Si el usuario especifica un setting → se usa ese
- Si no → se detecta del input

El campo `setting_type` en el output sigue existiendo.

---

## 7. Efectos en el resto del sistema

| Componente | Efecto |
|-----------|--------|
| `world_builder.py` | Elimina `_validate_genre_presence`, `_GENRE_KEYWORDS`, genre validation en Layer 1 |
| `telegram_handler.py` | Sin cambios |
| `narrative_generator.py` | Sin cambios |
| `state/` | Sin cambios |
| Tests existentes | `test_world_builder.py` — 18 tests deben pasar. `test_world_builder_echo.py` — algunos tests que mockean genre validation necesitan actualizarse |

---

## 8. Tests requeridos

### 8.1 Tests nuevos

```python
def test_samurai_input_generates_content():
    """Usuario pide samurai → contenido samurai, sin genre validation error."""
    # Mock API para devolver contenido samurai
    # Verificar que no lanza ValueError de genre validation
    result = generate_setup_with_ai("samurais en el Japón feudal")
    assert "samurai" in result["premise"].lower() or "japón" in result["premise"].lower() or ...

def test_werewolf_input_generates_content():
    """Usuario pide hombres lobo → contenido licántropo, sin genre validation error."""
    ...

def test_pirates_input_generates_content():
    """Usuario pide piratas → contenido pirata, sin genre validation error."""
    ...

def test_custom_genre_works():
    """Género inventado por usuario → funciona sin error."""
    result = generate_setup_with_ai("espías victorianos en Londres")
    assert result is not None
```

### 8.2 Tests a actualizar en `test_world_builder_echo.py`

Los tests de genre validation en Layer 1 ya no aplican:
- `test_fallback_detects_dark_tone` → verificar que sigue funcionando (tone, no genre)
- `test_fallback_generates_original_premise_from_nouns` → re-evaluar assertions

---

## 9. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Sin genre validation, la AI puede generar contenido fuera de setting | El prompt sigue pidiendo contenido coerente con el input. Si el usuario dice "samurai", la AI sabe que es samurai. |
| Templates de world-building no aplican a géneros inventados | Los templates se usan como fallback de contenido (NPCs, locations). Si el género es "samurai", los NPCs serían genéricos pero el contenido principal viene de la AI. |
| Genre detection para templates se rompe | Solo se usa para categorización, no para validación. Si detecta mal, usa "fantasy" como default. No rompe nada. |

---

## 10. Implementación plan

### Fase 1: Eliminar validación (fix mínimo, bajo riesgo)
1. Eliminar `_validate_genre_presence`
2. Eliminar `_GENRE_KEYWORDS`
3. Eliminar genre validation block en Layer 1 (~448-458)
4. Correr tests existentes
5. Commit: "refactor: remove keyword-based genre validation"

### Fase 2: Tests de regresión
1. Escribir tests para samurai, werewolf, piratas, géneros inventados
2. Verificar que Layer 1 y Layer 3 funcionan
3. Commit: "test: add genre-free regression tests"

### Fase 3: Limpieza (opcional)
1. Eliminar función `_detect_genre_from_description` si no se usa en ningún lado
2. Verificar que no hay imports huérfanos
3. Commit: "chore: remove unused genre detection code"

---

## 11. Métricas de éxito

- `/setup samurais en Japón feudal` → genera contenido samurai, sin errores
- `/setup hombres lobo en Transilvania` → genera contenido licántropo, sin errores
- `/setup piratas buscando tesoro` → genera contenido pirata, sin errores
- Tests: 18/18 passing en `test_world_builder.py`
- Tests: 20+/20+ passing en `test_world_builder_echo.py`
