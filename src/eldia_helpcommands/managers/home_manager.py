"""Player 3-slot Home persistence (`homes.json`)."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

from eldia_helpcommands.core.types import HOME_SLOTS, TeleportPoint, normalize_home_slot

if TYPE_CHECKING:
    from pathlib import Path


class HomeManager:
    """Manages up to 3 homes (`1`, `2`, `3`) per player across worlds."""

    def __init__(self, storage_path: Path, *, create_file: bool = True) -> None:
        self.storage_path = storage_path
        self.create_file = create_file
        self._homes: dict[str, dict[str, TeleportPoint]] = {}
        self.load()

    def load(self) -> None:
        """Load `homes.json` from disk."""
        if not self.storage_path.exists():
            return
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        players_raw = raw.get("players", raw) if isinstance(raw, dict) else {}
        if not isinstance(players_raw, dict):
            return
        loaded: dict[str, dict[str, TeleportPoint]] = {}
        for player_key, slots_map in players_raw.items():
            if not isinstance(slots_map, dict):
                continue
            player_slots: dict[str, TeleportPoint] = {}
            for slot_key, pt_data in slots_map.items():
                norm_slot = normalize_home_slot(str(slot_key))
                if norm_slot is not None and isinstance(pt_data, dict):
                    player_slots[norm_slot] = TeleportPoint.from_dict(pt_data)
            if player_slots:
                loaded[str(player_key)] = player_slots
        self._homes = loaded

    def save(self) -> None:
        """Save all player homes to `homes.json`."""
        if not self.create_file and not self.storage_path.exists():
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "players": {
                player_key: {slot: pt.to_dict() for slot, pt in slots.items()}
                for player_key, slots in self._homes.items()
            },
        }
        self.storage_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def set_home(
        self,
        player_key: str,
        slot: str | None,
        *,
        dimension: str,
        world_name: str,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
    ) -> tuple[str, TeleportPoint] | None:
        """Save a player's home in slot `1`, `2`, or `3`."""
        norm_slot = normalize_home_slot(slot)
        if norm_slot is None:
            return None
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
        pkey = str(player_key)
        if pkey not in self._homes:
            self._homes[pkey] = {}
        self._homes[pkey][norm_slot] = point
        self.save()
        return norm_slot, point

    def get_home(self, player_key: str, slot: str | None) -> TeleportPoint | None:
        """Retrieve a player's home in slot `1`, `2`, or `3`."""
        norm_slot = normalize_home_slot(slot)
        if norm_slot is None:
            return None
        return self._homes.get(str(player_key), {}).get(norm_slot)

    def delete_home(self, player_key: str, slot: str | None) -> bool:
        """Delete a player's home in slot `1`, `2`, or `3`."""
        norm_slot = normalize_home_slot(slot)
        if norm_slot is None:
            return False
        pkey = str(player_key)
        player_slots = self._homes.get(pkey)
        if not player_slots or norm_slot not in player_slots:
            return False
        del player_slots[norm_slot]
        if not player_slots:
            del self._homes[pkey]
        self.save()
        return True

    def list_homes(self, player_key: str) -> dict[str, TeleportPoint | None]:
        """Return an ordered dict of `{ "1": point_or_none, "2": ..., "3": ... }`."""
        player_slots = self._homes.get(str(player_key), {})
        return {slot: player_slots.get(slot) for slot in HOME_SLOTS}
