# SPEC — HermesDM Version Announcement on Startup

## Status: PROPOSED

---

## 1. CONTEXTO Y PROBLEMA

### Problema

Cuando Sherman reinicia el bot, no sabe si está corriendo código nuevo o viejo.
El log dice `HermesDM bot starting...` pero no dice qué versión.

**Situación real:**
```
hermes    563205  ... /home/hermes/hermes-agent/venv/bin/python3 -m bot.telegram_handler
# → ¿Es 1.0.1? ¿1.0.2? ¿El código nuevo con los fixes de narrative?
```

### Decisión de diseño

- **Minimal**: solo anuncia la versión en startup, sin cambios en el runtime.
- **Un source of truth**: el VERSION vive en un solo lugar (`VERSION` file en el repo),
  no en múltiples lugares (pyproject.toml + code + git tag).
- **No requiere git**: se puede determinar la versión desde el VERSION file
  sin necesidad de git describe o git log.

---

## 2. DISEÑO

### Source of truth: `VERSION` file

```
hermesdm/VERSION
```
```
VERSION=1.0.2
BUNDLED=2025-04-24
BUILD=git:feat/narrative-fix@2763c8a
```

Formato: clave=valor, una por línea. Líneas que no son `KEY=VALUE` son ignoradas.

### Comandos

| Qué | Dónde | Cómo |
|---|---|---|
| Leer versión | Código Python | `from bot.version import get_version; get_version()` |
| Leer versión | Bash/shell | `cat hermesdm/VERSION` |
| Cambiar versión | Humano | Editar `VERSION` file |
| Version bump | CI/CD | `echo "VERSION=1.0.3" > hermesdm/VERSION` |

### Qué announce la versión

**On bot startup** (primera línea del log + mensaje al grupo configurado):

```
🎲 HermesDM v1.0.2 — campaña activa: False
```

**On `/version` command**:

```
🤖 HermesDM
Versión: 1.0.2
Build:   feat/narrative-fix (git:2763c8a)
Bundled: 2025-04-24
```

**On `/newgame` inicio de campaña**:

```
🎲 HermesDM v1.0.2 — nueva campaña iniciada
```

---

## 3. ARQUITECTURA

### Estructura propuesta

```
hermesdm/
├── VERSION                     ← Source of truth (NUEVO)
├── bot/
│   ├── __init__.py            ← Mover get_version aquí
│   └── version.py             ← NUEVO: parser de VERSION
├── bot/telegram_handler.py     → cmd_version (NUEVO handler)
├── bot/main.py o __main__.py  → announce_version() al iniciar
```

### 3.1 `bot/version.py` — Parser minimal

```python
"""
bot/version.py — HermesDM version reader.

Lee VERSION file y retorna version info.
No tiene dependencias externas.
"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass

VERSION_FILE = Path(__file__).parent.parent / "VERSION"


@dataclass
class Version:
    version: str       # "1.0.2"
    bundled: str       # "2025-04-24"
    build: str         # "git:feat/narrative-fix@2763c8a" o "dev"
    
    @property
    def is_release(self) -> bool:
        """True si es un build con git info (no dev)."""
        return self.build.startswith("git:")
    
    @property
    def short(self) -> str:
        """Versión corta para display: 'v1.0.2'."""
        return f"v{self.version}"
    
    def __str__(self) -> str:
        return self.short


def get_version() -> Version:
    """
    Lee y parsea el VERSION file.
    
    Returns:
        Version con defaults si el archivo no existe o está malformado.
    """
    defaults = Version(version="dev", bundled="unknown", build="dev")
    
    if not VERSION_FILE.exists():
        return defaults
    
    data: dict[str, str] = {}
    try:
        content = VERSION_FILE.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                data[key.strip()] = value.strip()
    except Exception:
        return defaults
    
    return Version(
        version=data.get("VERSION", defaults.version),
        bundled=data.get("BUNDLED", defaults.bundled),
        build=data.get("BUILD", defaults.build),
    )


def format_full(version: Version) -> str:
    """Formato completo para /version command."""
    lines = [
        "🤖 *HermesDM*",
        f"Versión: `{version.short}`",
        f"Build:   `{version.build}`",
        f"Bundled: {version.bundled}",
    ]
    return "\n".join(lines)


def format_startup(version: Version, campaign_active: bool = False) -> str:
    """Formato corto para announce de startup."""
    status = "campaña activa" if campaign_active else "sin campaña activa"
    return f"🎲 HermesDM {version.short} — {status}"
```

### 3.2 `VERSION` file

```
VERSION=1.0.2
BUNDLED=2025-04-24
BUILD=git:feat/narrative-fix@2763c8a
```

**Regla**: BUILD="dev" cuando se está trabajando en local sin git info.
BUILD="git:..." cuando se hizo `hermes update` o git describe.

