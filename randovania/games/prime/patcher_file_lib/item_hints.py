import collections

import typing
from typing import Tuple, Optional

from randovania.game_description.item.item_category import USELESS_ITEM_CATEGORY, ItemCategory
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintItemPrecision, Hint, RelativeDataItem
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.games.prime.patcher_file_lib import hint_lib
from randovania.games.prime.patcher_file_lib.hint_formatters import RelativeFormatter
from randovania.games.prime.patcher_file_lib.hint_lib import Determiner
from randovania.interface_common.players_configuration import PlayersConfiguration

_DET_AN = [
    "Annihilator Beam",
    "Amber Translator",
    "Echo Visor",
    "Emerald Translator",
    "Energy Transfer Module",
    "Energy Tank",
    "Ice Beam",
    "Ice Spreader",
    "X-Ray Visor"
]

_DET_NULL = []
_DET_NULL.extend(f"{temple} Key {i}"
                 for i in range(1, 4)
                 for temple in ("Dark Agon", "Dark Torvus", "Ing Hive"))
_DET_NULL.extend(f"Sky Temple Key {i}" for i in range(1, 10))


class RelativeItemFormatter(RelativeFormatter):
    def __init__(self, world_list: WorldList, patches: GamePatches, players_config: PlayersConfiguration):
        super().__init__(world_list, patches)
        self.players_config = players_config

    def format(self, determiner: Determiner, pickup: str, hint: Hint) -> str:
        relative = typing.cast(RelativeDataItem, hint.precision.relative)
        index = relative.other_index

        other_area = self.world_list.nodes_to_area(self._index_to_node[index])
        other_determiner, name = create_pickup_hint(self.patches.pickup_assignment, self.world_list,
                                                    relative.precision,
                                                    self.patches.pickup_assignment.get(index),
                                                    self.players_config,
                                                    False)
        other_name = f"{other_determiner}{name}"

        return self.relative_format(determiner, pickup, hint, other_area, other_name)


def _calculate_determiner(pickup_assignment: PickupAssignment, pickup: PickupEntry, world_list: WorldList) -> str:
    name_count = collections.defaultdict(int)
    for i in range(world_list.num_pickup_nodes):
        index = PickupIndex(i)
        if index in pickup_assignment:
            pickup_name = pickup_assignment[index].pickup.name
        else:
            pickup_name = "Energy Transfer Module"
        name_count[pickup_name] += 1

    if pickup.name in _DET_NULL:
        determiner = ""
    elif name_count[pickup.name] == 1:
        determiner = "the "
    elif pickup.name in _DET_AN:
        determiner = "an "
    else:
        determiner = "a "

    return determiner


def create_pickup_hint(pickup_assignment: PickupAssignment,
                       world_list: WorldList,
                       precision: HintItemPrecision,
                       target: Optional[PickupTarget],
                       players_config: PlayersConfiguration,
                       include_owner: bool,
                       ) -> Tuple[Determiner, str]:
    """

    :param pickup_assignment:
    :param world_list:
    :param precision:
    :param target:
    :param players_config:
    :param include_owner:
    :return:
    """
    if target is None:
        target = PickupTarget(
            pickup=PickupEntry(
                name="Energy Transfer Module",
                progression=tuple(),
                model=PickupModel(
                    game=RandovaniaGame.METROID_PRIME_ECHOES,
                    name="EnergyTransferModule",
                ),
                item_category=USELESS_ITEM_CATEGORY,
                broad_category=USELESS_ITEM_CATEGORY,
            ),
            player=players_config.player_index,
        )

    if precision is HintItemPrecision.GENERAL_CATEGORY:
        details = target.pickup.item_category.general_details

    elif precision is HintItemPrecision.PRECISE_CATEGORY:
        details = target.pickup.item_category.hint_details

    elif precision is HintItemPrecision.BROAD_CATEGORY:
        details = target.pickup.broad_category.hint_details

    elif precision is HintItemPrecision.DETAILED:
        details = _calculate_determiner(pickup_assignment, target.pickup, world_list), target.pickup.name

    elif precision is HintItemPrecision.NOTHING:
        details = "an ", "item"

    else:
        raise ValueError(f"Unknown precision: {precision}")

    if include_owner and players_config.is_multiworld:
        determiner = hint_lib.player_determiner(players_config, target.player)
    else:
        determiner = Determiner(details[0], True)

    return determiner, details[1]
