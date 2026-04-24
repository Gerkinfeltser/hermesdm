"""
bot/version.py — HermesDM version reader.

Reads VERSION file and returns version info.
No external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Version:
    """HermesDM version info."""

    version: str   # "1.0.2"
    bundled: str   # "2025-04-24"
    build: str     # "git:feat/narrative-fix@2763c8a" or "dev"

    @property
    def is_release(self) -> bool:
        """True if this is a released build with git info."""
        return self.build.startswith("git:")

    @property
    def short(self) -> str:
        """Short version string for display: 'v1.0.2'."""
        return f"v{self.version}"

    def __str__(self) -> str:
        return self.short


def _find_version_file() -> Path | None:
    """Locate VERSION file relative to this file (works from anywhere)."""
    # bot/version.py → hermesdm/VERSION
    base = Path(__file__).resolve().parent.parent
    vf = base / "VERSION"
    if vf.exists():
        return vf
    return None


def get_version() -> Version:
    """
    Read and parse the VERSION file.

    Returns:
        Version with sane defaults if file is missing or malformed.
    """
    defaults = Version(version="dev", bundled="unknown", build="dev")

    vf = _find_version_file()
    if vf is None:
        return defaults

    data: dict[str, str] = {}
    try:
        content = vf.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                data[key.strip()] = value.strip()
    except Exception:
        return defaults

    if not data:
        return defaults

    return Version(
        version=data.get("VERSION", defaults.version),
        bundled=data.get("BUNDLED", defaults.bundled),
        build=data.get("BUILD", defaults.build),
    )


def format_full(v: Version) -> str:
    """Full format for /version command."""
    lines = [
        "🤖 *HermesDM*",
        f"Versión:  `{v.short}`",
        f"Build:    `{v.build}`",
        f"Bundled:  {v.bundled}",
    ]
    return "\n".join(lines)


def format_startup(v: Version, campaign_active: bool = False) -> str:
    """Short format for startup announcement."""
    status = "campaña activa" if campaign_active else "sin campaña activa"
    return f"🎲 HermesDM {v.short} — {status}"