### 3.3 Wire-in en telegram_handler.py

**a) Handler `/version`**

```python
async def cmd_version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /version — muestra versión del bot."""
    from bot.version import get_version, format_full
    v = get_version()
    await update.message.reply_text(
        format_full(v),
        parse_mode=ParseMode.MARKDOWN,
    )
```

Registrar en `build_app()`:

```python
app.add_handler(CommandHandler("version", cmd_version))
```

**b) Anuncio en startup**

En `main()`:

```python
def main() -> None:
    logging.basicConfig(...)
    
    from bot.version import get_version, format_startup
    
    v = get_version()
    log.info(f"HermesDM {v.short} starting...")  # Ya sale en log
    
    app = build_app()
    
    # Anunciar al grupo si ALLOWED_GROUP_ID está configurado
    settings = load_settings()
    if settings.ALLOWED_GROUP_ID:
        async def _announce():
            await app.bot.send_message(
                chat_id=settings.ALLOWED_GROUP_ID,
                text=format_startup(v),
                parse_mode=ParseMode.MARKDOWN,
            )
        #.schedule announcement after bot is ready
        app.post_init = _announce  # O usar job_queue.run_once con delay=5
    
    app.run_polling(...)
```

### 3.4 Actualizar `main.py`

```python
# main.py — entry point
if __name__ == "__main__":
    from bot.version import get_version
    v = get_version()
    print(f"HermesDM {v.short} — starting...")
    from bot.telegram_handler import main
    main()
```

---

## 4. MIGRACIÓN DEL VERSION FILE EXISTENTE

**Archivo actual en `~/hermesdm/profile/VERSION`**:

```
VERSION=25.04
BUNDLED=2025-04-22
SPEC=SPEC_HERMESDM_PROFILE.md
```

**Migrar a `~/hermesdm/VERSION`** (raíz del repo):

```
VERSION=1.0.2
BUNDLED=2025-04-24
BUILD=dev
```

Notas:
- `SPEC=...` se remueve — ya no es relevante en el VERSION file.
- `BUILD=dev` indica trabajo en curso. En release, BUILD="git:tag@hash".
- El VERSION file del repo se commitea; `.env` del profile no tiene versión.

---

## 5. CRITERIOS DE ACEPTACIÓN

```
═══════════════════════════════════════════════════
V1: Version file existe y es parseable
═══════════════════════════════════════════════════
  [ ] `cat hermesdm/VERSION` retorna clave=valor
  [ ] `python -c "from bot.version import get_version; print(get_version())"` 
      imprime v{VERSION}

═══════════════════════════════════════════════════
V2: /version command responde en Telegram
═══════════════════════════════════════════════════
  [ ] /version → mensaje con versión, build, bundled
  [ ] El mensaje usa parse_mode=Markdown

═══════════════════════════════════════════════════
V3: Startup log incluye versión
═══════════════════════════════════════════════════
  [ ] `log.info("HermesDM {v.short} starting...")` aparece en logs
  [ ] Si ALLOWED_GROUP_ID existe → bot envía mensaje al grupo con versión

═══════════════════════════════════════════════════
V4: Defaults sane
═══════════════════════════════════════════════════
  [ ] Si VERSION file no existe → get_version() retorna "dev"
  [ ] Si VERSION file está vacío → get_version() retorna "dev"
  [ ] No lanza exceptions en ningún caso

═══════════════════════════════════════════════════
V5: El campo BUILD se actualiza en hermes update
═══════════════════════════════════════════════════
  [ ] `hermes update` setea BUILD="git:{branch}@{hash}" en el VERSION file
  [ ] El hash es corto (7 chars): 2763c8a
```

---

## 6. PLAN DE IMPLEMENTACIÓN

```
PASO 1 — VERSION file
  → Crear hermesdm/VERSION con VERSION=1.0.2, BUILD=dev, BUNDLED=2025-04-24
  → Commitear al repo

PASO 2 — bot/version.py
  → Crear parser minimal con defaults sane
  → Test: importar y verificar que retorna Version

PASO 3 — cmd_version handler
  → Agregar cmd_version() en telegram_handler.py
  → Registrar en build_app()
  → Test: /version responde en grupo

PASO 4 — Startup announcement
  → Agregar format_startup() call en main()
  → Si ALLOWED_GROUP_ID → job_queue.run_once con delay=3 para anunciar al grupo
  → Test: reiniciar bot → mensaje aparece en grupo

PASO 5 — Log con versión
  → Cambiar "HermesDM bot starting..." → "HermesDM {v.short} starting..."
  → Test: grep logs

PASO 6 — Update BUILD en git pull
  → Hook o script en hermes update que actualice BUILD=git:{branch}@{hash}
  → Opcional por ahora (BUILD=dev mientras no esté merged)
```
