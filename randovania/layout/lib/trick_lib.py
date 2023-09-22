from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from randovania.layout.base.trick_level import LayoutTrickLevel

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.trick_resource_info import TrickResourceInfo

T = TypeVar("T")


def difficulties_for_trick(game: GameDescription, trick: TrickResourceInfo) -> set[LayoutTrickLevel]:
    return {LayoutTrickLevel.from_number(level) for level in game.get_used_trick_levels().get(trick, set())}


def used_tricks(game: GameDescription) -> set[TrickResourceInfo]:
    return {trick for trick, uses in game.get_used_trick_levels().items() if uses}
