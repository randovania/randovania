import collections
import dataclasses
import typing
import uuid

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description import data_writer
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.hint import Hint
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.pickup_entry import (
    PickupEntry, ResourceLock, PickupModel,
)
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.game import RandovaniaGame
from randovania.generator import generator
from randovania.generator.pickup_pool import pickup_creator, pool_creator
from randovania.layout import game_patches_serializer
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.network_common.pickup_serializer import BitPackPickupEntry


@pytest.fixture(
    params=[
        {},
        {"starting_pickup": "Morph Ball"},
        {"elevator": NodeIdentifier.create("Temple Grounds", "Transport to Agon Wastes",
                                           "Elevator to Agon Wastes - Transport to Temple Grounds")},
        {"configurable_nodes": [("Agon Wastes/Mining Plaza/Translator Gate", "Cobalt"),
                                ("Torvus Bog/Great Bridge/Translator Gate", "Emerald")]},
        {"pickup": "Morph Ball Bomb"},
        {"hint": ['Torvus Bog/Catacombs/Lore Scan', {
            "hint_type": "location",
            "dark_temple": None,
            "precision": {"location": "detailed", "item": "detailed",
                          "relative": None,
                          "include_owner": False},
            "target": 50}]},
    ],
    name="patches_with_data")
def _patches_with_data(request, echoes_game_description, echoes_game_patches, echoes_pickup_database):
    game = echoes_game_description
    db = game.resource_database

    data: dict[str, typing.Any] = {
        "game": echoes_game_description.game.value,
        "starting_location": "Temple Grounds/Landing Site/Save Station",
        "starting_equipment": {"pickups": []},
        "teleporters": {
            "Temple Grounds/Temple Transport C/Elevator to Great Temple - Temple Transport C": "Great Temple/Temple Transport C",
            "Temple Grounds/Transport to Agon Wastes/Elevator to Agon Wastes - Transport to Temple Grounds": "Agon Wastes/Transport to Temple Grounds",
            "Temple Grounds/Transport to Torvus Bog/Elevator to Torvus Bog - Transport to Temple Grounds": "Torvus Bog/Transport to Temple Grounds",
            "Temple Grounds/Temple Transport B/Elevator to Great Temple - Temple Transport B": "Great Temple/Temple Transport B",
            "Temple Grounds/Transport to Sanctuary Fortress/Elevator to Sanctuary Fortress - Transport to Temple Grounds": "Sanctuary Fortress/Transport to Temple Grounds",
            "Temple Grounds/Temple Transport A/Elevator to Great Temple - Temple Transport A": "Great Temple/Temple Transport A",
            "Great Temple/Temple Transport A/Elevator to Temple Grounds - Temple Transport A": "Temple Grounds/Temple Transport A",
            "Great Temple/Temple Transport C/Elevator to Temple Grounds - Temple Transport C": "Temple Grounds/Temple Transport C",
            "Great Temple/Temple Transport B/Elevator to Temple Grounds - Temple Transport B": "Temple Grounds/Temple Transport B",
            "Temple Grounds/Sky Temple Gateway/Teleport to Great Temple - Sky Temple Energy Controller": "Great Temple/Sky Temple Energy Controller",
            "Great Temple/Sky Temple Energy Controller/Teleport to Temple Grounds - Sky Temple Gateway": "Temple Grounds/Sky Temple Gateway",
            "Agon Wastes/Transport to Temple Grounds/Elevator to Temple Grounds - Transport to Agon Wastes": "Temple Grounds/Transport to Agon Wastes",
            "Agon Wastes/Transport to Torvus Bog/Elevator to Torvus Bog - Transport to Agon Wastes": "Torvus Bog/Transport to Agon Wastes",
            "Agon Wastes/Transport to Sanctuary Fortress/Elevator to Sanctuary Fortress - Transport to Agon Wastes": "Sanctuary Fortress/Transport to Agon Wastes",
            "Torvus Bog/Transport to Temple Grounds/Elevator to Temple Grounds - Transport to Torvus Bog": "Temple Grounds/Transport to Torvus Bog",
            "Torvus Bog/Transport to Agon Wastes/Elevator to Agon Wastes - Transport to Torvus Bog": "Agon Wastes/Transport to Torvus Bog",
            "Torvus Bog/Transport to Sanctuary Fortress/Elevator to Sanctuary Fortress - Transport to Torvus Bog": "Sanctuary Fortress/Transport to Torvus Bog",
            "Sanctuary Fortress/Transport to Temple Grounds/Elevator to Temple Grounds - Transport to Sanctuary Fortress": "Temple Grounds/Transport to Sanctuary Fortress",
            "Sanctuary Fortress/Transport to Agon Wastes/Elevator to Agon Wastes - Transport to Sanctuary Fortress": "Agon Wastes/Transport to Sanctuary Fortress",
            "Sanctuary Fortress/Transport to Torvus Bog/Elevator to Torvus Bog - Transport to Sanctuary Fortress": "Torvus Bog/Transport to Sanctuary Fortress",
            "Sanctuary Fortress/Aerie/Elevator to Sanctuary Fortress - Aerie Transport Station": "Sanctuary Fortress/Aerie Transport Station",
            "Sanctuary Fortress/Aerie Transport Station/Elevator to Sanctuary Fortress - Aerie": "Sanctuary Fortress/Aerie",
        },
        "dock_connections": {},
        "dock_weakness": {},
        "configurable_nodes": {},
        "locations": {},
        "hints": {}
    }
    patches = dataclasses.replace(echoes_game_patches, player_index=0)

    locations = collections.defaultdict(dict)
    for region, area, node in game.region_list.all_regions_areas_nodes:
        if node.is_resource_node and isinstance(node, PickupNode):
            world_name = region.dark_name if area.in_dark_aether else region.name
            locations[world_name][game.region_list.node_name(node)] = game_patches_serializer._ETM_NAME

    data["locations"] = {
        region: {
            area: item
            for area, item in sorted(locations[region].items())
        }
        for region in sorted(locations.keys())
    }

    def create_pickup(name, percentage=True):
        return pickup_creator.create_standard_pickup(echoes_pickup_database.standard_pickups[name],
                                                     StandardPickupState(), game.resource_database, None, False)

    if request.param.get("starting_pickup"):
        item_name = request.param.get("starting_pickup")
        patches = patches.assign_extra_starting_pickups([
            create_pickup(item_name, False),
        ])
        data["starting_equipment"]["pickups"].append(item_name)

    if request.param.get("elevator"):
        teleporter: NodeIdentifier = request.param.get("elevator")
        patches = patches.assign_elevators([
            (game.region_list.get_teleporter_node(teleporter),
             # TODO: Starting Locations are now NodeIdentifier not AreaIdentifier => was modified but can be refactored back if teleporter also uses Node instead of Area a.k.a default_node is removed
             game.starting_location.area_identifier),
        ])
        data["teleporters"][teleporter.as_string] = "Temple Grounds/Landing Site"

    if request.param.get("configurable_nodes"):
        gates = []
        for identifier, translator in request.param.get("configurable_nodes"):
            requirement = ResourceRequirement.simple(db.get_item(translator))
            gates.append((NodeIdentifier.from_string(identifier), requirement))
            data["configurable_nodes"][identifier] = data_writer.write_requirement(requirement)

        patches = patches.assign_node_configuration(gates)

    if request.param.get("pickup"):
        pickup_name = request.param.get("pickup")
        pickup = create_pickup(pickup_name)

        patches = patches.assign_new_pickups([(PickupIndex(5), PickupTarget(pickup, 0))])
        data["locations"]["Temple Grounds"]['Transport to Agon Wastes/Pickup (Missile)'] = pickup_name

    if request.param.get("hint"):
        identifier, hint = request.param.get("hint")
        patches = patches.assign_hint(NodeIdentifier.from_string(identifier), Hint.from_json(hint))
        data["hints"][identifier] = hint

    return data, patches


