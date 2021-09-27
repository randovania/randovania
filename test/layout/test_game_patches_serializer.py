import collections
import copy
import dataclasses
import uuid

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description import data_reader
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.hint import Hint
from randovania.game_description.world.node import PickupNode
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry, \
    ResourceLock, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world.teleporter import Teleporter
from randovania.games.game import RandovaniaGame
from randovania.generator import generator
from randovania.generator.item_pool import pickup_creator, pool_creator
from randovania.layout import game_patches_serializer
from randovania.layout.base.major_item_state import MajorItemState
from randovania.layout.permalink import Permalink
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
from randovania.network_common.pickup_serializer import BitPackPickupEntry


@pytest.fixture(
    params=[
        {},
        {"starting_item": "Morph Ball"},
        {"elevator": [Teleporter(1006255871, 1660916974, 1572998), "Temple Grounds/Transport to Agon Wastes"]},
        {"translator": [(10, "Mining Plaza", "Cobalt Translator"), (12, "Great Bridge", "Emerald Translator")]},
        {"pickup": "Morph Ball Bomb"},
        {"hint": [1000, {"hint_type": "location",
                         "dark_temple": None,
                         "precision": {"location": "detailed", "item": "detailed", "relative": None,
                                       "include_owner": False},
                         "target": 50}]},
    ],
    name="patches_with_data")
def _patches_with_data(request, echoes_game_description, echoes_item_database):
    game = echoes_game_description

    data = {
        "starting_location": "Temple Grounds/Landing Site",
        "starting_items": {},
        "elevators": {
            "Temple Grounds/Temple Transport C": "Great Temple/Temple Transport C",
            "Temple Grounds/Transport to Agon Wastes": "Agon Wastes/Transport to Temple Grounds",
            "Temple Grounds/Transport to Torvus Bog": "Torvus Bog/Transport to Temple Grounds",
            "Temple Grounds/Temple Transport B": "Great Temple/Temple Transport B",
            "Temple Grounds/Transport to Sanctuary Fortress": "Sanctuary Fortress/Transport to Temple Grounds",
            "Temple Grounds/Temple Transport A": "Great Temple/Temple Transport A",
            "Great Temple/Temple Transport A": "Temple Grounds/Temple Transport A",
            "Great Temple/Temple Transport C": "Temple Grounds/Temple Transport C",
            "Great Temple/Temple Transport B": "Temple Grounds/Temple Transport B",
            "Sky Temple Grounds/Sky Temple Gateway": "Sky Temple/Sky Temple Energy Controller",
            "Sky Temple/Sky Temple Energy Controller": "Sky Temple Grounds/Sky Temple Gateway",
            "Agon Wastes/Transport to Temple Grounds": "Temple Grounds/Transport to Agon Wastes",
            "Agon Wastes/Transport to Torvus Bog": "Torvus Bog/Transport to Agon Wastes",
            "Agon Wastes/Transport to Sanctuary Fortress": "Sanctuary Fortress/Transport to Agon Wastes",
            "Torvus Bog/Transport to Temple Grounds": "Temple Grounds/Transport to Torvus Bog",
            "Torvus Bog/Transport to Agon Wastes": "Agon Wastes/Transport to Torvus Bog",
            "Torvus Bog/Transport to Sanctuary Fortress": "Sanctuary Fortress/Transport to Torvus Bog",
            "Sanctuary Fortress/Transport to Temple Grounds": "Temple Grounds/Transport to Sanctuary Fortress",
            "Sanctuary Fortress/Transport to Agon Wastes": "Agon Wastes/Transport to Sanctuary Fortress",
            "Sanctuary Fortress/Transport to Torvus Bog": "Torvus Bog/Transport to Sanctuary Fortress",
            "Sanctuary Fortress/Aerie": "Sanctuary Fortress/Aerie Transport Station",
            "Sanctuary Fortress/Aerie Transport Station": "Sanctuary Fortress/Aerie",
        },
        "translators": {},
        "locations": {},
        "hints": {}
    }
    patches = dataclasses.replace(game.create_game_patches(), player_index=0)

    locations = collections.defaultdict(dict)
    for world, area, node in game.world_list.all_worlds_areas_nodes:
        if node.is_resource_node and isinstance(node, PickupNode):
            world_name = world.dark_name if area.in_dark_aether else world.name
            locations[world_name][game.world_list.node_name(node)] = game_patches_serializer._ETM_NAME

    data["locations"] = {
        world: {
            area: item
            for area, item in sorted(locations[world].items())
        }
        for world in sorted(locations.keys())
    }

    if request.param.get("starting_item"):
        item_name = request.param.get("starting_item")
        patches = patches.assign_extra_initial_items({
            find_resource_info_with_long_name(game.resource_database.item, item_name): 1,
        })
        data["starting_items"][item_name] = 1

    if request.param.get("elevator"):
        teleporter, elevator_source = request.param.get("elevator")
        elevator_connection = copy.copy(patches.elevator_connection)
        elevator_connection[teleporter] = game.starting_location

        patches = dataclasses.replace(patches, elevator_connection=elevator_connection)
        data["elevators"][elevator_source] = "Temple Grounds/Landing Site"

    if request.param.get("translator"):
        gates = {}
        for index, gate_name, translator in request.param.get("translator"):
            gates[TranslatorGate(index)] = find_resource_info_with_long_name(game.resource_database.item, translator)
            data["translators"][gate_name] = translator

        patches = patches.assign_gate_assignment(gates)

    if request.param.get("pickup"):
        pickup_name = request.param.get("pickup")
        pickup = pickup_creator.create_major_item(echoes_item_database.major_items[pickup_name],
                                                  MajorItemState(), True, game.resource_database,
                                                  None, False)

        patches = patches.assign_new_pickups([(PickupIndex(5), PickupTarget(pickup, 0))])
        data["locations"]["Temple Grounds"]['Transport to Agon Wastes/Pickup (Missile)'] = pickup_name

    if request.param.get("hint"):
        asset, hint = request.param.get("hint")
        patches = patches.assign_hint(LogbookAsset(asset), Hint.from_json(hint))
        data["hints"][str(asset)] = hint

    return data, patches


