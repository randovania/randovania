from typing import Callable

from randovania.exporter.hints.hint_formatters import RelativeFormatter
from randovania.exporter.hints.pickup_hint import PickupHint, create_pickup_hint
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, RelativeDataItem
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import PlayersConfiguration


class RelativeItemFormatter(RelativeFormatter):
    def __init__(self, patches: GamePatches, distance_painter: Callable[[str, bool], str],
                 players_config: PlayersConfiguration):
        super().__init__(patches, distance_painter)
        self.players_config = players_config

    def format(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        assert isinstance(hint.precision.relative, RelativeDataItem)
        index = hint.precision.relative.other_index

        other_area = self.world_list.nodes_to_area(self.world_list.node_from_pickup_index(index))
        phint = create_pickup_hint(
            self.patches.pickup_assignment, self.world_list,
            hint.precision.relative.precision,
            self.patches.pickup_assignment.get(index),
            self.players_config,
            False,
        )
        assert phint.player_name is None
        other_name = f"{phint.determiner}{phint.pickup_name}"
        return self.relative_format(pick_hint, hint, other_area, other_name, with_color)
