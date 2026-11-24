"""Endstone Plugin class for Eldia HelpCommands (`eldia-helpcommands`).

IMPORTANT: Do NOT add `from __future__ import annotations` to this module!
Endstone's `@event_handler` inspects parameter type annotations at runtime via
`issubclass(param.annotation, Event)`, which requires real `Event` classes.
"""

import math
import time
from pathlib import Path
from typing import Any, ClassVar

from endstone import Player
from endstone.command import Command, CommandSender
from endstone.event import (
    ActorDamageEvent,
    ActorKnockbackEvent,
    BlockBreakEvent,
    EventPriority,
    PlayerBedEnterEvent,
    PlayerBedLeaveEvent,
    PlayerDeathEvent,
    PlayerInteractActorEvent,
    PlayerInteractEvent,
    PlayerQuitEvent,
    PlayerRespawnEvent,
    event_handler,
)
from endstone.plugin import Plugin

from eldia_helpcommands.commands import HelpCommandRouter
from eldia_helpcommands.core.types import TeleportPoint, is_bed_block
from eldia_helpcommands.managers import HelpCommandServices


def _player_key(player: Any) -> str:
    """Return a consistent unique string key for a player (UUID or lowercase name)."""
    uid = getattr(player, "unique_id", None)
    if uid is not None:
        return str(uid)
    return str(getattr(player, "name", "unknown")).lower()


def _is_player_instance(actor: Any) -> bool:
    if actor is None:
        return False
    if isinstance(actor, Player):
        return True
    return hasattr(actor, "unique_id") and hasattr(actor, "send_form") and hasattr(actor, "is_op")


class _EndstonePlayerActor:
    """Adapts an Endstone `Player` to the `CommandActor` protocol."""

    def __init__(self, player: Player, services: HelpCommandServices) -> None:
        self._player = player
        self._services = services

    @property
    def raw_player(self) -> Player:
        return self._player

    @property
    def player_key(self) -> str:
        return _player_key(self._player)

    @property
    def name(self) -> str:
        return str(getattr(self._player, "name", "Player"))

    @property
    def is_op(self) -> bool:
        return bool(getattr(self._player, "is_op", False))

    @property
    def dimension_name(self) -> str:
        dim = getattr(self._player, "dimension", None)
        if dim is not None and getattr(dim, "name", ""):
            return str(dim.name)
        loc = getattr(self._player, "location", None)
        loc_dim = getattr(loc, "dimension", None)
        if loc_dim is not None and getattr(loc_dim, "name", ""):
            return str(loc_dim.name)
        return "Overworld"

    @property
    def world_name(self) -> str:
        x, _, z = self.position
        return self._services.worlds.detect_world_name(self.dimension_name, x, z)

    @property
    def position(self) -> tuple[float, float, float]:
        loc = getattr(self._player, "location", None)
        if loc is None:
            return (0.0, 64.0, 0.0)
        return (
            float(getattr(loc, "x", 0.0)),
            float(getattr(loc, "y", 64.0)),
            float(getattr(loc, "z", 0.0)),
        )

    @property
    def rotation(self) -> tuple[float, float]:
        loc = getattr(self._player, "location", None)
        if loc is None:
            return (0.0, 0.0)
        return (
            float(getattr(loc, "yaw", 0.0)),
            float(getattr(loc, "pitch", 0.0)),
        )

    @property
    def is_dead(self) -> bool:
        return bool(getattr(self._player, "is_dead", False))

    @property
    def is_in_lava(self) -> bool:
        return bool(getattr(self._player, "is_in_lava", False))

    @property
    def is_gliding(self) -> bool:
        return bool(getattr(self._player, "is_gliding", False))

    @property
    def scoreboard_tags(self) -> tuple[str, ...]:
        tags = getattr(self._player, "scoreboard_tags", None)
        if not tags:
            return ()
        return tuple(str(t) for t in tags)

    def send_message(self, message: str) -> None:
        self._player.send_message(message)

    def teleport_to_point(self, point: TeleportPoint) -> bool:
        return self._services.worlds.teleport_player(
            self._player,
            world_name=point.world_name,
            dimension=point.dimension,
            x=point.x,
            y=point.y,
            z=point.z,
            yaw=point.yaw,
            pitch=point.pitch,
        )