def test_encode(patches_with_data):
    expected, patches = patches_with_data

    # Run
    encoded = game_patches_serializer.serialize_single(0, 1, patches)

    # Assert
    for key, value in expected["locations"].items():
        assert encoded["locations"][key] == value
    assert encoded == expected


def test_decode(patches_with_data, default_echoes_configuration):
    encoded, expected = patches_with_data

    game = expected.game
    pool = pool_creator.calculate_pool_results(default_echoes_configuration, game)

    # Run
    decoded = game_patches_serializer.decode_single(0, {0: pool}, game, encoded, default_echoes_configuration)

    # Assert
    assert set(decoded.all_elevator_connections()) == set(expected.all_elevator_connections())
    assert decoded == expected


@pytest.mark.parametrize("has_convert", [False, True])
def test_bit_pack_pickup_entry(has_convert: bool, echoes_resource_database, generic_pickup_category,
                               default_generator_params):
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
        pickup_category=generic_pickup_category,
        broad_category=generic_pickup_category,
        progression=(
            (find_resource_info_with_long_name(echoes_resource_database.item, "Morph Ball"), 1),
            (find_resource_info_with_long_name(echoes_resource_database.item, "Grapple Beam"), 1),
        ),
        generator_params=default_generator_params,
        extra_resources=(
            (find_resource_info_with_long_name(echoes_resource_database.item, "Item Percentage"), 5),
        ),
        resource_lock=resource_lock,
    )

    # Run
    encoded = bitpacking.pack_value(BitPackPickupEntry(pickup, echoes_resource_database))
    decoder = BitPackDecoder(encoded)
    decoded = BitPackPickupEntry.bit_pack_unpack(decoder, echoes_resource_database)

    # Assert
    assert pickup == decoded


async def test_round_trip_generated_patches(default_preset):
    # Setup
    preset = dataclasses.replace(
        default_preset,
        uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'),
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
        generator_params=GeneratorParameters(
            seed_number=1000,
            spoiler=True,
            presets=[preset],
        ),
        status_update=lambda x: None,
        attempts=0,
    )
    all_patches = description.all_patches

    # Run
    encoded = game_patches_serializer.serialize(all_patches)
    decoded = game_patches_serializer.decode(encoded, {0: preset.configuration})
    decoded_with_original_game = {
        i: dataclasses.replace(d, game=orig.game)
        for (i, d), orig in zip(decoded.items(), all_patches.values())
    }

    # Assert
    assert all_patches == decoded_with_original_game
