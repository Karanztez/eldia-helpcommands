"""Comprehensive test suite for `eldia-helpcommands`."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from eldia_worlds import WorldRegistry, WorldsAPI
from endstone.event import Event

from eldia_helpcommands import HelpCommandsPlugin
from eldia_helpcommands.commands import HelpCommandRouter, MockCommandActor
from eldia_helpcommands.core.types import normalize_home_slot, normalize_warp_name
from eldia_helpcommands.managers import HelpCommandServices

if TYPE_CHECKING:
    from pathlib import Path


class _FakeClock:
    def __init__(self, initial: float = 1000.0) -> None:
        self.current = initial

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def _make_services(tmp_path: Path, clock: _FakeClock | None = None) -> tuple[HelpCommandServices, _FakeClock]:
    clk = clock or _FakeClock()
    services = HelpCommandServices(
        data_folder=tmp_path,
        create_files=True,
        clock=clk,
    )
    return services, clk


# ── 1. Spawn & Bed Respawn Tests ──────────────────────────────────────


def test_setspawn_and_spawn_across_worlds(tmp_path: Path) -> None:
    services, clk = _make_services(tmp_path)
    router = HelpCommandRouter(services)

    op_actor = MockCommandActor(
        name="Admin",
        player_key="admin-1",
        is_op=True,
        dimension_name="CustomDim",
        world_name="lobby_world",
        position=(120.0, 80.0, -45.0),
        rotation=(90.0, 0.0),
    )
    non_op = MockCommandActor(
        name="Player1",
        player_key="player-1",
        is_op=False,
        dimension_name="Overworld",
        world_name="survival",
        position=(10.0, 64.0, 10.0),
    )

    # Non-OP cannot /setspawn
    router.dispatch(non_op, "setspawn")
    assert services.spawn.get_main_spawn() is None
    assert any("เฉพาะ OP" in m for m in non_op.messages)

    # OP sets main spawn in lobby_world
    router.dispatch(op_actor, "setspawn")
    main_spawn = services.spawn.get_main_spawn()
    assert main_spawn is not None
    assert main_spawn.world_name == "lobby_world"
    assert main_spawn.dimension == "CustomDim"
    assert main_spawn.x == 120.0

    # Player uses /spawn (or /hub) from survival world -> teleports to lobby_world
    router.dispatch(non_op, "spawn")
    assert non_op.world_name == "lobby_world"
    assert non_op.dimension_name == "CustomDim"
    assert non_op.position == (120.0, 80.0, -45.0)

    # Advance past teleport cooldown and test /hub alias
    clk.advance(5.0)
    non_op.world_name = "nether_world"
    non_op.position = (0.0, 50.0, 0.0)
    router.dispatch(non_op, "hub")
    assert non_op.world_name == "lobby_world"
    assert non_op.position == (120.0, 80.0, -45.0)


def test_death_respawn_priority_bed_vs_main_spawn(tmp_path: Path) -> None:
    services, _ = _make_services(tmp_path)
    services.spawn.set_main_spawn(
        dimension="Overworld",
        world_name="hub_world",
        x=0.0,
        y=100.0,
        z=0.0,
    )

    # Case 1: Player has NO bed saved -> death respawns at Main Server Spawn
    pt, reason = services.spawn.resolve_respawn_point("player-1")
    assert pt is not None
    assert reason == "spawn"
    assert pt.world_name == "hub_world"

    # Case 2: Player saves a bed in survival_world -> death respawns at their bed
    services.spawn.set_bed_spawn(
        "player-1",
        dimension="Overworld",
        world_name="survival_world",
        x=250.5,
        y=65.6,
        z=-120.5,
    )
    pt_bed, reason_bed = services.spawn.resolve_respawn_point(
        "player-1",
        bed_verifier=lambda _p: True,
    )
    assert pt_bed is not None
    assert reason_bed == "bed"
    assert pt_bed.world_name == "survival_world"
    assert pt_bed.x == 250.5

    # /spawn command ALWAYS teleports to Main Server Spawn even when bed is saved
    router = HelpCommandRouter(services)
    actor = MockCommandActor(
        name="Player1",
        player_key="player-1",
        world_name="survival_world",
        position=(250.5, 65.6, -120.5),
    )
    router.dispatch(actor, "spawn")
    assert actor.world_name == "hub_world"
    assert actor.position == (0.0, 100.0, 0.0)

    # Case 3: Bed is broken (bed_verifier returns False) -> clears bed and falls back to Main Server Spawn
    pt_fallback, reason_fallback = services.spawn.resolve_respawn_point(
        "player-1",
        bed_verifier=lambda _p: False,
    )
    assert pt_fallback is not None
    assert reason_fallback == "bed_missing"
    assert pt_fallback.world_name == "hub_world"
    assert services.spawn.get_bed_spawn("player-1") is None


# ── 2. Homes (1, 2, 3 + GUI) Tests ───────────────────────────────────


def test_three_homes_set_teleport_gui_and_delete(tmp_path: Path) -> None:
    services, clk = _make_services(tmp_path)
    router = HelpCommandRouter(services)
    actor = MockCommandActor(
        name="Builder",
        player_key="builder-uuid",
        dimension_name="Overworld",
        world_name="world_a",
        position=(10.0, 64.0, 20.0),
    )

    # Save Home 1, 2, 3 across different worlds
    router.dispatch(actor, "sethome", ["1"])
    actor.world_name = "world_b"
    actor.dimension_name = "Nether"
    actor.position = (50.0, 70.0, 50.0)
    router.dispatch(actor, "sethome", ["2"])

    actor.world_name = "world_c"
    actor.dimension_name = "TheEnd"
    actor.position = (300.0, 90.0, -100.0)
    router.dispatch(actor, "sethome", ["3"])

    # Invalid slot 4 is rejected
    actor.messages.clear()
    router.dispatch(actor, "sethome", ["4"])
    assert any("1, 2 หรือ 3" in m for m in actor.messages)

    # Teleport to Home 1, 2, 3
    router.dispatch(actor, "home", ["1"])
    assert actor.world_name == "world_a"
    assert actor.position == (10.0, 64.0, 20.0)

    clk.advance(5.0)
    router.dispatch(actor, "home", ["2"])
    assert actor.world_name == "world_b"
    assert actor.dimension_name == "Nether"
    assert actor.position == (50.0, 70.0, 50.0)

    clk.advance(5.0)
    router.dispatch(actor, "home", ["3"])
    assert actor.world_name == "world_c"
    assert actor.dimension_name == "TheEnd"
    assert actor.position == (300.0, 90.0, -100.0)

    # /home or /home gui lists all 3 homes when headless
    actor.messages.clear()
    router.dispatch(actor, "home", ["gui"])
    joined = "\n".join(actor.messages)
    assert "world_a" in joined
    assert "world_b" in joined
    assert "world_c" in joined

    # Delete Home 2
    router.dispatch(actor, "delhome", ["2"])
    assert services.homes.get_home("builder-uuid", "2") is None


# ── 3. Cross-World Warps (OP Only) Tests ──────────────────────────────


def test_warps_op_only_and_cross_world(tmp_path: Path) -> None:
    services, _ = _make_services(tmp_path)
    router = HelpCommandRouter(services)

    op_actor = MockCommandActor(
        name="Admin",
        player_key="admin-uuid",
        is_op=True,
        dimension_name="Nether",
        world_name="boss_dungeon",
        position=(500.0, 45.0, -250.0),
    )
    normal_actor = MockCommandActor(
        name="Member",
        player_key="member-uuid",
        is_op=False,
        dimension_name="Overworld",
        world_name="main_world",
        position=(0.0, 64.0, 0.0),
    )

    # OP creates warp "dungeon"
    router.dispatch(op_actor, "setwarp", ["dungeon"])
    warp_pt = services.warps.get_warp("dungeon")
    assert warp_pt is not None
    assert warp_pt.world_name == "boss_dungeon"
    assert warp_pt.dimension == "Nether"

    # Non-OP tries /warp dungeon -> blocked and told to use /home
    router.dispatch(normal_actor, "warp", ["dungeon"])
    assert normal_actor.world_name == "main_world"
    assert normal_actor.position == (0.0, 64.0, 0.0)
    assert any("/home" in m for m in normal_actor.messages)

    # Non-OP tries /setwarp -> blocked
    normal_actor.messages.clear()
    router.dispatch(normal_actor, "setwarp", ["hack"])
    assert services.warps.get_warp("hack") is None

    # OP warps from Overworld to boss_dungeon
    op_actor.dimension_name = "Overworld"
    op_actor.world_name = "main_world"
    op_actor.position = (1.0, 65.0, 1.0)
    router.dispatch(op_actor, "warp", ["dungeon"])
    assert op_actor.world_name == "boss_dungeon"
    assert op_actor.dimension_name == "Nether"
    assert op_actor.position == (500.0, 45.0, -250.0)


# ── 4. Combat & Active Event Guard Tests ──────────────────────────────


def test_combat_guard_blocks_all_movement_commands(tmp_path: Path) -> None:
    services, clk = _make_services(tmp_path)
    router = HelpCommandRouter(services)

    services.spawn.set_main_spawn(
        dimension="Overworld",
        world_name="spawn_world",
        x=0.0,
        y=64.0,
        z=0.0,
    )
    services.warps.set_warp(
        "arena",
        dimension="Overworld",
        world_name="arena_world",
        x=100.0,
        y=64.0,
        z=100.0,
    )

    fighter = MockCommandActor(
        name="Fighter",
        player_key="fighter-1",
        is_op=True,
        dimension_name="Overworld",
        world_name="pvp_zone",
        position=(50.0, 64.0, 50.0),
    )
    router.dispatch(fighter, "sethome", ["1"])
    fighter.position = (75.0, 64.0, 75.0)

    # Simulate PvP damage tagging both victim (fighter-1) and attacker (enemy-2)
    tagged = services.combat.handle_damage_event(
        victim_key="fighter-1",
        victim_is_player=True,
        attacker_key="enemy-2",
        attacker_is_player=True,
        damage=6.0,
        duration_sec=15.0,
    )
    assert "fighter-1" in tagged
    assert "enemy-2" in tagged
    assert services.combat.is_in_combat("fighter-1")
    assert services.combat.is_in_combat("enemy-2")

    # While in combat: /spawn, /hub, /home, /sethome, /warp MUST all be blocked
    for cmd, args in (
        ("spawn", []),
        ("hub", []),
        ("home", ["1"]),
        ("home", ["gui"]),
        ("sethome", ["2"]),
        ("warp", ["arena"]),
    ):
        fighter.messages.clear()
        router.dispatch(fighter, cmd, args)
        assert fighter.position == (75.0, 64.0, 75.0), f"Command /{cmd} should be blocked in combat"
        assert any("ต่อสู้" in m for m in fighter.messages)

    # Advance 10s -> still 5s left in combat
    clk.advance(10.0)
    fighter.messages.clear()
    router.dispatch(fighter, "spawn")
    assert fighter.position == (75.0, 64.0, 75.0)
    assert any("5" in m for m in fighter.messages)

    # Advance another 6s -> combat expires -> /spawn succeeds
    clk.advance(6.0)
    assert not services.combat.is_in_combat("fighter-1")
    router.dispatch(fighter, "spawn")
    assert fighter.world_name == "spawn_world"
    assert fighter.position == (0.0, 64.0, 0.0)


def test_event_locks_scoreboard_tags_and_hazards_block_teleport(tmp_path: Path) -> None:
    services, clk = _make_services(tmp_path)
    router = HelpCommandRouter(services)
    services.spawn.set_main_spawn(
        dimension="Overworld",
        world_name="spawn_world",
        x=0.0,
        y=64.0,
        z=0.0,
    )

    player = MockCommandActor(
        name="Participant",
        player_key="part-1",
        world_name="event_world",
        position=(20.0, 64.0, 20.0),
    )

    # 1. Scoreboard tag "in_event" blocks teleport
    player.scoreboard_tags = ("in_event",)
    router.dispatch(player, "spawn")
    assert player.position == (20.0, 64.0, 20.0)
    assert any("in_event" in m for m in player.messages)
    player.scoreboard_tags = ()

    # 2. Explicit eventlock via /ehc eventlock blocks teleport
    admin = MockCommandActor(name="Admin", player_key="admin", is_op=True)
    router.dispatch(admin, "ehc", ["eventlock", "part-1", "on", "BossFight"])
    player.messages.clear()
    router.dispatch(player, "spawn")
    assert player.position == (20.0, 64.0, 20.0)
    assert any("BossFight" in m for m in player.messages)

    # Unlock eventlock
    router.dispatch(admin, "ehc", ["eventlock", "part-1", "off"])

    # 3. Sleeping in bed blocks teleport
    services.combat.set_sleeping("part-1", True)
    player.messages.clear()
    router.dispatch(player, "spawn")
    assert player.position == (20.0, 64.0, 20.0)
    services.combat.set_sleeping("part-1", False)

    # 4. Lava hazard blocks teleport
    player.is_in_lava = True
    player.messages.clear()
    router.dispatch(player, "spawn")
    assert player.position == (20.0, 64.0, 20.0)
    player.is_in_lava = False

    # 5. Clear of all locks -> teleport succeeds
    clk.advance(5.0)
    router.dispatch(player, "spawn")
    assert player.position == (0.0, 64.0, 0.0)


# ── 5. Endstone Event Annotation & Metadata Validation ────────────────


def test_endstone_event_handlers_have_runtime_event_classes() -> None:
    for name, member in inspect.getmembers(HelpCommandsPlugin, predicate=inspect.isfunction):
        if getattr(member, "_is_event_handler", False):
            sig = inspect.signature(member)
            params = list(sig.parameters.values())
            assert len(params) == 2, f"{name} must accept (self, event)"
            ann = params[1].annotation
            assert isinstance(ann, type) and issubclass(ann, Event), (
                f"{name} parameter annotation {ann!r} must be a real Event subclass at runtime"
            )


def test_slot_and_warp_normalizers() -> None:
    assert normalize_home_slot(None) == "1"
    assert normalize_home_slot("2") == "2"
    assert normalize_home_slot("home3") == "3"
    assert normalize_home_slot("4") is None
    assert normalize_warp_name("Spawn_Hub-1") == "spawn_hub-1"
    assert normalize_warp_name("invalid name!") is None


def test_direct_eldia_worlds_api_package_integration(tmp_path: Path) -> None:
    registry = WorldRegistry(tmp_path / "worlds.json")
    registry.load()
    sky_world = registry.create("sky_kingdom", world_type="void", dimension="overworld", border_radius=500)
    api = WorldsAPI(registry=registry)

    clk = _FakeClock()
    services = HelpCommandServices(
        data_folder=tmp_path,
        create_files=True,
        worlds_api=api,
        clock=clk,
    )
    router = HelpCommandRouter(services)

    admin = MockCommandActor(
        name="Admin",
        player_key="admin-1",
        is_op=True,
        dimension_name="overworld",
        world_name="overworld",
        position=(float(sky_world.center_x + 12), 120.0, float(sky_world.center_z - 8)),
    )

    # /setspawn automatically detects "sky_kingdom" from eldia_worlds.WorldsAPI and syncs registry spawn
    router.dispatch(admin, "setspawn")
    main_spawn = services.spawn.get_main_spawn()
    assert main_spawn is not None
    assert main_spawn.world_name == "sky_kingdom"
    assert sky_world.spawn_y == 120.0

    # /setwarp inside sky_kingdom also records world_name="sky_kingdom" via eldia_worlds API
    router.dispatch(admin, "setwarp", ["sky_shop"])
    warp_pt = services.warps.get_warp("sky_shop")
    assert warp_pt is not None
    assert warp_pt.world_name == "sky_kingdom"
