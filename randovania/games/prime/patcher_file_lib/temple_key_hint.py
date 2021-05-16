from typing import Dict

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintDarkTemple
from randovania.game_description.node import PickupNode
from randovania.game_description.resources import resource_info
from randovania.game_description.world_list import WorldList
from randovania.games.prime import echoes_items
from randovania.games.prime.patcher_file_lib import hint_lib


def create_temple_key_hint(all_patches: Dict[int, GamePatches],
                           player_index: int,
                           temple: HintDarkTemple,
                           world_list: WorldList,
                           ) -> str:
    """
    Creates the text for .
    :param all_patches:
    :param player_index:
    :param temple:
    :param world_list:
    :return:
    """
    all_world_names = set()

    _TEMPLE_NAMES = ["Dark Agon Temple", "Dark Torvus Temple", "Hive Temple"]
    temple_index = [HintDarkTemple.AGON_WASTES, HintDarkTemple.TORVUS_BOG,
                    HintDarkTemple.SANCTUARY_FORTRESS].index(temple)
    keys = echoes_items.DARK_TEMPLE_KEY_ITEMS[temple_index]

    index_to_node = {
        node.pickup_index: node
        for node in world_list.all_nodes
        if isinstance(node, PickupNode)
    }

    for patches in all_patches.values():
        for pickup_index, target in patches.pickup_assignment.items():
            if target.player != player_index:
                continue

            resources = resource_info.convert_resource_gain_to_current_resources(target.pickup.resource_gain({}))
            for resource, quantity in resources.items():
                if quantity < 1 or resource.index not in keys:
                    continue

                pickup_node = index_to_node[pickup_index]
                all_world_names.add(world_list.world_name_from_node(pickup_node, True))

    temple_name = hint_lib.color_text(hint_lib.TextColor.ITEM, _TEMPLE_NAMES[temple_index])
    names_sorted = [hint_lib.color_text(hint_lib.TextColor.LOCATION, world) for world in sorted(all_world_names)]
    if len(names_sorted) == 0:
        return f"The keys to {temple_name} are nowhere to be found."
    elif len(names_sorted) == 1:
        return f"The keys to {temple_name} can all be found in {names_sorted[0]}."
    else:
        last = names_sorted.pop()
        front = ", ".join(names_sorted)
        return f"The keys to {temple_name} can be found in {front} and {last}."
