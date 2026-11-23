"""Service container wiring all managers for Eldia HelpCommands using `eldia_worlds` API."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from eldia_worlds import WorldsAPI, get_worlds_api

from eldia_helpcommands.managers.combat_manager import CombatManager
from eldia_helpcommands.managers.config_manager import ConfigManager, HelpConfig
from eldia_helpcommands.managers.home_manager import HomeManager
from eldia_helpcommands.managers.lang_manager import LangManager
from eldia_helpcommands.managers.spawn_manager import SpawnManager
from eldia_helpcommands.managers.ui_manager import HelpUIManager
from eldia_helpcommands.managers.warp_manager import WarpManager

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "CombatManager",
    "ConfigManager",
    "HelpCommandServices",
    "HelpConfig",
    "HelpUIManager",
    "HomeManager",
    "LangManager",
    "SpawnManager",
    "WarpManager",
    "WorldsAPI",
]


class HelpCommandServices:
    """Central service container for `eldia-helpcommands` integrated with `eldia_worlds.WorldsAPI`."""

    def __init__(
        self,
        data_folder: Path | None = None,
        *,
        create_files: bool = True,
        server_getter: Callable[[], Any] | None = None,
        worlds_api: WorldsAPI | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        base = Path(data_folder) if data_folder is not None else Path(".")
        self.data_folder = base
        self.config_manager = ConfigManager(base / "config.yml", create_file=create_files)
        cfg = self.config_manager.config
        self.lang = LangManager(language=cfg.language, prefix=cfg.prefix)
        self.worlds: WorldsAPI = worlds_api or get_worlds_api(server_getter=server_getter)
        self.spawn = SpawnManager(base / "spawn.json", create_file=create_files)
        self.homes = HomeManager(base / "homes.json", create_file=create_files)
        self.warps = WarpManager(base / "warps.json", create_file=create_files)
        self.combat = CombatManager(clock=clock)
        self.ui = HelpUIManager()

    @property
    def config(self) -> HelpConfig:
        return self.config_manager.config

    def reload_config(self) -> HelpConfig:
        cfg = self.config_manager.reload()
        self.lang.set_language(cfg.language)
        self.lang.prefix = cfg.prefix
        return cfg

    def cleanup_player(self, player_key: str) -> None:
        self.combat.cleanup_player(player_key)