def test_encode(patches_with_data):
    expected, patches = patches_with_data

    # Run
    encoded = game_patches_serializer.serialize_single(0, 1, patches, RandovaniaGame.METROID_PRIME_ECHOES)

    # Assert
    for key, value in expected["locations"].items():
        assert encoded["locations"][key] == value
    assert encoded == expected


def test_decode(patches_with_data, default_layout_configuration):
    encoded, expected = patches_with_data

    game = data_reader.decode_data(default_layout_configuration.game_data)
    pool = pool_creator.calculate_pool_results(default_layout_configuration, game.resource_database)

    # Run
    decoded = game_patches_serializer.decode_single(0, {0: pool}, game, encoded, default_layout_configuration)

    # Assert
    assert decoded == expected


@pytest.mark.parametrize("has_convert", [False, True])
def test_bit_pack_pickup_entry(has_convert: bool, echoes_resource_database, generic_item_category):
    # Setup
    name = "Some Random Name"
    if has_convert:
        resource_lock = ResourceLock(
            find_resource_info_with_long_name(echoes_resource_database.item, "Morph Ball"),
            find_resource_info_with_long_name(echoes_resource_database.item, "Item Percentage"),
            find_resource_info_with_long_name(echoes_resource_database.item, "Space Jump Boots"),
        )
    else:
        resource_lock = None

    pickup = PickupEntry(
        name=name,
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_CORRUPTION,
            name="HyperMissile",
        ),
        item_category=generic_item_category,
        broad_category=generic_item_category, 
        progression=(
            (find_resource_info_with_long_name(echoes_resource_database.item, "Morph Ball"), 1),
            (find_resource_info_with_long_name(echoes_resource_database.item, "Grapple Beam"), 1),
        ),
        extra_resources=(
            (find_resource_info_with_long_name(echoes_resource_database.item, "Item Percentage"), 5),
        ),
        resource_lock=resource_lock
    )

    # Run
    encoded = bitpacking.pack_value(BitPackPickupEntry(pickup, echoes_resource_database))
    decoder = BitPackDecoder(encoded)
    decoded = BitPackPickupEntry.bit_pack_unpack(decoder, echoes_resource_database)

    # Assert
    assert pickup == decoded


@pytest.mark.asyncio
async def test_round_trip_generated_patches(default_preset):
    # Setup
    preset = dataclasses.replace(
        default_preset,
        uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'),
        base_preset_uuid=default_preset.uuid,
        configuration=dataclasses.replace(
            default_preset.configuration,
            trick_level=TrickLevelConfiguration(
                minimal_logic=True,
                specific_levels={},
                game=default_preset.game,
            )
        )
    )

    description = await generator._create_description(
        permalink=Permalink(
            seed_number=1000,
            spoiler=True,
            presets={0: preset},
        ),
        status_update=lambda x: None,
        attempts=0,
    )
    all_patches = description.all_patches

    # Run
    encoded = game_patches_serializer.serialize(all_patches, {0: default_preset.game})
    decoded = game_patches_serializer.decode(encoded, {0: preset.configuration})

    # Assert
    assert all_patches == decoded
