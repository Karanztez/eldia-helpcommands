"""Main Server Spawn and Player Bed Respawn persistence (`spawn.json`)."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

from eldia_helpcommands.core.types import TeleportPoint

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class SpawnManager:
    """Manages the Main Server Spawn (`/setspawn`, `/spawn`) and Player Bed Respawns."""

    def __init__(self, storage_path: Path, *, create_file: bool = True) -> None:
        self.storage_path = storage_path
        self.create_file = create_file
        self.main_spawn: TeleportPoint | None = None
        self.bed_spawns: dict[str, TeleportPoint] = {}
        self.load()

    def load(self) -> None:
        """Load `spawn.json` from disk."""
        if not self.storage_path.exists():
            return
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        main_raw = raw.get("main_spawn")
        if isinstance(main_raw, dict):
            self.main_spawn = TeleportPoint.from_dict(main_raw)

        beds_raw = raw.get("bed_spawns")
        if isinstance(beds_raw, dict):
            loaded_beds: dict[str, TeleportPoint] = {}
            for player_key, bed_data in beds_raw.items():
                if isinstance(bed_data, dict):
                    loaded_beds[str(player_key)] = TeleportPoint.from_dict(bed_data)
            self.bed_spawns = loaded_beds

    def save(self) -> None:
        """Persist `main_spawn` and `bed_spawns` to `spawn.json`."""
        if not self.create_file and not self.storage_path.exists():
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "main_spawn": self.main_spawn.to_dict() if self.main_spawn is not None else None,
            "bed_spawns": {k: v.to_dict() for k, v in self.bed_spawns.items()},
        }
        self.storage_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def set_main_spawn(
        self,
        *,
        dimension: str,
        world_name: str,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
    ) -> TeleportPoint:
        """Set the global Main Server Spawn (whatever world `/setspawn` is executed in)."""
        point = TeleportPoint(
            dimension=dimension,
            world_name=world_name or dimension,
            x=round(float(x), 3),
            y=round(float(y), 3),
            z=round(float(z), 3),
            yaw=round(float(yaw), 2),
            pitch=round(float(pitch), 2),
            updated_at=time.time(),
        )
        self.main_spawn = point
        self.save()
        return point

    def get_main_spawn(self) -> TeleportPoint | None:
        """Return the current Main Server Spawn point, or `None` if not configured."""
        return self.main_spawn

    def set_bed_spawn(
        self,
        player_key: str,
        *,
        dimension: str,
        world_name: str,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
    ) -> TeleportPoint:
        """Record a player's saved bed respawn location."""
        point = TeleportPoint(
            dimension=dimension,
            world_name=world_name or dimension,
            x=round(float(x), 3),
            y=round(float(y), 3),
            z=round(float(z), 3),
            yaw=round(float(yaw), 2),
            pitch=round(float(pitch), 2),
            updated_at=time.time(),
        )
        self.bed_spawns[str(player_key)] = point
        self.save()
        return point

    def get_bed_spawn(self, player_key: str) -> TeleportPoint | None:
        """Return a player's saved bed location if one exists."""
        return self.bed_spawns.get(str(player_key))

    def clear_bed_spawn(self, player_key: str) -> bool:
        """Remove a player's saved bed location."""
        key = str(player_key)
        if key in self.bed_spawns:
            del self.bed_spawns[key]
            self.save()
            return True
        return False

    def clear_beds_near(self, dimension: str, x: float, y: float, z: float, radius: float = 2.5) -> int:
        """Clear any saved bed spawns within `radius` blocks of a broken bed block."""
        dim_low = dimension.lower()
        to_remove: list[str] = []
        r_sq = radius * radius
        for key, pt in self.bed_spawns.items():
            if pt.dimension.lower() != dim_low and pt.world_name.lower() != dim_low:
                continue
            dist_sq = (pt.x - x) ** 2 + (pt.y - y) ** 2 + (pt.z - z) ** 2
            if dist_sq <= r_sq:
                to_remove.append(key)
        for key in to_remove:
            del self.bed_spawns[key]
        if to_remove:
            self.save()
        return len(to_remove)

    def resolve_respawn_point(
        self,
        player_key: str,
        bed_verifier: Callable[[TeleportPoint], bool] | None = None,
    ) -> tuple[TeleportPoint | None, str]:
        """Resolve where a player should respawn after death.

        Returns `(point, reason)` where `reason` is one of:
        - `"bed"`: Player has a valid saved bed and respawns at their bed.
        - `"bed_missing"`: Player had a saved bed, but the bed block was broken;
          bed record is cleared and player falls back to `main_spawn`.
        - `"spawn"`: Player has no saved bed; respawns at `main_spawn`.
        - `"none"`: Neither bed nor `main_spawn` is configured.
        """
        bed = self.get_bed_spawn(player_key)
        if bed is not None:
            if bed_verifier is None or bed_verifier(bed):
                return bed, "bed"
            self.clear_bed_spawn(player_key)
            if self.main_spawn is not None:
                return self.main_spawn, "bed_missing"
            return None, "none"

        if self.main_spawn is not None:
            return self.main_spawn, "spawn"
        return None, "none"
