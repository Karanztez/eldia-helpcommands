"""Bedrock Form GUI builders for `/home` (3-slot Home GUI) and `/warp` (OP Warp GUI)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eldia_helpcommands.core.types import HOME_SLOTS, TeleportPoint

if TYPE_CHECKING:
    from collections.abc import Callable

    from eldia_helpcommands.managers.lang_manager import LangManager


class HelpUIManager:
    """Builds and sends Endstone `ActionForm` menus for Homes and Warps."""

    def open_home_gui(
        self,
        player: Any,
        homes: dict[str, TeleportPoint | None],
        lang: LangManager,
        *,
        on_teleport: Callable[[str], None],
        on_set: Callable[[str], None],
        on_delete: Callable[[str], None],
    ) -> bool:
        """Open the 3-Home GUI on an Endstone `Player`.

        Returns `True` if `send_form` was called, or `False` if `endstone.form` / `send_form`
        is unavailable (in which case callers can fall back to chat output).
        """
        send_form = getattr(player, "send_form", None)
        if not callable(send_form):
            return False

        try:
            from endstone.form import ActionForm
        except ImportError:
            return False

        actions: list[tuple[str, str]] = []
        buttons: list[str] = []

        # Primary 3 buttons: Home 1, Home 2, Home 3 (Teleport if set, Save if empty)
        for slot in HOME_SLOTS:
            pt = homes.get(slot)
            if pt is not None:
                label = lang.raw(
                    "home_gui_btn_tp",
                    slot=slot,
                    world=pt.world_name,
                    x=round(pt.x),
                    y=round(pt.y),
                    z=round(pt.z),
                )
                actions.append(("tp", slot))
            else:
                label = lang.raw("home_gui_btn_empty", slot=slot)
                actions.append(("set", slot))
            buttons.append(label)

        # Secondary buttons: Overwrite or Delete existing slots
        for slot in HOME_SLOTS:
            pt = homes.get(slot)
            if pt is not None:
                buttons.append(lang.raw("home_gui_btn_set", slot=slot))
                actions.append(("set", slot))
                buttons.append(lang.raw("home_gui_btn_del", slot=slot))
                actions.append(("del", slot))

        def _on_submit(_p: Any, index: int | None) -> None:
            if index is None or index < 0 or index >= len(actions):
                return
            act, slot = actions[index]
            if act == "tp":
                on_teleport(slot)
            elif act == "set":
                on_set(slot)
            elif act == "del":
                on_delete(slot)

        form = ActionForm(
            title=lang.raw("home_gui_title"),
            content=lang.raw("home_gui_content"),
            on_submit=_on_submit,
        )
        for label in buttons:
            form.add_button(label)

        send_form(form)
        return True

    def open_warp_gui(
        self,
        player: Any,
        warps: dict[str, TeleportPoint],
        lang: LangManager,
        *,
        on_teleport: Callable[[str], None],
    ) -> bool:
        """Open the OP Warp selection GUI on an Endstone `Player`."""
        send_form = getattr(player, "send_form", None)
        if not callable(send_form) or not warps:
            return False

        try:
            from endstone.form import ActionForm
        except ImportError:
            return False

        warp_names = list(warps.keys())

        def _on_submit(_p: Any, index: int | None) -> None:
            if index is None or index < 0 or index >= len(warp_names):
                return
            on_teleport(warp_names[index])

        form = ActionForm(
            title=lang.raw("warp_gui_title"),
            content=lang.raw("warp_gui_content"),
            on_submit=_on_submit,
        )
        for name in warp_names:
            pt = warps[name]
            form.add_button(
                lang.raw(
                    "warp_gui_btn",
                    name=name,
                    world=pt.world_name,
                    x=round(pt.x),
                    y=round(pt.y),
                    z=round(pt.z),
                ),
            )

        send_form(form)
        return True
