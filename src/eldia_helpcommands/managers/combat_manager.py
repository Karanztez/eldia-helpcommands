"""Combat & Active Event Guard preventing teleportation during combat or server events."""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


class CombatManager:
    """Tracks combat timers, active event locks, hazards, and teleport cooldowns."""

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock: Callable[[], float] = clock or time.monotonic
        self._combat_until: dict[str, float] = {}
        self._combat_reason: dict[str, str] = {}
        self._event_locks: dict[str, str] = {}
        self._busy_until: dict[str, tuple[float, str]] = {}
        self._tp_cooldown_until: dict[str, float] = {}
        self._sleeping: set[str] = set()
        self._dead: set[str] = set()

    def now(self) -> float:
        return self._clock()

    # ── Combat Tagging ────────────────────────────────────────────────

    def tag_combat(
        self,
        player_key: str,
        duration_sec: float = 15.0,
        *,
        reason: str = "combat",
    ) -> float:
        """Tag a player as in combat for `duration_sec` seconds. Returns remaining seconds."""
        if duration_sec <= 0:
            return 0.0
        key = str(player_key)
        until = self.now() + float(duration_sec)
        prev = self._combat_until.get(key, 0.0)
        self._combat_until[key] = max(prev, until)
        self._combat_reason[key] = reason
        return max(0.0, self._combat_until[key] - self.now())

    def clear_combat(self, player_key: str) -> None:
        """Remove a player's active combat tag (e.g. on death or disconnect)."""
        key = str(player_key)
        self._combat_until.pop(key, None)
        self._combat_reason.pop(key, None)

    def get_remaining_combat(self, player_key: str) -> float:
        """Return seconds remaining on a player's combat tag (`0.0` if expired/none)."""
        key = str(player_key)
        until = self._combat_until.get(key)
        if until is None:
            return 0.0
        rem = until - self.now()
        if rem <= 0.0:
            self._combat_until.pop(key, None)
            self._combat_reason.pop(key, None)
            return 0.0
        return rem

    def is_in_combat(self, player_key: str) -> bool:
        """Return `True` if the player currently has an active combat timer."""
        return self.get_remaining_combat(player_key) > 0.0

    def handle_damage_event(
        self,
        *,
        victim_key: str | None,
        victim_is_player: bool,
        attacker_key: str | None,
        attacker_is_player: bool,
        damage: float,
        duration_sec: float,
        tag_all_damage: bool = True,
        pvp_only: bool = False,
    ) -> list[str]:
        """Process a damage event and tag involved players in combat.

        Returns a list of `player_key`s that were Newly tagged (was not already in combat).
        """
        if damage <= 0.0 or duration_sec <= 0.0:
            return []

        is_pvp = victim_is_player and attacker_is_player and victim_key != attacker_key
        if pvp_only and not is_pvp:
            return []

        newly_tagged: list[str] = []

        # Tag victim player if PvP, or if attacked by any actor/mob, or if tag_all_damage
        should_tag_victim = victim_is_player and (
            is_pvp or attacker_key is not None or tag_all_damage
        )
        if should_tag_victim and victim_key:
            was_in_combat = self.is_in_combat(victim_key)
            self.tag_combat(
                victim_key,
                duration_sec,
                reason="pvp" if is_pvp else "damage",
            )
            if not was_in_combat:
                newly_tagged.append(victim_key)

        # Tag attacker player whenever a player attacks any entity (player or mob)
        should_tag_attacker = attacker_is_player and attacker_key is not None and (
            is_pvp or not pvp_only
        )
        if should_tag_attacker and attacker_key and attacker_key != victim_key:
            was_in_combat = self.is_in_combat(attacker_key)
            self.tag_combat(
                attacker_key,
                duration_sec,
                reason="pvp" if is_pvp else "attack",
            )
            if not was_in_combat:
                newly_tagged.append(attacker_key)

        return newly_tagged

    # ── Event / Activity Locks ────────────────────────────────────────

    def set_event_lock(self, player_key: str, reason: str = "Active Event") -> None:
        """Lock a player from using teleport commands while in a server event/minigame."""
        self._event_locks[str(player_key)] = reason.strip() or "Active Event"

    def clear_event_lock(self, player_key: str) -> bool:
        """Clear a player's active event lock."""
        return self._event_locks.pop(str(player_key), None) is not None

    def get_event_lock(self, player_key: str) -> str | None:
        """Return the active event lock reason for `player_key`, or `None`."""
        return self._event_locks.get(str(player_key))

    def mark_busy_event(
        self,
        player_key: str,
        duration_sec: float = 3.0,
        *,
        reason: str = "Event Interaction",
    ) -> None:
        """Temporarily mark a player as busy in an interactive event for `duration_sec`."""
        if duration_sec <= 0.0:
            return
        self._busy_until[str(player_key)] = (self.now() + duration_sec, reason)

    def get_busy_event(self, player_key: str) -> tuple[float, str] | None:
        """Return `(remaining_seconds, reason)` if player has an active busy event timer."""
        key = str(player_key)
        entry = self._busy_until.get(key)
        if entry is None:
            return None
        until, reason = entry
        rem = until - self.now()
        if rem <= 0.0:
            self._busy_until.pop(key, None)
            return None
        return rem, reason

    # ── Player State Flags (Dead / Sleeping / Cooldown) ───────────────

    def set_sleeping(self, player_key: str, sleeping: bool) -> None:
        key = str(player_key)
        if sleeping:
            self._sleeping.add(key)
        else:
            self._sleeping.discard(key)

    def is_sleeping(self, player_key: str) -> bool:
        return str(player_key) in self._sleeping

    def set_dead(self, player_key: str, dead: bool) -> None:
        key = str(player_key)
        if dead:
            self._dead.add(key)
        else:
            self._dead.discard(key)

    def is_dead(self, player_key: str) -> bool:
        return str(player_key) in self._dead

    def record_teleport(self, player_key: str, cooldown_sec: float) -> None:
        """Start the teleport command cooldown timer for `player_key`."""
        if cooldown_sec <= 0.0:
            return
        self._tp_cooldown_until[str(player_key)] = self.now() + cooldown_sec

    def get_remaining_cooldown(self, player_key: str) -> float:
        key = str(player_key)
        until = self._tp_cooldown_until.get(key)
        if until is None:
            return 0.0
        rem = until - self.now()
        if rem <= 0.0:
            self._tp_cooldown_until.pop(key, None)
            return 0.0
        return rem

    def cleanup_player(self, player_key: str) -> None:
        """Clean up transient state when a player quits."""
        key = str(player_key)
        self._combat_until.pop(key, None)
        self._combat_reason.pop(key, None)
        self._busy_until.pop(key, None)
        self._tp_cooldown_until.pop(key, None)
        self._sleeping.discard(key)
        self._dead.discard(key)

    # ── Central Guard Verification ────────────────────────────────────

    def check_can_teleport(
        self,
        player_key: str,
        *,
        is_dead: bool = False,
        is_sleeping: bool = False,
        is_in_lava: bool = False,
        is_gliding: bool = False,
        scoreboard_tags: Iterable[str] = (),
        blocked_tags: Iterable[str] = (),
        block_in_hazard: bool = True,
        check_cooldown: bool = True,
    ) -> tuple[bool, str, dict[str, object]]:
        """Verify if `player_key` is allowed to use a teleport/home/spawn/warp command.

        Returns `(allowed, lang_key, format_kwargs)`.
        """
        key = str(player_key)

        if is_dead or self.is_dead(key):
            return False, "dead_blocked", {}

        if is_sleeping or self.is_sleeping(key):
            return False, "sleeping_blocked", {}

        combat_rem = self.get_remaining_combat(key)
        if combat_rem > 0.0:
            return (
                False,
                "combat_blocked",
                {"seconds": max(1, math.ceil(combat_rem))},
            )

        lock_reason = self.get_event_lock(key)
        if lock_reason is not None:
            return False, "event_blocked", {"reason": lock_reason}

        blocked_set = {t.strip().lower() for t in blocked_tags if t.strip()}
        for tag in scoreboard_tags:
            t_low = str(tag).strip().lower()
            if t_low in blocked_set or t_low.startswith(("event:", "arena:")):
                return False, "event_blocked", {"reason": str(tag)}

        busy = self.get_busy_event(key)
        if busy is not None:
            busy_rem, busy_reason = busy
            return (
                False,
                "event_blocked",
                {"reason": f"{busy_reason} ({max(1, math.ceil(busy_rem))}s)"},
            )

        if block_in_hazard and (is_in_lava or is_gliding):
            return False, "hazard_blocked", {}

        if check_cooldown:
            cd_rem = self.get_remaining_cooldown(key)
            if cd_rem > 0.0:
                return (
                    False,
                    "cooldown_blocked",
                    {"seconds": max(1, math.ceil(cd_rem))},
                )

        return True, "", {}
