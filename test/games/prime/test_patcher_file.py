import dataclasses

from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import PickupIndex, PickupEntry, SimpleResourceInfo, \
    ConditionalResources
from randovania.games.prime import patcher_file, default_data


def test_create_spawn_point_field(echoes_resource_database, empty_patches):
    # Setup
    patches = empty_patches.assign_starting_location(AreaLocation(100, 5000)).assign_extra_initial_items([
        (echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 15), 3)
    ])

    capacities = [
        {'amount': 3 if item.index == 15 else 0, 'index': item.index}
        for item in echoes_resource_database.item
    ]

    # Run
    result = patcher_file._create_spawn_point_field(patches, echoes_resource_database)

    # Assert
    assert result == {
        "location": {
            "world_asset_id": 100,
            "area_asset_id": 5000,
        },
        "amount": capacities,
        "capacity": capacities,
    }


def test_create_elevators_field_no_elevator(empty_patches):
    # Setup
    game = data_reader.decode_data(default_data.decode_default_prime2(), False)

    # Run
    result = patcher_file._create_elevators_field(empty_patches, game.world_list)

    # Assert
    assert result == []


def test_create_elevators_field_elevators_for_a_seed(echoes_resource_database, empty_patches):
    # Setup
    game = data_reader.decode_data(default_data.decode_default_prime2(), False)
    patches = dataclasses.replace(
        empty_patches,
        elevator_connection={
            589851: AreaLocation(464164546, 900285955),
            1572998: AreaLocation(1039999561, 3479543630),
            1966093: AreaLocation(2252328306, 2068511343),
        })

    # Run
    result = patcher_file._create_elevators_field(patches, game.world_list)

    # Assert
    assert result == [
        {"instance_id": 589851,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2918020398},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
         "room_name": "Transport to Sanctuary Fortress - Agon", },
        {"instance_id": 1572998,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1660916974},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
         "room_name": "Transport to Torvus Bog - Agon", },
        {"instance_id": 1966093,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2889020216},
         "target_location": {"world_asset_id": 2252328306, "area_asset_id": 2068511343},
         "room_name": "Transport to Great Temple - Sky Temple Energy Controller", },
    ]


def test_create_pickup_list(empty_patches):
    # Setup
    useless_resource = SimpleResourceInfo(0, "Useless", "Useless", ResourceType.ITEM)
    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    resource_b = SimpleResourceInfo(2, "B", "B", ResourceType.ITEM)
    pickup_a = PickupEntry("A", ((resource_a, 1),), 1, tuple(), "temple_key", 0)
    pickup_b = PickupEntry("B",
                           ((resource_b, 1), (resource_a, 1)),
                           2,
                           tuple([
                               ConditionalResources(resource_b, ((resource_a, 5),))
                           ]),
                           "", 0)

    pickup_c = PickupEntry("C", ((resource_b, 2), (resource_a, 1)), 2,
                           tuple(), "expansion", 0)

    useless_pickup = PickupEntry("Useless", ((useless_resource, 1),), 0, tuple(), "", 0)
    patches = empty_patches.assign_pickup_assignment({
        PickupIndex(0): pickup_a,
        PickupIndex(2): pickup_b,
        PickupIndex(3): pickup_a,
        PickupIndex(4): pickup_c,
    })

    # Run
    result = patcher_file._create_pickup_list(patches, useless_pickup, 5)

    # Assert
    assert len(result) == 5
    assert result[0] == {
        "pickup_index": 0,
        "model_index": 1,
        "scan": "A",
        "hud_text": ["A acquired!"],
        "sound_index": 1,
        "jingle_index": 2,
        "resources": [
            {
                "index": 1,
                "amount": 1
            }
        ],
        "conditional_resources": []
    }
    assert result[1] == {
        "pickup_index": 1,
        "scan": "Useless",
        "model_index": 0,
        "hud_text": ["Useless acquired!"],
        "sound_index": 0,
        "jingle_index": 0,
        "resources": [
            {
                "index": 0,
                "amount": 1
            }
        ],
        "conditional_resources": []
    }
    assert result[2] == {
        "pickup_index": 2,
        "scan": "B",
        "model_index": 2,
        "hud_text": ["B acquired!", "B acquired!"],
        "sound_index": 0,
        "jingle_index": 0,
        "resources": [
            {
                "index": 2,
                "amount": 1
            },
            {
                "index": 1,
                "amount": 1
            }
        ],
        "conditional_resources": [{
            "item": 2,
            "resources": [
                {
                    "index": 1,
                    "amount": 5
                }
            ]
        }]
    }
    assert result[3] == {
        "pickup_index": 3,
        "scan": "A",
        "model_index": 1,
        "hud_text": ["A acquired!"],
        "sound_index": 1,
        "jingle_index": 2,
        "resources": [
            {
                "index": 1,
                "amount": 1
            }
        ],
        "conditional_resources": []
    }
    assert result[4] == {
        "pickup_index": 4,
        "scan": "C that provides 2 B, 1 A",
        "model_index": 2,
        "hud_text": ["C acquired!"],
        "sound_index": 0,
        "jingle_index": 0,
        "resources": [
            {
                "index": 2,
                "amount": 2
            },
            {
                "index": 1,
                "amount": 1
            }
        ],
        "conditional_resources": []
    }
