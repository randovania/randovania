from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter.hints.hint_formatters import RelativeFormatter
from randovania.exporter.hints.pickup_hint import PickupHint, create_pickup_hint
from randovania.game_description.hint import LocationHint, RelativeDataItem

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration


class RelativeItemFormatter(RelativeFormatter):
    def __init__(
        self, patches: GamePatches, distance_painter: Callable[[str, bool], str], players_config: PlayersConfiguration
    ):
        super().__init__(patches, distance_painter)
        self.players_config = players_config

    def format(self, game: RandovaniaGame, pick_hint: PickupHint, hint: LocationHint, with_color: bool) -> str:
        assert isinstance(hint.precision.relative, RelativeDataItem)
        index = hint.precision.relative.other_index

        other_area = self.region_list.nodes_to_area(self.region_list.node_from_pickup_index(index))
        phint = create_pickup_hint(
            self.patches.pickup_assignment,
            self.region_list,
            hint.precision.relative.precision,
            self.patches.pickup_assignment.get(index),
            self.players_config,
            False,
        )
        assert phint.world_name is None
        other_name = f"{phint.determiner}{phint.pickup_name}"
        return self.relative_format(pick_hint, hint, other_area, other_name, with_color)
