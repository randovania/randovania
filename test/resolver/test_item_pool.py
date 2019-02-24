import pytest

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.major_item import MajorItem, MajorItemCategory
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import PickupEntry, ConditionalResources
from randovania.layout.ammo_state import AmmoState
from randovania.layout.major_item_state import MajorItemState
from randovania.resolver import item_pool


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
        item_category=MajorItemCategory.MORPH_BALL,
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
    result = item_pool._create_pickup_for(major_item, state, percentage, echoes_resource_database)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        resources=_create_resources(item_a),
        model_index=1337,
        conditional_resources=(
            ConditionalResources(
                item=item_a,
                resources=_create_resources(item_b),
            ),
            ConditionalResources(
                item=item_b,
                resources=_create_resources(item_c),
            ),
        ),
        item_category="morph_ball",
        probability_offset=5,
    )


@pytest.mark.parametrize(["per_pickup", "total_pickup", "included"], [
    (1, 5, 0),
    (1, 5, 1),
    (2, 5, 1),
    (50, 1, 0),
])
def test_items_for_ammo_one_item(per_pickup: int, total_pickup: int, included: int):
    # Setup
    item_a = 1

    included_ammo_for_item = {item_a: included}
    previous_pickup_for_item = {}

    maximum = per_pickup * total_pickup + included
    ammo = Ammo("My Ammo", tuple(), (item_a,), maximum)
    state = AmmoState(maximum, 0, total_pickup)

    # Run
    ammo_per_pickup = item_pool._items_for_ammo(ammo, state, included_ammo_for_item, previous_pickup_for_item)

    # Assert
    assert previous_pickup_for_item == {
        item_a: ammo
    }
    assert ammo_per_pickup == [[per_pickup]] * total_pickup


def test_items_for_ammo_one_item_non_divisible():
    # Setup
    item_a = 1

    maximum = 11
    total_pickup = 5

    included_ammo_for_item = {item_a: 0}
    previous_pickup_for_item = {}

    ammo = Ammo("My Ammo", tuple(), (item_a,), maximum)
    state = AmmoState(maximum, 0, total_pickup)

    # Run
    ammo_per_pickup = item_pool._items_for_ammo(ammo, state, included_ammo_for_item, previous_pickup_for_item)

    # Assert
    assert previous_pickup_for_item == {
        item_a: ammo
    }
    assert ammo_per_pickup == [[3]] + [[2]] * (total_pickup - 1)


@pytest.mark.parametrize(["per_pickup", "total_pickup", "included"], [
    (1, 5, 0),
    (1, 5, 1),
    (2, 5, 1),
    (50, 1, 0),
])
def test_items_for_ammo_two_item(per_pickup: int, total_pickup: int, included: int):
    # Setup
    item_a = 1
    item_b = 2

    included_ammo_for_item = {item_a: included, item_b: included}
    previous_pickup_for_item = {}

    maximum = per_pickup * total_pickup + included
    ammo = Ammo("My Ammo", tuple(), (item_a, item_b), maximum)
    state = AmmoState(maximum, 0, total_pickup)

    # Run
    ammo_per_pickup = item_pool._items_for_ammo(ammo, state, included_ammo_for_item, previous_pickup_for_item)

    # Assert
    assert previous_pickup_for_item == {
        item_a: ammo,
        item_b: ammo,
    }
    assert ammo_per_pickup == [[per_pickup, per_pickup]] * total_pickup


def test_items_for_ammo_two_item_diverging_values():
    # Setup
    item_a = 1
    item_b = 2

    total_pickup = 10
    maximum = 200

    included_ammo_for_item = {item_a: 0, item_b: 100}
    previous_pickup_for_item = {}

    ammo = Ammo("My Ammo", tuple(), (item_a, item_b), maximum)
    state = AmmoState(maximum, 0, total_pickup)

    # Run
    ammo_per_pickup = item_pool._items_for_ammo(ammo, state, included_ammo_for_item, previous_pickup_for_item)

    # Assert
    assert previous_pickup_for_item == {
        item_a: ammo,
        item_b: ammo,
    }
    assert ammo_per_pickup == [[20, 10]] * total_pickup
