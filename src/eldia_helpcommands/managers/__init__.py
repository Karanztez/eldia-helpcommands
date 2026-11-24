"""Service container wiring all managers for Eldia HelpCommands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

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
]


class _FallbackWorldsAPI:
    """Fallback world/dimension helper used when `endstone-eldia-worlds>=0.2.1` is not installed."""

    def __init__(self, server_getter: Callable[[], Any] | None = None) -> None:
        self._server_getter = server_getter

    @property
    def server(self) -> Any:
        return self._server_getter() if self._server_getter is not None else None

    def _eldia_worlds_plugin(self) -> Any:
        srv = self.server
        pm = getattr(srv, "plugin_manager", None) if srv is not None else None
        if pm is None:
            return None
        for pname in ("eldia_worlds", "eldia-worlds"):
            try:
                plug = pm.get_plugin(pname)
                if plug is not None:
                    return plug
            except Exception as exc:  # noqa: BLE001
                _ = exc
        return None

    def detect_world_name(self, dimension_name: str, x: float, z: float) -> str:
        plug = self._eldia_worlds_plugin()
        reg = getattr(plug, "registry", None) if plug is not None else None
        if reg is not None:
            find_at = getattr(reg, "find_world_at", None)
            if callable(find_at):
                try:
                    vw = find_at(dimension_name.lower(), x, z)
                    if vw is not None and getattr(vw, "name", ""):
                        return str(vw.name)
                except Exception as exc:  # noqa: BLE001
                    _ = exc
        return dimension_name or "Overworld"

    def set_world_spawn(
        self,
        world_name: str,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
        *,
        dimension: str | None = None,
    ) -> Any:
        plug = self._eldia_worlds_plugin()
        reg = getattr(plug, "registry", None) if plug is not None else None
        if reg is None:
            return None
        get_vw = getattr(reg, "get", None)
        vw = get_vw(world_name) if callable(get_vw) else None
        if vw is None:
            return None
        if dimension:
            vw.dimension = dimension.lower()
        vw.spawn_x = float(x)
        vw.spawn_y = float(y)
        vw.spawn_z = float(z)
        vw.spawn_yaw = float(yaw)
        vw.spawn_pitch = float(pitch)
        save_fn = getattr(reg, "save", None)
        if callable(save_fn):
            save_fn()
        return vw

    def resolve_dimension(self, dimension_or_world: str) -> Any:
        srv = self.server
        level = getattr(srv, "level", None) if srv is not None else None
        if level is None:
            return None
        target_key = dimension_or_world
        plug = self._eldia_worlds_plugin()
        reg = getattr(plug, "registry", None) if plug is not None else None
        if reg is not None and callable(getattr(reg, "get", None)):
            vw = reg.get(dimension_or_world)
            if vw is not None and getattr(vw, "dimension", ""):
                target_key = str(vw.dimension)

        get_dim = getattr(level, "get_dimension", None)
        if callable(get_dim):
            for candidate in (target_key, target_key.lower(), target_key.upper()):
                try:
                    dim = get_dim(candidate)
                    if dim is not None:
                        return dim
                except Exception as exc:  # noqa: BLE001
                    _ = exc
        dims = getattr(level, "dimensions", None)
        if dims is not None:
            low = target_key.lower()
            for d in dims:
                d_name = str(getattr(d, "name", "")).lower()
                if d_name == low or d_name.endswith(f":{low}"):
                    return d
        return None

    def teleport_player(
        self,
        player: Any,
        *,
        world_name: str,
        dimension: str,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
    ) -> bool:
        if hasattr(player, "teleport_to_coords") and callable(player.teleport_to_coords):
            return bool(
                player.teleport_to_coords(
                    dimension=dimension,
                    world_name=world_name,
                    x=x,
                    y=y,
                    z=z,
                    yaw=yaw,
                    pitch=pitch,
                ),
            )
        dim = (
            self.resolve_dimension(world_name)
            or self.resolve_dimension(dimension)
            or getattr(player, "dimension", None)
        )
        try:
            from endstone.level import Location

            try:
                loc = Location(dim, float(x), float(y), float(z), float(pitch), float(yaw))
            except TypeError:
                loc = Location(float(x), float(y), float(z), float(yaw), float(pitch), dim)
            res = player.teleport(loc)
            return True if res is None else bool(res)
        except Exception as exc:  # noqa: BLE001
            _ = exc
            return False

    def is_block_matching_near(
        self,
        dimension: str,
        world_name: str,
        x: float,
        y: float,
        z: float,
        predicate: Callable[[str], bool],
    ) -> bool:
        dim = self.resolve_dimension(dimension) or self.resolve_dimension(world_name)
        if dim is None:
            return self.server is None
        get_block_at = getattr(dim, "get_block_at", None)
        if not callable(get_block_at):
            return True
        bx = round(x - 0.5) if x != int(x) else int(x)
        by = int(y)
        bz = round(z - 0.5) if z != int(z) else int(z)
        for dy in (0, -1, 1):
            for dx in (0, -1, 1):
                for dz in (0, -1, 1):
                    try:
                        block = get_block_at(bx + dx, by + dy, bz + dz)
                        if predicate(str(getattr(block, "type", ""))):
                            return True
                    except Exception as exc:  # noqa: BLE001
                        _ = exc
        return False


def _resolve_worlds_api(server_getter: Callable[[], Any] | None) -> Any:
    try:
        from eldia_worlds import get_worlds_api

        return get_worlds_api(server_getter=server_getter)
    except ImportError:
        return _FallbackWorldsAPI(server_getter=server_getter)


class HelpCommandServices:
    """Central service container for `eldia-helpcommands` integrated with `eldia_worlds.WorldsAPI`."""

    def __init__(
        self,
        data_folder: Path | None = None,
        *,
        create_files: bool = True,
        server_getter: Callable[[], Any] | None = None,
        worlds_api: Any = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        base = Path(data_folder) if data_folder is not None else Path(".")
        self.data_folder = base
        self.config_manager = ConfigManager(base / "config.yml", create_file=create_files)
        cfg = self.config_manager.config
        self.lang = LangManager(language=cfg.language, prefix=cfg.prefix)
        self.worlds: Any = worlds_api if worlds_api is not None else _resolve_worlds_api(server_getter)
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
