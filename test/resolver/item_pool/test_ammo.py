import pytest

import randovania.generator.item_pool.ammo
import randovania.generator.item_pool.pickup_creator
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.layout.base.ammo_state import AmmoState


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
    ammo = Ammo("My Ammo", model_name="Model", maximum=maximum, items=(item_a,), broad_category=ItemCategory.BEAM_RELATED)
    state = AmmoState(0, total_pickup)
    maximum_ammo = {item_a: maximum}

    # Run
    ammo_per_pickup = randovania.generator.item_pool.ammo.items_for_ammo(ammo, state, included_ammo_for_item,
                                                                         previous_pickup_for_item, maximum_ammo)

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

    ammo = Ammo("My Ammo", model_name="Model", maximum=maximum, items=(item_a,),
                broad_category=ItemCategory.BEAM_RELATED)
    state = AmmoState(0, total_pickup)
    maximum_ammo = {item_a: maximum}

    # Run
    ammo_per_pickup = randovania.generator.item_pool.ammo.items_for_ammo(ammo, state, included_ammo_for_item,
                                                                         previous_pickup_for_item, maximum_ammo)

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
    ammo = Ammo("My Ammo", model_name="Model", maximum=maximum, items=(item_a, item_b),
                broad_category=ItemCategory.BEAM_RELATED)
    state = AmmoState(0, total_pickup)
    maximum_ammo = {item_a: maximum, item_b: maximum}

    # Run
    ammo_per_pickup = randovania.generator.item_pool.ammo.items_for_ammo(ammo, state, included_ammo_for_item,
                                                                         previous_pickup_for_item, maximum_ammo)

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

    ammo = Ammo("My Ammo", model_name="Model", maximum=maximum, items=(item_a, item_b),
                broad_category=ItemCategory.BEAM_RELATED)
    state = AmmoState(0, total_pickup)
    maximum_ammo = {item_a: maximum, item_b: maximum}

    # Run
    ammo_per_pickup = randovania.generator.item_pool.ammo.items_for_ammo(ammo, state, included_ammo_for_item,
                                                                         previous_pickup_for_item, maximum_ammo)

    # Assert
    assert previous_pickup_for_item == {
        item_a: ammo,
        item_b: ammo,
    }
    assert ammo_per_pickup == [[20, 10]] * total_pickup
