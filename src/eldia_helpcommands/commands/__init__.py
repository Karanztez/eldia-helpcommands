"""Command router, context, and testable actor abstraction for Eldia HelpCommands."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from eldia_helpcommands.core.types import TeleportPoint
    from eldia_helpcommands.managers import HelpCommandServices


class CommandActor(Protocol):
    """Protocol representing a player or command sender."""

    @property
    def player_key(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def is_op(self) -> bool: ...

    @property
    def dimension_name(self) -> str: ...

    @property
    def world_name(self) -> str: ...

    @property
    def position(self) -> tuple[float, float, float]: ...

    @property
    def rotation(self) -> tuple[float, float]: ...

    @property
    def is_dead(self) -> bool: ...

    @property
    def is_in_lava(self) -> bool: ...

    @property
    def is_gliding(self) -> bool: ...

    @property
    def scoreboard_tags(self) -> tuple[str, ...]: ...

    @property
    def raw_player(self) -> Any: ...

    def send_message(self, message: str) -> None: ...

    def teleport_to_point(self, point: TeleportPoint) -> bool: ...


@dataclass
class MockCommandActor:
    """In-memory command actor for headless unit testing."""

    name: str = "Steve"
    player_key: str = "steve-uuid"
    is_op: bool = False
    dimension_name: str = "Overworld"
    world_name: str = "Overworld"
    position: tuple[float, float, float] = (0.0, 64.0, 0.0)
    rotation: tuple[float, float] = (0.0, 0.0)
    is_dead: bool = False
    is_in_lava: bool = False
    is_gliding: bool = False
    scoreboard_tags: tuple[str, ...] = ()
    messages: list[str] = field(default_factory=list)
    raw_player: Any = None

    def send_message(self, message: str) -> None:
        self.messages.append(message)

    def teleport_to_point(self, point: TeleportPoint) -> bool:
        return self.teleport_to_coords(
            dimension=point.dimension,
            world_name=point.world_name,
            x=point.x,
            y=point.y,
            z=point.z,
            yaw=point.yaw,
            pitch=point.pitch,
        )

    def teleport_to_coords(
        self,
        *,
        dimension: str,
        world_name: str,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
    ) -> bool:
        self.dimension_name = dimension
        self.world_name = world_name
        self.position = (x, y, z)
        self.rotation = (yaw, pitch)
        return True


@dataclass(slots=True)
class CommandContext:
    """Invocation context passed to command handlers."""

    actor: CommandActor
    services: HelpCommandServices
    command_name: str
    args: tuple[str, ...]


@dataclass(slots=True)
class CommandSpec:
    """Metadata and handler for a registered plugin command."""

    name: str
    description: str
    usage: str
    handler: Callable[[CommandContext], bool]
    aliases: tuple[str, ...] = ()
    permission: str = "eldia_helpcommands.command.user"
    op_only: bool = False


class HelpCommandRouter:
    """Dispatches `/spawn`, `/hub`, `/setspawn`, `/sethome`, `/delhome`, `/home`, `/setwarp`, `/delwarp`, `/warp`, `/ehc`."""

    def __init__(self, services: HelpCommandServices) -> None:
        self.services = services
        self._specs: dict[str, CommandSpec] = {}
        self._aliases: dict[str, str] = {}

        from eldia_helpcommands.commands.handlers import register_all_commands

        register_all_commands(self)

    def register(self, spec: CommandSpec) -> None:
        canonical = spec.name.lower().lstrip("/")
        self._specs[canonical] = spec
        self._aliases[canonical] = canonical
        for alias in spec.aliases:
            self._aliases[alias.lower().lstrip("/")] = canonical

    @property
    def specs(self) -> dict[str, CommandSpec]:
        return dict(self._specs)

    def resolve(self, name: str) -> CommandSpec | None:
        key = name.lower().lstrip("/")
        canonical = self._aliases.get(key)
        if canonical is None:
            return None
        return self._specs.get(canonical)

    def dispatch(
        self,
        actor: CommandActor,
        command_name: str,
        args: list[str] | tuple[str, ...] = (),
    ) -> bool:
        spec = self.resolve(command_name)
        if spec is None:
            return False

        # Normalize flattened single-string `<args: message>` from Endstone
        norm_args: list[str] = []
        for token in args:
            norm_args.extend(part for part in str(token).split() if part)

        if spec.op_only and not actor.is_op:
            if spec.name in {"warp"}:
                actor.send_message(self.services.lang.msg("warp_op_only"))
            else:
                actor.send_message(self.services.lang.msg("no_permission"))
            return True

        ctx = CommandContext(
            actor=actor,
            services=self.services,
            command_name=spec.name,
            args=tuple(norm_args),
        )
        return spec.handler(ctx)
