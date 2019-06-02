import copy
import dataclasses

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import PickupNode
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import ConditionalResources, ResourceConversion, PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import find_resource_info_with_long_name
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.generator.item_pool import pickup_creator
from randovania.layout import game_patches_serializer
from randovania.layout.game_patches_serializer import BitPackPickupEntry
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.major_item_state import MajorItemState


@pytest.fixture(
    params=[
        {},
        {"starting_item": "Morph Ball"},
        {"elevator": [1572998, "Temple Grounds/Transport to Agon Wastes"]},
        {"translator": [(10, "Mining Plaza", "Cobalt Translator"), (12, "Great Bridge", "Emerald Translator")]},
        {"pickup": ['HUhMANYCAA==', "Screw Attack"]},
        {"hint": [1000, {"location_precision": "detailed", "item_precision": "detailed", "target": 50}]},
    ],
    name="patches_with_data")
def _patches_with_data(request, echoes_game_data, echoes_item_database):
    game = data_reader.decode_data(echoes_game_data)

    data = {
        "starting_location": "Temple Grounds/Landing Site",
        "starting_items": {},
        "elevators": {
            "Temple Grounds/Temple Transport C": "Great Temple/Temple Transport C",
            "Temple Grounds/Transport to Agon Wastes": "Agon Wastes/Transport to Temple Grounds",
            "Temple Grounds/Transport to Torvus Bog": "Torvus Bog/Transport to Temple Grounds",
            "Temple Grounds/Temple Transport B": "Great Temple/Temple Transport B",
            "Temple Grounds/Sky Temple Gateway": "Great Temple/Sky Temple Energy Controller",
            "Temple Grounds/Transport to Sanctuary Fortress": "Sanctuary Fortress/Transport to Temple Grounds",
            "Temple Grounds/Temple Transport A": "Great Temple/Temple Transport A",
            "Great Temple/Temple Transport A": "Temple Grounds/Temple Transport A",
            "Great Temple/Temple Transport C": "Temple Grounds/Temple Transport C",
            "Great Temple/Temple Transport B": "Temple Grounds/Temple Transport B",
            "Great Temple/Sky Temple Energy Controller": "Temple Grounds/Sky Temple Gateway",
            "Agon Wastes/Transport to Temple Grounds": "Temple Grounds/Transport to Agon Wastes",
            "Agon Wastes/Transport to Torvus Bog": "Torvus Bog/Transport to Agon Wastes",
            "Agon Wastes/Transport to Sanctuary Fortress": "Sanctuary Fortress/Transport to Agon Wastes",
            "Torvus Bog/Transport to Temple Grounds": "Temple Grounds/Transport to Torvus Bog",
            "Torvus Bog/Transport to Agon Wastes": "Agon Wastes/Transport to Torvus Bog",
            "Torvus Bog/Transport to Sanctuary Fortress": "Sanctuary Fortress/Transport to Torvus Bog",
            "Sanctuary Fortress/Transport to Temple Grounds": "Temple Grounds/Transport to Sanctuary Fortress",
            "Sanctuary Fortress/Transport to Agon Wastes": "Agon Wastes/Transport to Sanctuary Fortress",
            "Sanctuary Fortress/Transport to Torvus Bog": "Torvus Bog/Transport to Sanctuary Fortress"
        },
        "translators": {},
        "locations": {
            world.name: {
                game.world_list.node_name(node): "Nothing"
                for node in world.all_nodes
                if node.is_resource_node and isinstance(node, PickupNode)
            }
            for world in sorted(game.world_list.worlds, key=lambda w: w.name)
        },
        "hints": {},
        "_locations_internal": "",
    }
    patches = GamePatches.with_game(game)

    if request.param.get("starting_item"):
        item_name = request.param.get("starting_item")
        patches = patches.assign_extra_initial_items({
            find_resource_info_with_long_name(game.resource_database.item, item_name): 1,
        })
        data["starting_items"][item_name] = 1

    if request.param.get("elevator"):
        elevator_id, elevator_source = request.param.get("elevator")
        elevator_connection = copy.copy(patches.elevator_connection)
        elevator_connection[elevator_id] = game.starting_location

        patches = dataclasses.replace(patches, elevator_connection=elevator_connection)
        data["elevators"][elevator_source] = "Temple Grounds/Landing Site"

    if request.param.get("translator"):
        gates = {}
        for index, gate_name, translator in request.param.get("translator"):
            gates[TranslatorGate(index)] = find_resource_info_with_long_name(game.resource_database.item, translator)
            data["translators"][gate_name] = translator

        patches = patches.assign_gate_assignment(gates)

    if request.param.get("pickup"):
        data["_locations_internal"], pickup_name = request.param.get("pickup")
        pickup = pickup_creator.create_major_item(echoes_item_database.major_items[pickup_name],
                                                  MajorItemState(), True, game.resource_database,
                                                  None, False)

        patches = patches.assign_new_pickups([(PickupIndex(5), pickup)])
        data["locations"]["Temple Grounds"]['Transport to Agon Wastes/Pickup (Missile)'] = pickup_name

    if request.param.get("hint"):
        asset, hint = request.param.get("hint")
        patches = patches.assign_hint(LogbookAsset(asset), Hint.from_json(hint))
        data["hints"][str(asset)] = hint

    return data, patches


def test_encode(patches_with_data, echoes_game_data):
    expected, patches = patches_with_data

    # Run
    encoded = game_patches_serializer.serialize(patches, echoes_game_data)

    # Assert
    for key, value in expected["locations"].items():
        assert encoded["locations"][key] == value
    assert encoded == expected


def test_decode(patches_with_data):
    encoded, expected = patches_with_data

    # Run
    decoded = game_patches_serializer.decode(encoded, LayoutConfiguration.default())

    # Assert
    assert decoded == expected


@pytest.mark.parametrize("has_convert", [False, True])
def test_bit_pack_pickup_entry(has_convert: bool, echoes_resource_database):
    # Setup
    name = "Some Random Name"
    if has_convert:
        convert_resources = (
            ResourceConversion(
                find_resource_info_with_long_name(echoes_resource_database.item, "Morph Ball"),
                find_resource_info_with_long_name(echoes_resource_database.item, "Item Percentage")
            ),
        )
    else:
        convert_resources = ()

    pickup = PickupEntry(
        name=name,
        model_index=26,
        item_category=ItemCategory.TEMPLE_KEY,
        resources=(
            ConditionalResources(
                "Morph Ball", None,
                (
                    (find_resource_info_with_long_name(echoes_resource_database.item, "Morph Ball"), 2),
                    (find_resource_info_with_long_name(echoes_resource_database.item, "Item Percentage"), 5),
                ),
            ),
            ConditionalResources(
                "Grapple Beam", find_resource_info_with_long_name(echoes_resource_database.item, "Morph Ball"),
                (
                    (find_resource_info_with_long_name(echoes_resource_database.item, "Grapple Beam"), 3),
                ),
            )
        ),
        convert_resources=convert_resources
    )

    # Run
    encoded = bitpacking.pack_value(BitPackPickupEntry(pickup, echoes_resource_database))
    decoder = BitPackDecoder(encoded)
    decoded = BitPackPickupEntry.bit_pack_unpack(decoder, name, echoes_resource_database)

    # Assert
    assert pickup == decoded
