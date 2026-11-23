"""Cross-world Warp persistence (`warps.json`)."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

from eldia_helpcommands.core.types import TeleportPoint, normalize_warp_name

if TYPE_CHECKING:
    from pathlib import Path


class WarpManager:
    """Manages named server warps (`/setwarp`, `/delwarp`, `/warp`) across `eldia-worlds`."""

    def __init__(self, storage_path: Path, *, create_file: bool = True) -> None:
        self.storage_path = storage_path
        self.create_file = create_file
        self._warps: dict[str, TeleportPoint] = {}
        self.load()

    def load(self) -> None:
        """Load `warps.json` from disk."""
        if not self.storage_path.exists():
            return
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        warps_raw = raw.get("warps", raw) if isinstance(raw, dict) else {}
        if not isinstance(warps_raw, dict):
            return
        loaded: dict[str, TeleportPoint] = {}
        for name, pt_data in warps_raw.items():
            norm = normalize_warp_name(str(name))
            if norm is not None and isinstance(pt_data, dict):
                loaded[norm] = TeleportPoint.from_dict(pt_data)
        self._warps = loaded

    def save(self) -> None:
        """Persist all warps to `warps.json`."""
        if not self.create_file and not self.storage_path.exists():
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "warps": {name: pt.to_dict() for name, pt in sorted(self._warps.items())},
        }
        self.storage_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def set_warp(
        self,
        name: str,
        *,
        dimension: str,
        world_name: str,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
    ) -> tuple[str, TeleportPoint] | None:
        """Create or update a cross-world warp point."""
        norm = normalize_warp_name(name)
        if norm is None:
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
        self._warps[norm] = point
        self.save()
        return norm, point

    def get_warp(self, name: str) -> TeleportPoint | None:
        """Retrieve a warp by name (case-insensitive)."""
        norm = normalize_warp_name(name)
        if norm is None:
            return None
        return self._warps.get(norm)

    def delete_warp(self, name: str) -> bool:
        """Delete a warp by name."""
        norm = normalize_warp_name(name)
        if norm is None or norm not in self._warps:
            return False
        del self._warps[norm]
        self.save()
        return True

    def list_warps(self) -> dict[str, TeleportPoint]:
        """Return all warps sorted by name."""
        return dict(sorted(self._warps.items()))
