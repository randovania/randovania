from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import PickupNode
from randovania.game_description.resources import resource_info
from randovania.game_description.world_list import WorldList
from randovania.games.prime import echoes_items

import num2words


_SKY_TEMPLE_KEY_SCAN_ASSETS = [
    0xD97685FE,
    0x32413EFD,
    0xDD8355C3,
    0x3F5F4EBA,
    0xD09D2584,
    0x3BAA9E87,
    0xD468F5B9,
    0x2563AE34,
    0xCAA1C50A,
]


def _sky_temple_key_name(key_number: int) -> str:
    return num2words.num2words(key_number, lang='en', to='ordinal_num')


def create_hints(patches: GamePatches, world_list: WorldList) -> list:
    index_to_node = {
        node.pickup_index: node
        for node in world_list.all_nodes
        if isinstance(node, PickupNode)
    }
    sky_temple_key_hints = {}

    for pickup_index, pickup in patches.pickup_assignment.items():
        resources = resource_info.convert_resource_gain_to_current_resources(pickup.resource_gain({}))

        for resource, quantity in resources.items():
            try:
                key_number = echoes_items.SKY_TEMPLE_KEY_ITEMS.index(resource.index) + 1
            except ValueError:
                continue

            assert resource.index not in sky_temple_key_hints
            sky_temple_key_hints[resource.index] = "The {} Sky Temple Key is located in {}".format(
                _sky_temple_key_name(key_number),
                world_list.area_name(
                    world_list.nodes_to_area(index_to_node[pickup_index]),
                    " - "
                )
            )

    for starting_resource, quantity in patches.starting_items.items():
        try:
            key_number = echoes_items.SKY_TEMPLE_KEY_ITEMS.index(starting_resource.index) + 1
        except ValueError:
            continue

        assert starting_resource.index not in sky_temple_key_hints
        sky_temple_key_hints[starting_resource.index] = "The {} Sky Temple Key has no need to be located.".format(
            _sky_temple_key_name(key_number),
        )

    if len(sky_temple_key_hints) != len(echoes_items.SKY_TEMPLE_KEY_ITEMS):
        raise ValueError(
            "Expected to find {} Sky Temple Keys between pickup placement and starting items, found {}".format(
                len(echoes_items.SKY_TEMPLE_KEY_ITEMS),
                len(sky_temple_key_hints)
            ))

    return [
        {
            "asset_id": _SKY_TEMPLE_KEY_SCAN_ASSETS[key_number],
            "strings": [
                sky_temple_key_hints[key_index]
            ]
        }
        for key_number, key_index in enumerate(echoes_items.SKY_TEMPLE_KEY_ITEMS)
    ]
