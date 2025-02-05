from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
    from randovania.layout.preset_describer import GamePresetDescriber


def _get_none(hash: bytes) -> str | None:
    return None


@dataclass(frozen=True)
class GameLayout:
    configuration: type[BaseConfiguration]
    # TODO Revise this text
    """Logic and gameplay settings such as teleporter shuffling."""

    cosmetic_patches: type[BaseCosmeticPatches]
    """Cosmetic settings such as item icons on maps."""

    preset_describer: GamePresetDescriber
    """Contains game-specific preset descriptions, used by the preset screen and Discord bot."""

    get_ingame_hash: Callable[[bytes], str | None] = _get_none
    """(Optional) Takes a layout hash bytes and produces a string representing how the game
    will represent the hash in-game. Only override if the game cannot display arbitrary text on the title screen."""
