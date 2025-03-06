from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description import default_database
from randovania.game_description.db.hint_node import HintNode, HintNodeKind

if TYPE_CHECKING:
    from randovania.game.game_enum import RandovaniaGame
    from randovania.generator.hint_distributor import HintDistributor


@dataclasses.dataclass(frozen=True)
class SpecificHintDetails:
    long_name: str
    description: str

    disabled_details: str = "Provides no useful information."
    hide_area_details: str = "Indicates only which region the pickup is in."
    precise_details: str = "Indicates the exact region and area the pickup is in."

    show_in_gui: bool = True


@dataclasses.dataclass(frozen=True)
class GameHints:
    hint_distributor: HintDistributor
    """Use AllJokesDistributor if not using hints."""

    specific_pickup_hints: dict[str, SpecificHintDetails]
    """
    Defines each category of specific pickup hint this game uses,
    as well as how they should appear in the preset tab.
    """

    @staticmethod
    def _has_hint_with_kind(game: RandovaniaGame, kind: HintNodeKind) -> bool:
        region_list = default_database.game_description_for(game).region_list
        return any(isinstance(node, HintNode) and node.kind == kind for node in region_list.iterate_nodes())

    def has_random_hints(self, game: RandovaniaGame) -> bool:
        return GameHints._has_hint_with_kind(game, HintNodeKind.GENERIC)

    def has_specific_location_hints(self, game: RandovaniaGame) -> bool:
        return GameHints._has_hint_with_kind(game, HintNodeKind.SPECIFIC_LOCATION)

    def has_specific_pickup_hints(self, game: RandovaniaGame) -> bool:
        return bool(self.specific_pickup_hints) or GameHints._has_hint_with_kind(game, HintNodeKind.SPECIFIC_PICKUP)
