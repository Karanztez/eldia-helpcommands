"""Core coordinate models and validation helpers for Spawn, Homes (1-3), Warps, and Beds."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

HOME_SLOTS: tuple[str, ...] = ("1", "2", "3")
_WARP_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")


@dataclass(frozen=True)
class TeleportPoint:
    """Immutable cross-world teleport destination compatible with eldia-worlds."""

    dimension: str
    world_name: str
    x: float
    y: float
    z: float
    yaw: float = 0.0
    pitch: float = 0.0
    updated_at: float = 0.0

    @property
    def block_coords(self) -> tuple[int, int, int]:
        return (int(self.x // 1), int(self.y // 1), int(self.z // 1))

    def format_short(self) -> str:
        return f"{self.world_name} ({self.x:.1f}, {self.y:.1f}, {self.z:.1f})"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TeleportPoint:
        dim = str(data.get("dimension", "Overworld"))
        wname = str(data.get("world_name", dim))
        return cls(
            dimension=dim,
            world_name=wname,
            x=float(data["x"]),
            y=float(data["y"]),
            z=float(data["z"]),
            yaw=float(data.get("yaw", 0.0)),
            pitch=float(data.get("pitch", 0.0)),
            updated_at=float(data.get("updated_at", 0.0)),
        )


def normalize_home_slot(raw: str | None) -> str | None:
    """Normalize and validate a home slot number ('1', '2', or '3'), or None if invalid."""
    if raw is None or not raw.strip():
        return "1"
    tok = raw.strip().lower()
    if tok.startswith("home"):
        tok = tok[4:].strip()
    if tok not in HOME_SLOTS:
        return None
    return tok


def normalize_warp_name(raw: str | None) -> str | None:
    """Normalize and validate a warp identifier, or None if invalid."""
    if raw is None:
        return None
    clean = raw.strip().lower()
    if not clean or not _WARP_NAME_RE.match(clean):
        return None
    return clean


def is_bed_block(block_type: str) -> bool:
    """Return True if a Bedrock block type identifier represents a bed block."""
    low = block_type.strip().lower()
    if "bedrock" in low:
        return False
    return low == "minecraft:bed" or low.endswith("_bed") or low == "bed"
