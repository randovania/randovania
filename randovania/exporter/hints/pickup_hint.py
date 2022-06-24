import collections
import dataclasses

from randovania.exporter.hints.determiner import Determiner
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.hint import HintItemPrecision
from randovania.game_description.item.item_category import USELESS_ITEM_CATEGORY
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
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


@dataclasses.dataclass(frozen=True)
class PickupHint:
    determiner: Determiner
    player_name: str | None
    pickup_name: str


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
                       target: PickupTarget | None,
                       players_config: PlayersConfiguration,
                       include_owner: bool,
                       ) -> PickupHint:
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

    determiner = Determiner(details[0])
    player = None

    if include_owner and players_config.is_multiworld:
        player = players_config.player_names[target.player]

    return PickupHint(determiner, player, details[1])
