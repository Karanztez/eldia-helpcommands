"""Command handlers for `/spawn`, `/hub`, `/setspawn`, `/sethome`, `/delhome`, `/home`, `/setwarp`, `/delwarp`, `/warp`, `/ehc`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eldia_helpcommands.commands import CommandContext, CommandSpec, HelpCommandRouter
from eldia_helpcommands.core.types import HOME_SLOTS, TeleportPoint, normalize_home_slot

if TYPE_CHECKING:
    from eldia_helpcommands.commands import CommandActor
    from eldia_helpcommands.managers import HelpCommandServices


def _check_teleport_guard(
    actor: CommandActor,
    services: HelpCommandServices,
    *,
    check_cooldown: bool = True,
) -> bool:
    """Verify the player is not in combat, dead, sleeping, or locked in an event."""
    cfg = services.config
    allowed, lang_key, fmt_kwargs = services.combat.check_can_teleport(
        actor.player_key,
        is_dead=actor.is_dead,
        is_in_lava=actor.is_in_lava,
        is_gliding=actor.is_gliding,
        scoreboard_tags=actor.scoreboard_tags,
        blocked_tags=cfg.blocked_scoreboard_tags,
        block_in_hazard=cfg.block_in_hazard,
        check_cooldown=check_cooldown,
    )
    if not allowed:
        actor.send_message(services.lang.msg(lang_key, **fmt_kwargs))
        return False
    return True


def _execute_teleport(
    actor: CommandActor,
    services: HelpCommandServices,
    point: TeleportPoint,
) -> bool:
    """Teleport `actor` to `point` via `eldia_worlds.WorldsAPI` and record cooldown."""
    target = actor.raw_player or actor

    def _do_tp() -> bool:
        ok = services.worlds.teleport_player(
            target,
            world_name=point.world_name,
            dimension=point.dimension,
            x=point.x,
            y=point.y,
            z=point.z,
            yaw=point.yaw,
            pitch=point.pitch,
        )
        if not ok and actor.raw_player is not None:
            ok = actor.teleport_to_point(point)
        return ok

    if not _do_tp():
        actor.send_message(
            services.lang.msg(
                "world_not_loaded",
                world=point.world_name,
                dimension=point.dimension,
            ),
        )
        return False

    # Re-snap 2 ticks later so cross-dimension chunk loading never drops the player into void
    raw_p = actor.raw_player
    srv = getattr(raw_p, "server", None) if raw_p is not None else None
    scheduler = getattr(srv, "scheduler", None) if srv is not None else None
    if scheduler is not None and hasattr(scheduler, "run_task"):
        try:
            pm = getattr(srv, "plugin_manager", None)
            plugin_ref = pm.get_plugin("eldia_helpcommands") if pm is not None else None
            if plugin_ref is not None:
                scheduler.run_task(
                    plugin_ref,
                    lambda: _do_tp() if getattr(raw_p, "is_valid", True) else None,
                    delay=2,
                )
        except Exception as exc:  # noqa: BLE001
            _ = exc

    services.combat.record_teleport(
        actor.player_key,
        services.config.teleport_cooldown_seconds,
    )
    return True


# ── /spawn (/hub) & /setspawn ─────────────────────────────────────────


def handle_setspawn(ctx: CommandContext) -> bool:
    """`/setspawn` (OP only) — Sets current world & coordinates as Main Server Spawn."""
    actor = ctx.actor
    services = ctx.services
    x, y, z = actor.position
    yaw, pitch = actor.rotation
    world_name = services.worlds.detect_world_name(actor.dimension_name, x, z)
    if actor.world_name and actor.world_name != actor.dimension_name:
        world_name = actor.world_name

    point = services.spawn.set_main_spawn(
        dimension=actor.dimension_name,
        world_name=world_name,
        x=x,
        y=y,
        z=z,
        yaw=yaw,
        pitch=pitch,
    )
    services.worlds.set_world_spawn(
        point.world_name,
        point.x,
        point.y,
        point.z,
        point.yaw,
        point.pitch,
        dimension=point.dimension,
    )
    actor.send_message(
        services.lang.msg(
            "spawn_set",
            world=point.world_name,
            dimension=point.dimension,
            x=round(point.x),
            y=round(point.y),
            z=round(point.z),
        ),
    )
    return True


def handle_spawn(ctx: CommandContext) -> bool:
    """`/spawn` (or `/hub`) — Teleports to Main Server Spawn (blocked during combat/events)."""
    actor = ctx.actor
    services = ctx.services
    if not _check_teleport_guard(actor, services):
        return True

    main_spawn = services.spawn.get_main_spawn()
    if main_spawn is None:
        actor.send_message(services.lang.msg("spawn_not_set"))
        return True

    if _execute_teleport(actor, services, main_spawn):
        actor.send_message(
            services.lang.msg("spawn_teleported", world=main_spawn.world_name),
        )
    return True


# ── /sethome, /delhome, /home (Slots 1, 2, 3 + GUI) ───────────────────


def _do_sethome_slot(actor: CommandActor, services: HelpCommandServices, slot_raw: str | None) -> None:
    if not _check_teleport_guard(actor, services, check_cooldown=False):
        return
    slot = normalize_home_slot(slot_raw)
    if slot is None:
        actor.send_message(services.lang.msg("home_invalid_slot"))
        return

    x, y, z = actor.position
    yaw, pitch = actor.rotation
    world_name = services.worlds.detect_world_name(actor.dimension_name, x, z)
    if actor.world_name and actor.world_name != actor.dimension_name:
        world_name = actor.world_name

    saved = services.homes.set_home(
        actor.player_key,
        slot,
        dimension=actor.dimension_name,
        world_name=world_name,
        x=x,
        y=y,
        z=z,
        yaw=yaw,
        pitch=pitch,
    )
    if saved is None:
        actor.send_message(services.lang.msg("home_invalid_slot"))
        return
    norm_slot, pt = saved
    actor.send_message(
        services.lang.msg(
            "home_set",
            slot=norm_slot,
            world=pt.world_name,
            x=round(pt.x),
            y=round(pt.y),
            z=round(pt.z),
        ),
    )


def _do_delhome_slot(actor: CommandActor, services: HelpCommandServices, slot_raw: str | None) -> None:
    slot = normalize_home_slot(slot_raw)
    if slot is None:
        actor.send_message(services.lang.msg("home_invalid_slot"))
        return
    if services.homes.delete_home(actor.player_key, slot):
        actor.send_message(services.lang.msg("home_deleted", slot=slot))
    else:
        actor.send_message(services.lang.msg("home_not_set", slot=slot))


def _do_teleport_home_slot(actor: CommandActor, services: HelpCommandServices, slot_raw: str | None) -> None:
    if not _check_teleport_guard(actor, services):
        return
    slot = normalize_home_slot(slot_raw)
    if slot is None:
        actor.send_message(services.lang.msg("home_invalid_slot"))
        return
    pt = services.homes.get_home(actor.player_key, slot)
    if pt is None:
        actor.send_message(services.lang.msg("home_not_set", slot=slot))
        return
    if _execute_teleport(actor, services, pt):
        actor.send_message(
            services.lang.msg("home_teleported", slot=slot, world=pt.world_name),
        )


def _open_or_print_home_gui(actor: CommandActor, services: HelpCommandServices) -> None:
    if not _check_teleport_guard(actor, services, check_cooldown=False):
        return
    homes = services.homes.list_homes(actor.player_key)
    target_player = actor.raw_player if actor.raw_player is not None else actor
    opened = services.ui.open_home_gui(
        target_player,
        homes,
        services.lang,
        on_teleport=lambda s: _do_teleport_home_slot(actor, services, s),
        on_set=lambda s: _do_sethome_slot(actor, services, s),
        on_delete=lambda s: _do_delhome_slot(actor, services, s),
    )
    if not opened:
        actor.send_message(services.lang.msg("home_list_header"))
        for slot in HOME_SLOTS:
            pt = homes.get(slot)
            if pt is not None:
                actor.send_message(
                    services.lang.msg(
                        "home_list_entry_set",
                        slot=slot,
                        world=pt.world_name,
                        dimension=pt.dimension,
                        x=round(pt.x),
                        y=round(pt.y),
                        z=round(pt.z),
                    ),
                )
            else:
                actor.send_message(services.lang.msg("home_list_entry_empty", slot=slot))


def handle_sethome(ctx: CommandContext) -> bool:
    """`/sethome [1|2|3]` — Saves home in slot 1, 2, or 3 (defaults to 1)."""
    slot_arg = ctx.args[0] if ctx.args else "1"
    _do_sethome_slot(ctx.actor, ctx.services, slot_arg)
    return True


def handle_delhome(ctx: CommandContext) -> bool:
    """`/delhome [1|2|3]` — Deletes home in slot 1, 2, or 3 (defaults to 1)."""
    slot_arg = ctx.args[0] if ctx.args else "1"
    _do_delhome_slot(ctx.actor, ctx.services, slot_arg)
    return True


def handle_home(ctx: CommandContext) -> bool:
    """`/home [1|2|3|gui]` — Opens 3-Home GUI or teleports directly to Home 1, 2, or 3."""
    if not ctx.args or ctx.args[0].lower() in {"gui", "menu", "list"}:
        _open_or_print_home_gui(ctx.actor, ctx.services)
        return True

    sub = ctx.args[0].lower()
    if sub in {"set", "save"} and len(ctx.args) >= 2:
        _do_sethome_slot(ctx.actor, ctx.services, ctx.args[1])
        return True
    if sub in {"del", "delete", "remove"} and len(ctx.args) >= 2:
        _do_delhome_slot(ctx.actor, ctx.services, ctx.args[1])
        return True

    _do_teleport_home_slot(ctx.actor, ctx.services, ctx.args[0])
    return True


# ── /setwarp, /delwarp, /warp (OP Only, Cross-World) ──────────────────


def handle_setwarp(ctx: CommandContext) -> bool:
    """`/setwarp <name>` (OP only) — Sets a cross-world warp point."""
    actor = ctx.actor
    services = ctx.services
    if not ctx.args:
        actor.send_message(services.lang.msg("warp_usage_set"))
        return True

    x, y, z = actor.position
    yaw, pitch = actor.rotation
    world_name = services.worlds.detect_world_name(actor.dimension_name, x, z)
    if actor.world_name and actor.world_name != actor.dimension_name:
        world_name = actor.world_name

    saved = services.warps.set_warp(
        ctx.args[0],
        dimension=actor.dimension_name,
        world_name=world_name,
        x=x,
        y=y,
        z=z,
        yaw=yaw,
        pitch=pitch,
    )
    if saved is None:
        actor.send_message(services.lang.msg("warp_invalid_name"))
        return True

    norm_name, pt = saved
    actor.send_message(
        services.lang.msg(
            "warp_set",
            name=norm_name,
            world=pt.world_name,
            dimension=pt.dimension,
            x=round(pt.x),
            y=round(pt.y),
            z=round(pt.z),
        ),
    )
    return True


def handle_delwarp(ctx: CommandContext) -> bool:
    """`/delwarp <name>` (OP only) — Deletes a warp point."""
    actor = ctx.actor
    services = ctx.services
    if not ctx.args:
        actor.send_message(services.lang.msg("warp_usage_del"))
        return True

    name = ctx.args[0]
    if services.warps.delete_warp(name):
        actor.send_message(services.lang.msg("warp_deleted", name=name.lower()))
    else:
        actor.send_message(services.lang.msg("warp_not_found", name=name))
    return True


def _do_teleport_warp(actor: CommandActor, services: HelpCommandServices, name: str) -> None:
    if not _check_teleport_guard(actor, services):
        return
    pt = services.warps.get_warp(name)
    if pt is None:
        actor.send_message(services.lang.msg("warp_not_found", name=name))
        return
    if _execute_teleport(actor, services, pt):
        actor.send_message(
            services.lang.msg("warp_teleported", name=name.lower(), world=pt.world_name),
        )


def handle_warp(ctx: CommandContext) -> bool:
    """`/warp [name]` (OP only) — Teleports across worlds to `<name>` or opens Warp GUI."""
    actor = ctx.actor
    services = ctx.services

    if not ctx.args or ctx.args[0].lower() in {"gui", "list"}:
        if not _check_teleport_guard(actor, services, check_cooldown=False):
            return True
        warps = services.warps.list_warps()
        if not warps:
            actor.send_message(services.lang.msg("warp_empty"))
            return True
        target_player = actor.raw_player if actor.raw_player is not None else actor
        opened = services.ui.open_warp_gui(
            target_player,
            warps,
            services.lang,
            on_teleport=lambda wname: _do_teleport_warp(actor, services, wname),
        )
        if not opened:
            actor.send_message(services.lang.msg("warp_list_header", count=len(warps)))
            for name, pt in warps.items():
                actor.send_message(
                    services.lang.msg(
                        "warp_list_entry",
                        name=name,
                        world=pt.world_name,
                        dimension=pt.dimension,
                        x=round(pt.x),
                        y=round(pt.y),
                        z=round(pt.z),
                    ),
                )
        return True

    _do_teleport_warp(actor, services, ctx.args[0])
    return True


# ── /helpcommands (/ehc) Admin Management ─────────────────────────────


def handle_ehc_admin(ctx: CommandContext) -> bool:
    """`/ehc [reload|lang|eventlock|status]` (OP only)."""
    actor = ctx.actor
    services = ctx.services
    sub = ctx.args[0].lower() if ctx.args else "status"

    if sub == "reload":
        cfg = services.reload_config()
        actor.send_message(services.lang.msg("config_reloaded", lang=cfg.language))
        return True

    if sub == "lang":
        if len(ctx.args) < 2 or not services.lang.set_language(ctx.args[1]):
            actor.send_message(services.lang.msg("lang_invalid"))
            return True
        services.config_manager.save_language(services.lang.language)
        actor.send_message(services.lang.msg("lang_changed", lang=services.lang.language))
        return True

    if sub == "eventlock" and len(ctx.args) >= 3:
        target_key = ctx.args[1]
        mode = ctx.args[2].lower()
        reason = " ".join(ctx.args[3:]) if len(ctx.args) > 3 else "Active Event"
        if mode in {"on", "true", "1", "lock"}:
            services.combat.set_event_lock(target_key, reason=reason)
            actor.send_message(
                services.lang.msg("eventlock_set", player=target_key, state="ON", reason=reason),
            )
        else:
            services.combat.clear_event_lock(target_key)
            actor.send_message(
                services.lang.msg("eventlock_set", player=target_key, state="OFF", reason="-"),
            )
        return True

    spawn_pt = services.spawn.get_main_spawn()
    spawn_desc = f"{spawn_pt.world_name}({int(spawn_pt.x)},{int(spawn_pt.y)},{int(spawn_pt.z)})" if spawn_pt else "None"
    actor.send_message(
        services.lang.msg(
            "status_info",
            lang=services.lang.language,
            combat_sec=services.config.combat_tag_seconds,
            warps=len(services.warps.list_warps()),
            spawn=spawn_desc,
        ),
    )
    return True


def register_all_commands(router: HelpCommandRouter) -> None:
    """Register all plugin commands on `router`."""
    router.register(
        CommandSpec(
            name="spawn",
            aliases=("hub",),
            description="Teleport to the main server spawn",
            usage="/spawn",
            handler=handle_spawn,
            permission="eldia_helpcommands.command.spawn",
            op_only=False,
        ),
    )
    router.register(
        CommandSpec(
            name="setspawn",
            description="Set the main server spawn in the current world (OP only)",
            usage="/setspawn",
            handler=handle_setspawn,
            permission="eldia_helpcommands.command.setspawn",
            op_only=True,
        ),
    )
    router.register(
        CommandSpec(
            name="sethome",
            description="Save your home location in slot 1, 2, or 3",
            usage="/sethome [1|2|3]",
            handler=handle_sethome,
            permission="eldia_helpcommands.command.home",
            op_only=False,
        ),
    )
    router.register(
        CommandSpec(
            name="delhome",
            description="Delete your saved home in slot 1, 2, or 3",
            usage="/delhome [1|2|3]",
            handler=handle_delhome,
            permission="eldia_helpcommands.command.home",
            op_only=False,
        ),
    )
    router.register(
        CommandSpec(
            name="home",
            aliases=("homes",),
            description="Teleport to Home 1, 2, or 3 or open the 3-Home GUI",
            usage="/home [1|2|3|gui]",
            handler=handle_home,
            permission="eldia_helpcommands.command.home",
            op_only=False,
        ),
    )
    router.register(
        CommandSpec(
            name="setwarp",
            description="Create a cross-world warp point at your location (OP only)",
            usage="/setwarp <name>",
            handler=handle_setwarp,
            permission="eldia_helpcommands.command.setwarp",
            op_only=True,
        ),
    )
    router.register(
        CommandSpec(
            name="delwarp",
            description="Delete a warp point (OP only)",
            usage="/delwarp <name>",
            handler=handle_delwarp,
            permission="eldia_helpcommands.command.setwarp",
            op_only=True,
        ),
    )
    router.register(
        CommandSpec(
            name="warp",
            aliases=("warps",),
            description="Teleport to a cross-world warp point (OP only; non-OP use /home)",
            usage="/warp [name]",
            handler=handle_warp,
            permission="eldia_helpcommands.command.warp",
            op_only=True,
        ),
    )
    router.register(
        CommandSpec(
            name="helpcommands",
            aliases=("ehc", "hc"),
            description="Eldia HelpCommands configuration and event lock controls (OP only)",
            usage="/ehc [reload|lang|eventlock|status]",
            handler=handle_ehc_admin,
            permission="eldia_helpcommands.command.admin",
            op_only=True,
        ),
    )
