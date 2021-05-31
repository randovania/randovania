import collections
from typing import Dict, List

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.games.prime.patcher_file_lib import hint_lib
from randovania.interface_common.players_configuration import PlayersConfiguration


def locations_for_major_pickups_and_keys(
        all_patches: Dict[int, GamePatches],
        players_config: PlayersConfiguration,
        area_namers: Dict[int, hint_lib.AreaNamer],
) -> Dict[PickupEntry, List[str]]:
    """

    :param all_patches:
    :param players_config:
    :param area_namers:
    :return:
    """

    results: Dict[PickupEntry, List[str]] = collections.defaultdict(list)

    def make_det(index):
        return hint_lib.player_determiner(players_config, index).s

    for player_index, patches in all_patches.items():
        for pickup_index, target in patches.pickup_assignment.items():
            if target.player != players_config.player_index:
                continue

            item_category = target.pickup.item_category
            if item_category.is_major_category or item_category.is_key:
                hint = area_namers[player_index].location_name(pickup_index, hide_area=False, color=None)
                if players_config.is_multiworld:
                    hint = f"{make_det(player_index)}{hint}"

                results[target.pickup].append(hint)

    return results
