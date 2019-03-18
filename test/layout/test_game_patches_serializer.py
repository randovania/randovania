import dataclasses

import pytest

from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import PickupNode
from randovania.game_description.resources import find_resource_info_with_long_name
from randovania.layout import game_patches_serializer
from randovania.layout.layout_configuration import LayoutConfiguration


@pytest.fixture(
    params=[
        {},
        {"starting_item": "Morph Ball"},
        {"elevator": [1572998, "Temple Grounds/Transport to Agon Wastes"]}
    ],
    name="patches_with_data")
def _patches_with_data(request, echoes_game_data):
    game = data_reader.decode_data(echoes_game_data)

    data = {
        "starting_location": "Temple Grounds/Landing Site",
        "starting_items": {},
        "elevators": {},
        "locations": {
            world.name: {
                game.world_list.node_name(node): "Nothing"
                for node in world.all_nodes
                if node.is_resource_node and isinstance(node, PickupNode)
            }
            for world in sorted(game.world_list.worlds, key=lambda w: w.name)
        },
    }
    patches = GamePatches.with_game(game)

    if request.param.get("starting_item"):
        item_name = request.param.get("starting_item")
        patches = patches.assign_extra_initial_items([
            (find_resource_info_with_long_name(game.resource_database.item, item_name), 1)
        ])
        data["starting_items"][item_name] = 1

    if request.param.get("elevator"):
        elevator_id, elevator_source = request.param.get("elevator")
        patches = dataclasses.replace(patches, elevator_connection={
            elevator_id: game.starting_location,
        })
        data["elevators"][elevator_source] = "Temple Grounds/Landing Site"

    return data, patches


def test_encode(patches_with_data, echoes_game_data):
    expected, patches = patches_with_data

    # Run
    encoded = game_patches_serializer.serialize(patches, echoes_game_data)

    # Assert
    assert encoded == expected


def test_decode(patches_with_data):
    encoded, expected = patches_with_data

    # Run
    decoded = game_patches_serializer.decode(encoded, LayoutConfiguration.default())

    # Assert
    assert decoded == expected
