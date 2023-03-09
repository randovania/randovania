from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.pickup_creator import create_sky_temple_key
from randovania.layout.exceptions import InvalidConfiguration


def add_sky_temple_key_distribution_logic(game: GameDescription,
                                          mode: LayoutSkyTempleKeyMode,
                                          ) -> PoolResults:
    """
    Adds the given Sky Temple Keys to the item pool
    :param game:
    :param mode:
    :return:
    """
    resource_database = game.resource_database
    item_pool: list[PickupEntry] = []
    new_assignment: dict[PickupIndex, PickupEntry] = {}
    initial_resources = ResourceCollection.with_database(resource_database)

    if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        locations_to_place = _GUARDIAN_INDICES[:]
        if mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
            locations_to_place += _SUB_GUARDIAN_INDICES

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

    for automatic_key_number in range(first_automatic_key, 9):
        initial_resources.add_resource_gain(
            create_sky_temple_key(automatic_key_number, resource_database).all_resources,
        )

    return PoolResults(item_pool, new_assignment, initial_resources)


# FIXME: use node identifiers
_GUARDIAN_INDICES = [
    PickupIndex(43),  # Dark Suit
    PickupIndex(79),  # Dark Visor
    PickupIndex(115),  # Annihilator Beam
]
_SUB_GUARDIAN_INDICES = [
    PickupIndex(38),  # Morph Ball Bomb
    PickupIndex(37),  # Space Jump Boots
    PickupIndex(75),  # Boost Ball
    PickupIndex(86),  # Grapple Beam
    PickupIndex(102),  # Spider Ball
    PickupIndex(88),  # Main Power Bombs
]