class HelpCommandsPlugin(Plugin):
    """Endstone plugin entry point for `eldia-helpcommands`."""

    api_version = "0.10"
    name = "eldia_helpcommands"
    version = "0.1.2"
    description = "Essential spawn, 3-slot Home GUI, cross-world OP Warp, and Combat Guard for Endstone"
    authors: ClassVar[list[str]] = ["Eldia"]
    soft_depend: ClassVar[list[str]] = ["eldia_worlds"]

    commands: ClassVar[dict[str, dict[str, Any]]] = {
        "spawn": {
            "description": "Teleport to the main server spawn (/spawn or /hub)",
            "usages": ["/spawn"],
            "aliases": ["hub"],
            "permissions": ["eldia_helpcommands.command.spawn"],
        },
        "setspawn": {
            "description": "Set the main server spawn in the current world (OP only)",
            "usages": ["/setspawn"],
            "permissions": ["eldia_helpcommands.command.setspawn"],
        },
        "sethome": {
            "description": "Save your home in slot 1, 2, or 3",
            "usages": ["/sethome", "/sethome <args: message>"],
            "permissions": ["eldia_helpcommands.command.home"],
        },
        "delhome": {
            "description": "Delete your saved home in slot 1, 2, or 3",
            "usages": ["/delhome", "/delhome <args: message>"],
            "permissions": ["eldia_helpcommands.command.home"],
        },
        "home": {
            "description": "Teleport to Home 1, 2, or 3 or open the 3-Home GUI",
            "usages": ["/home", "/home <args: message>"],
            "aliases": ["homes"],
            "permissions": ["eldia_helpcommands.command.home"],
        },
        "setwarp": {
            "description": "Create a cross-world warp point (OP only)",
            "usages": ["/setwarp", "/setwarp <args: message>"],
            "permissions": ["eldia_helpcommands.command.setwarp"],
        },
        "delwarp": {
            "description": "Delete a cross-world warp point (OP only)",
            "usages": ["/delwarp", "/delwarp <args: message>"],
            "permissions": ["eldia_helpcommands.command.setwarp"],
        },
        "warp": {
            "description": "Teleport to a warp point (OP only; non-OP players use /home)",
            "usages": ["/warp", "/warp <args: message>"],
            "aliases": ["warps"],
            "permissions": ["eldia_helpcommands.command.warp"],
        },
        "helpcommands": {
            "description": "Eldia HelpCommands configuration and event lock management (OP only)",
            "usages": ["/helpcommands", "/helpcommands <args: message>"],
            "aliases": ["ehc", "hc"],
            "permissions": ["eldia_helpcommands.command.admin"],
        },
    }

    permissions: ClassVar[dict[str, dict[str, Any]]] = {
        "eldia_helpcommands.command.spawn": {
            "description": "Allow players to teleport to main spawn via /spawn and /hub",
            "default": True,
        },
        "eldia_helpcommands.command.home": {
            "description": "Allow players to use /home, /sethome, and /delhome (slots 1-3 + GUI)",
            "default": True,
        },
        "eldia_helpcommands.command.setspawn": {
            "description": "Allow OP to set the main server spawn via /setspawn",
            "default": "op",
        },
        "eldia_helpcommands.command.setwarp": {
            "description": "Allow OP to create and delete warps via /setwarp and /delwarp",
            "default": "op",
        },
        "eldia_helpcommands.command.warp": {
            "description": "Allow OP to use /warp (regular players use /home)",
            "default": "op",
        },
        "eldia_helpcommands.command.admin": {
            "description": "Allow OP to manage Eldia HelpCommands via /ehc",
            "default": "op",
        },
    }

    def __init__(self) -> None:
        super().__init__()
        self._services: HelpCommandServices | None = None
        self._router: HelpCommandRouter | None = None
        self._bed_save_debounce: dict[str, float] = {}

    @property
    def services(self) -> HelpCommandServices:
        if self._services is None:
            folder = Path(str(self.data_folder)) if getattr(self, "data_folder", None) else Path("plugins/eldia_helpcommands")
            self._services = HelpCommandServices(
                data_folder=folder,
                create_files=True,
                server_getter=lambda: getattr(self, "server", None),
            )
        return self._services

    @property
    def router(self) -> HelpCommandRouter:
        if self._router is None:
            self._router = HelpCommandRouter(self.services)
        return self._router

    def on_enable(self) -> None:
        _ = self.router
        self.register_events(self)
        self.logger.info(
            f"Eldia HelpCommands enabled (lang={self.services.lang.language}, "
            f"combat_tag={self.services.config.combat_tag_seconds}s)",
        )

    def on_disable(self) -> None:
        self._bed_save_debounce.clear()

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not _is_player_instance(sender):
            sender.send_message("This command can only be executed by an in-game player.")
            return True
        actor = _EndstonePlayerActor(sender, self.services)  # type: ignore[arg-type]
        return self.router.dispatch(actor, command.name, args)

    # ── Combat & Event Guard Listeners ────────────────────────────────

    @event_handler(priority=EventPriority.MONITOR, ignore_cancelled=True)
    def on_actor_damage(self, event: ActorDamageEvent) -> None:
        """Tag victim and attacker players in combat when damage occurs."""
        victim = getattr(event, "actor", None)
        damage = float(getattr(event, "damage", 0.0))
        if damage <= 0.0:
            return

        dmg_source = getattr(event, "damage_source", None)
        attacker = getattr(dmg_source, "actor", None) if dmg_source is not None else None
        if attacker is None and dmg_source is not None:
            attacker = getattr(dmg_source, "damaging_actor", None)

        victim_is_player = _is_player_instance(victim)
        attacker_is_player = _is_player_instance(attacker)
        victim_key = _player_key(victim) if victim is not None else None
        attacker_key = _player_key(attacker) if attacker is not None else None

        cfg = self.services.config
        newly_tagged = self.services.combat.handle_damage_event(
            victim_key=victim_key,
            victim_is_player=victim_is_player,
            attacker_key=attacker_key,
            attacker_is_player=attacker_is_player,
            damage=damage,
            duration_sec=cfg.combat_tag_seconds,
            tag_all_damage=cfg.tag_all_damage,
            pvp_only=cfg.pvp_only,
        )

        sec_int = max(1, math.ceil(cfg.combat_tag_seconds))
        if victim_is_player and victim_key in newly_tagged:
            victim.send_message(self.services.lang.msg("combat_tagged", seconds=sec_int))
        if attacker_is_player and attacker_key in newly_tagged:
            attacker.send_message(self.services.lang.msg("combat_tagged", seconds=sec_int))

    @event_handler(priority=EventPriority.MONITOR, ignore_cancelled=True)
    def on_actor_knockback(self, event: ActorKnockbackEvent) -> None:
        """Tag both players when knockback occurs between actors in combat."""
        victim = getattr(event, "actor", None)
        source = getattr(event, "source", None)
        if source is None:
            return
        victim_is_player = _is_player_instance(victim)
        source_is_player = _is_player_instance(source)
        if not (victim_is_player or source_is_player):
            return
        cfg = self.services.config
        self.services.combat.handle_damage_event(
            victim_key=_player_key(victim) if victim is not None else None,
            victim_is_player=victim_is_player,
            attacker_key=_player_key(source),
            attacker_is_player=source_is_player,
            damage=1.0,
            duration_sec=cfg.combat_tag_seconds,
            tag_all_damage=cfg.tag_all_damage,
            pvp_only=cfg.pvp_only,
        )

    @event_handler(priority=EventPriority.MONITOR, ignore_cancelled=True)
    def on_player_interact_actor(self, event: PlayerInteractActorEvent) -> None:
        """If a player interacts with another player while PvP/event is active, refresh busy guard."""
        player = getattr(event, "player", None)
        target = getattr(event, "actor", None)
        if player is None or target is None:
            return
        pkey = _player_key(player)
        if self.services.combat.is_in_combat(pkey):
            self.services.combat.tag_combat(
                pkey,
                self.services.config.combat_tag_seconds,
                reason="combat_interact",
            )

    # ── Bed Saving & Sleeping State Listeners ─────────────────────────

    def _save_player_bed(self, player: Player, bed_block: Any) -> None:
        pkey = _player_key(player)
        now = time.monotonic()
        last = self._bed_save_debounce.get(pkey, 0.0)
        if now - last < 0.75:
            return
        self._bed_save_debounce[pkey] = now

        dim = getattr(bed_block, "dimension", None) or getattr(player, "dimension", None)
        dim_name = str(getattr(dim, "name", "Overworld")) if dim is not None else "Overworld"
        bx = float(getattr(bed_block, "x", 0)) + 0.5
        by = float(getattr(bed_block, "y", 64)) + 0.6
        bz = float(getattr(bed_block, "z", 0)) + 0.5
        loc = getattr(player, "location", None)
        yaw = float(getattr(loc, "yaw", 0.0)) if loc is not None else 0.0
        pitch = float(getattr(loc, "pitch", 0.0)) if loc is not None else 0.0

        world_name = self.services.worlds.detect_world_name(dim_name, bx, bz)
        pt = self.services.spawn.set_bed_spawn(
            pkey,
            dimension=dim_name,
            world_name=world_name,
            x=bx,
            y=by,
            z=bz,
            yaw=yaw,
            pitch=pitch,
        )
        player.send_message(
            self.services.lang.msg(
                "bed_saved",
                world=pt.world_name,
                x=round(pt.x),
                y=round(pt.y),
                z=round(pt.z),
            ),
        )

    @event_handler(priority=EventPriority.MONITOR, ignore_cancelled=True)
    def on_player_bed_enter(self, event: PlayerBedEnterEvent) -> None:
        """Mark player as sleeping (blocks teleport) and save their bed respawn point."""
        player = getattr(event, "player", None)
        bed = getattr(event, "bed", None)
        if player is None:
            return
        self.services.combat.set_sleeping(_player_key(player), True)
        if bed is not None:
            self._save_player_bed(player, bed)

    @event_handler(priority=EventPriority.MONITOR)
    def on_player_bed_leave(self, event: PlayerBedLeaveEvent) -> None:
        """Clear sleeping state when player leaves bed."""
        player = getattr(event, "player", None)
        if player is not None:
            self.services.combat.set_sleeping(_player_key(player), False)

    @event_handler(priority=EventPriority.MONITOR, ignore_cancelled=True)
    def on_player_interact(self, event: PlayerInteractEvent) -> None:
        """Save bed respawn point when right-clicking a bed block (even during daytime)."""
        if getattr(event, "action", None) != PlayerInteractEvent.Action.RIGHT_CLICK_BLOCK:
            return
        block = getattr(event, "block", None)
        player = getattr(event, "player", None)
        if block is None or player is None:
            return
        block_type = str(getattr(block, "type", ""))
        if is_bed_block(block_type):
            self._save_player_bed(player, block)

    @event_handler(priority=EventPriority.MONITOR, ignore_cancelled=True)
    def on_block_break(self, event: BlockBreakEvent) -> None:
        """If a bed block is broken, clear any saved bed spawns at that bed."""
        block = getattr(event, "block", None)
        if block is None:
            return
        block_type = str(getattr(block, "type", ""))
        if not is_bed_block(block_type):
            return
        dim = getattr(block, "dimension", None)
        dim_name = str(getattr(dim, "name", "Overworld")) if dim is not None else "Overworld"
        bx = float(getattr(block, "x", 0)) + 0.5
        by = float(getattr(block, "y", 64))
        bz = float(getattr(block, "z", 0)) + 0.5
        self.services.spawn.clear_beds_near(dim_name, bx, by, bz)

    # ── Death & Respawn Listeners (Bed vs Main Server Spawn) ──────────

    @event_handler(priority=EventPriority.MONITOR)
    def on_player_death(self, event: PlayerDeathEvent) -> None:
        """Clear combat tag on death and mark dead until respawn."""
        player = getattr(event, "player", None)
        if player is None:
            return
        pkey = _player_key(player)
        self.services.combat.clear_combat(pkey)
        self.services.combat.set_sleeping(pkey, False)
        self.services.combat.set_dead(pkey, True)

    @event_handler(priority=EventPriority.HIGHEST)
    def on_player_respawn(self, event: PlayerRespawnEvent) -> None:
        """Teleport respawning player to their saved bed (if intact) or Main Server Spawn."""
        player = getattr(event, "player", None)
        if player is None:
            return
        pkey = _player_key(player)
        self.services.combat.set_dead(pkey, False)
        self.services.combat.set_sleeping(pkey, False)
        self.services.combat.clear_combat(pkey)

        target_point, reason = self.services.spawn.resolve_respawn_point(
            pkey,
            bed_verifier=lambda pt: self.services.worlds.is_block_matching_near(
                pt.dimension,
                pt.world_name,
                pt.x,
                pt.y,
                pt.z,
                is_bed_block,
            ),
        )
        if target_point is None:
            return

        def _tp_to_target() -> None:
            self.services.worlds.teleport_player(
                player,
                world_name=target_point.world_name,
                dimension=target_point.dimension,
                x=target_point.x,
                y=target_point.y,
                z=target_point.z,
                yaw=target_point.yaw,
                pitch=target_point.pitch,
            )

        def _apply_respawn_tp() -> None:
            if not getattr(player, "is_valid", True):
                return
            _tp_to_target()
            if reason == "bed":
                player.send_message(
                    self.services.lang.msg("respawn_at_bed", world=target_point.world_name),
                )
            elif reason == "bed_missing":
                player.send_message(
                    self.services.lang.msg("respawn_bed_missing", world=target_point.world_name),
                )
            elif reason == "spawn":
                player.send_message(
                    self.services.lang.msg("respawn_at_spawn", world=target_point.world_name),
                )

        # Teleport immediately and schedule a 2-tick follow-up for cross-dimension respawns
        _tp_to_target()
        srv = getattr(self, "server", None)
        scheduler = getattr(srv, "scheduler", None) if srv is not None else None
        if scheduler is not None and hasattr(scheduler, "run_task"):
            try:
                scheduler.run_task(self, _apply_respawn_tp, delay=2)
                return
            except Exception as exc:  # noqa: BLE001
                _ = exc
        _apply_respawn_tp()

    @event_handler(priority=EventPriority.MONITOR)
    def on_player_quit(self, event: PlayerQuitEvent) -> None:
        """Clean up transient state when a player leaves the server."""
        player = getattr(event, "player", None)
        if player is not None:
            pkey = _player_key(player)
            self.services.cleanup_player(pkey)
            self._bed_save_debounce.pop(pkey, None)
