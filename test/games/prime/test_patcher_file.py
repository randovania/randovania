from randovania.game_description.area_location import AreaLocation
from randovania.games.prime import patcher_file
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
