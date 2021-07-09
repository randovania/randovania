from typing import Dict

from randovania.game_description import default_database
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintDarkTemple
from randovania.game_description.world.node import PickupNode
from randovania.game_description.resources import resource_info
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.games.prime import echoes_items
from randovania.games.prime.patcher_file_lib import hint_lib, guaranteed_item_hint


def create_temple_key_hint(all_patches: Dict[int, GamePatches],
                           player_index: int,
                           temple: HintDarkTemple,
                           area_namers: Dict[int, hint_lib.AreaNamer],
                           ) -> str:
    """
    Creates the text for .
    :param all_patches:
    :param player_index:
    :param temple:
    :param area_namers:
    :return:
    """
    all_world_names = set()

    _TEMPLE_NAMES = ["Dark Agon Temple", "Dark Torvus Temple", "Hive Temple"]
    temple_index = [HintDarkTemple.AGON_WASTES, HintDarkTemple.TORVUS_BOG,
                    HintDarkTemple.SANCTUARY_FORTRESS].index(temple)

    db = default_database.resource_database_for(RandovaniaGame.METROID_PRIME_ECHOES)
    items = [db.get_item(index) for index in echoes_items.DARK_TEMPLE_KEY_ITEMS[temple_index]]

    locations_for_items = guaranteed_item_hint.find_locations_that_gives_items(items, all_patches, player_index)

    for options in locations_for_items.values():
        for player, location in options:
            all_world_names.add(area_namers[player].location_name(location, hide_area=True, color=None))
            break

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
