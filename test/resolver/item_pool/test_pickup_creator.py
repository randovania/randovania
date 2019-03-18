import pytest

import randovania.resolver.item_pool.ammo
import randovania.resolver.item_pool.pickup_creator
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import PickupEntry, ConditionalResources
from randovania.layout.major_item_state import MajorItemState


@pytest.mark.parametrize(["percentage"], [
    (False,),
    (True,),
])
def test_create_pickup_for(percentage: bool, echoes_resource_database):
    # Setup
    item_a = echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 10)
    item_b = echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 15)
    item_c = echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 18)
    ammo_a = echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 40)
    ammo_b = echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 42)
    percentage_item = echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 47)

    major_item = MajorItem(
        name="The Item",
        item_category=ItemCategory.MORPH_BALL,
        model_index=1337,
        progression=(10, 15, 18),
        ammo_index=(40, 42),
        required=False,
        original_index=None,
        probability_offset=5,
    )
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(10, 20),
    )

    def _create_resources(item):
        if percentage:
            return (
                (item, 1),
                (ammo_a, 10),
                (ammo_b, 20),
                (percentage_item, 1),
            )
        else:
            return (
                (item, 1),
                (ammo_a, 10),
                (ammo_b, 20),
            )

    # Run
    result = randovania.resolver.item_pool.pickup_creator.create_major_item(major_item, state, percentage,
                                                                            echoes_resource_database)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model_index=1337,
        resources=(
            ConditionalResources(
                name="Dark Visor",
                item=None,
                resources=_create_resources(item_a),
            ),
            ConditionalResources(
                name="Morph Ball",
                item=item_a,
                resources=_create_resources(item_b),
            ),
            ConditionalResources(
                name="Morph Ball Bomb",
                item=item_b,
                resources=_create_resources(item_c),
            ),
        ),
        item_category=ItemCategory.MORPH_BALL,
        probability_offset=5,
    )


@pytest.mark.parametrize(["ammo_quantity"], [
    (0,),
    (10,),
    (15,),
])
def test_create_missile_launcher(ammo_quantity: int, echoes_item_database, echoes_resource_database):
    # Setup
    missile = echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 44)
    percentage_item = echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 47)

    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = randovania.resolver.item_pool.pickup_creator.create_major_item(
        echoes_item_database.major_items["Missile Launcher"],
        state,
        True,
        echoes_resource_database
    )

    # Assert
    assert result == PickupEntry(
        name="Missile Launcher",
        resources=(
            ConditionalResources(
                None, None,
                resources=(
                    (missile, ammo_quantity),
                    (percentage_item, 1),
                )
            ),
        ),
        model_index=24,
        item_category=ItemCategory.MISSILE,
    )
