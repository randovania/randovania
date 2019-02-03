import dataclasses

from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.games.prime import patcher_file, default_data, claris_randomizer
from randovania.layout import starting_resources
from randovania.layout.starting_resources import StartingResources, StartingResourcesConfiguration


def test_create_spawn_point_field(echoes_resource_database, empty_patches):
    # Setup
    patches = empty_patches.assign_starting_location(AreaLocation(100, 5000))
    capacities = [
        {'amount': starting_resources._vanilla_item_loss_enabled_items.get(item.index, 0), 'index': item.index}
        for item in echoes_resource_database.item
    ]

    # Run
    result = patcher_file._create_spawn_point_field(
        echoes_resource_database,
        StartingResources.from_non_custom_configuration(StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED),
        patches
    )

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
    result = patcher_file._create_elevators_field(game.world_list, empty_patches)

    # Assert
    assert result == []


def test_create_elevators_field_elevators_for_a_seed(echoes_resource_database, empty_patches):
    # Setup
    seed_number = 50000
    game = data_reader.decode_data(default_data.decode_default_prime2(), False)
    patches = dataclasses.replace(
        empty_patches,
        elevator_connection={
            589851: AreaLocation(464164546, 900285955),
            1572998: AreaLocation(1039999561, 3479543630),
        })

    # Run
    result = patcher_file._create_elevators_field(game.world_list, patches)

    # Assert
    assert result == [
        {"origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2918020398},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
         "room_name": "Transport to Sanctuary Fortress", },
        {"origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1660916974},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
         "room_name": "Transport to Torvus Bog", },
    ]
