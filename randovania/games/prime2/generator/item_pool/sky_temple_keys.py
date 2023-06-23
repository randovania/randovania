from random import Random

from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_sky_temple_key
from randovania.layout.exceptions import InvalidConfiguration


def add_sky_temple_key_distribution_logic(game: GameDescription,
                                          mode: LayoutSkyTempleKeyMode,
                                          rng: Random | None,
                                          ) -> PoolResults:
    """
    Adds the given Sky Temple Keys to the item pool
    :return:
    """
    resource_database = game.resource_database
    item_pool: list[PickupEntry] = []
    new_assignment: dict[PickupIndex, PickupEntry] = {}

    if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        locations_to_place = []
        for node in game.region_list.all_nodes:
            boss = node.extra.get("boss")
            if boss is not None and isinstance(node, PickupNode):
                if boss == "guardian" or mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
                    locations_to_place.append(node.pickup_index)

        if rng is not None:
            rng.shuffle(locations_to_place)

        for key_number, location in enumerate(locations_to_place):
            new_assignment[location] = create_sky_temple_key(key_number, resource_database)
        first_automatic_key = len(locations_to_place)

    else:
        keys_to_place = mode.value
        if not isinstance(keys_to_place, int):
            raise InvalidConfiguration(f"Unknown Sky Temple Key mode: {mode}")

        for key_number in range(keys_to_place):
            item_pool.append(create_sky_temple_key(key_number, resource_database))
        first_automatic_key = keys_to_place

    starting = [
        create_sky_temple_key(automatic_key_number, resource_database)
        for automatic_key_number in range(first_automatic_key, 9)
    ]

    return PoolResults(item_pool, new_assignment, starting)
