"""YAML configuration loader for Eldia HelpCommands (`config.yml`)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_BLOCKED_TAGS: tuple[str, ...] = (
    "in_event",
    "event",
    "combat",
    "busy",
    "arena",
    "duel",
    "minigame",
)

DEFAULT_CONFIG_YAML = """\
# Eldia HelpCommands Configuration
# Language: "th" (Thai) or "en" (English)
language: th

# Chat message prefix
prefix: "[EHC]"

# Combat tag duration in seconds after dealing or taking damage
combat_tag_seconds: 15.0

# Cooldown in seconds after an active event / interaction lock
event_cooldown_seconds: 3.0

# Cooldown in seconds between teleport commands (/spawn, /home, /warp)
teleport_cooldown_seconds: 3.0

# Maximum number of home slots per player (1, 2, 3)
max_homes: 3

# Tag players in combat on any damage (including mobs/fall/hazards), not only PvP
tag_all_damage: true

# If true, only player-vs-player damage activates combat lock
pvp_only: false

# Block teleport commands while in lava or gliding hazard
block_in_hazard: true

# Scoreboard tags that indicate a player is currently inside an active event/minigame
blocked_scoreboard_tags: th_default
"""


def _parse_bool(val: str, *, default: bool = True) -> bool:
    low = val.strip().lower()
    if low in {"true", "yes", "1", "on"}:
        return True
    if low in {"false", "no", "0", "off"}:
        return False
    return default


def _parse_float(val: str, *, default: float) -> float:
    try:
        return max(0.0, float(val.strip()))
    except ValueError:
        return default


def _parse_int(val: str, *, default: int) -> int:
    try:
        return max(1, int(val.strip()))
    except ValueError:
        return default


@dataclass(slots=True)
class HelpConfig:
    """Runtime configuration settings for Eldia HelpCommands."""

    language: str = "th"
    prefix: str = "[EHC]"
    combat_tag_seconds: float = 15.0
    event_cooldown_seconds: float = 3.0
    teleport_cooldown_seconds: float = 3.0
    max_homes: int = 3
    tag_all_damage: bool = True
    pvp_only: bool = False
    block_in_hazard: bool = True
    blocked_scoreboard_tags: tuple[str, ...] = DEFAULT_BLOCKED_TAGS


class ConfigManager:
    """Loads and saves `config.yml` without external YAML dependencies."""

    def __init__(self, config_path: Path, *, create_file: bool = True) -> None:
        self.config_path = config_path
        self.create_file = create_file
        self.config = HelpConfig()
        self.reload()

    def reload(self) -> HelpConfig:
        """Read `config.yml` from disk (creating default if missing)."""
        if not self.config_path.exists():
            if self.create_file:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                self.config_path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
            self.config = HelpConfig()
            return self.config

        raw = self.config_path.read_text(encoding="utf-8")
        cfg = HelpConfig()
        for raw_line in raw.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip()
            if "#" in val and not val.startswith(('"', "'")):
                val = val.split("#", 1)[0].strip()
            val = val.strip("\"'")

            if key in {"language", "lang"}:
                cfg.language = val.lower() if val.lower() in {"th", "en"} else "th"
            elif key == "prefix":
                if val:
                    cfg.prefix = val
            elif key == "combat_tag_seconds":
                cfg.combat_tag_seconds = _parse_float(val, default=15.0)
            elif key == "event_cooldown_seconds":
                cfg.event_cooldown_seconds = _parse_float(val, default=3.0)
            elif key == "teleport_cooldown_seconds":
                cfg.teleport_cooldown_seconds = _parse_float(val, default=3.0)
            elif key == "max_homes":
                cfg.max_homes = min(3, _parse_int(val, default=3))
            elif key == "tag_all_damage":
                cfg.tag_all_damage = _parse_bool(val, default=True)
            elif key == "pvp_only":
                cfg.pvp_only = _parse_bool(val, default=False)
            elif key == "block_in_hazard":
                cfg.block_in_hazard = _parse_bool(val, default=True)
            elif key == "blocked_scoreboard_tags" and val and val != "th_default":
                tags = tuple(
                    t.strip().lower()
                    for t in val.strip("[]").split(",")
                    if t.strip()
                )
                if tags:
                    cfg.blocked_scoreboard_tags = tags

        self.config = cfg
        return cfg

    def save_language(self, lang: str) -> None:
        """Persist updated language setting to `config.yml`."""
        norm = lang.lower() if lang.lower() in {"th", "en"} else "th"
        self.config.language = norm
        if not self.config_path.exists():
            if not self.create_file:
                return
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(
                DEFAULT_CONFIG_YAML.replace("language: th", f"language: {norm}"),
                encoding="utf-8",
            )
            return

        lines = self.config_path.read_text(encoding="utf-8").splitlines()
        out: list[str] = []
        replaced = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("language:", "lang:")):
                out.append(f"language: {norm}")
                replaced = True
            else:
                out.append(line)
        if not replaced:
            out.insert(0, f"language: {norm}")
        self.config_path.write_text("\n".join(out) + "\n", encoding="utf-8")
