from __future__ import annotations

import collections
import dataclasses
from typing import TYPE_CHECKING

from randovania.exporter.hints.determiner import Determiner
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.hint import HintItemPrecision
from randovania.game_description.hint_features import HintDetails, HintFeature
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.pickup_pool import pickup_creator

if TYPE_CHECKING:
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.interface_common.players_configuration import PlayersConfiguration

_DET_AN = [
    "Annihilator Beam",
    "Amber Translator",
    "Echo Visor",
    "Emerald Translator",
    "Energy Part",
    "Energy Transfer Module",
    "Energy Tank",
    "Ice Beam",
    "Ice Spreader",
    "X-Ray Visor",
]

_DET_NULL: list[str] = []
_DET_NULL.extend(f"{temple} Key {i}" for i in range(1, 4) for temple in ("Dark Agon", "Dark Torvus", "Ing Hive"))
_DET_NULL.extend(f"Sky Temple Key {i}" for i in range(1, 10))


@dataclasses.dataclass(frozen=True)
class PickupHint:
    determiner: Determiner
    world_name: str | None
    pickup_name: str


def _calculate_determiner(pickup_assignment: PickupAssignment, pickup: PickupEntry, region_list: RegionList) -> str:
    name_count: dict[str, int] = collections.defaultdict(int)
    for i in range(region_list.num_pickup_nodes):
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


def create_pickup_hint(
    pickup_assignment: PickupAssignment,
    region_list: RegionList,
    precision: HintItemPrecision | HintFeature,
    target: PickupTarget | None,
    players_config: PlayersConfiguration,
    include_owner: bool,
) -> PickupHint:
    """

    :param pickup_assignment:
    :param region_list:
    :param precision:
    :param target:
    :param players_config:
    :param include_owner:
    :return:
    """
    if target is None:
        # FIXME: adjust per game
        target = PickupTarget(
            pickup=pickup_creator.create_visual_nothing(
                RandovaniaGame.METROID_PRIME_ECHOES, "EnergyTransferModule", "Energy Transfer Module"
            ),
            player=players_config.player_index,
        )

    if isinstance(precision, HintFeature):
        details = precision.hint_details

    elif precision is HintItemPrecision.DETAILED:
        details = HintDetails(_calculate_determiner(pickup_assignment, target.pickup, region_list), target.pickup.name)

    else:
        raise ValueError(f"Unknown precision: {precision}")

    determiner = Determiner(details[0])
    player = None

    if include_owner and players_config.is_multiworld:
        player = players_config.player_names[target.player]

    return PickupHint(determiner, player, details[1])
