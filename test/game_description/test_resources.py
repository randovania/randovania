import dataclasses

import pytest

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import ConditionalResources, ResourceConversion, PickupEntry, \
    ResourceLock
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import add_resource_gain_to_current_resources, \
    add_resources_into_another, convert_resource_gain_to_current_resources


@pytest.mark.parametrize(["a", "b", "result"], [
    ({"a": 5}, {"b": 6}, {"a": 5, "b": 6}),
    ({"a": 5}, {"a": 6}, {"a": 11}),
])
def test_add_resources_into_another(a, b, result):
    add_resources_into_another(a, b)
    assert a == result


def test_pickup_index_equality():
    assert PickupIndex(1) == PickupIndex(1)


def test_pickup_index_has():
    d = {PickupIndex(1): True}
    assert PickupIndex(1) in d


def test_add_resource_gain_to_current_resources_convert(blank_pickup):
    # Setup
    resource_a = ItemResourceInfo(1, "A", "A", 10, None)
    resource_b = ItemResourceInfo(2, "B", "B", 10, None)

    pickup = dataclasses.replace(
        blank_pickup,
        progression=(), resource_lock=ResourceLock(resource_b, resource_b, resource_a), unlocks_resource=True,
    )
    current_resources = {
        resource_a: 5
    }

    # Run
    add_resource_gain_to_current_resources(pickup.resource_gain(current_resources), current_resources)

    # Assert
    assert current_resources == {
        resource_a: 0,
        resource_b: 5
    }


@pytest.mark.parametrize(["resource_gain", "expected"], [
    ([], {}),
    ([("a", 5), ("b", 6)], {"a": 5, "b": 6}),
    ([("a", 5), ("a", 6)], {"a": 11}),
    ([("a", 5), ("a", -5)], {"a": 0}),
])
def test_convert_resource_gain_to_current_resources(resource_gain, expected):
    # Setup
    # Run
    result = convert_resource_gain_to_current_resources(resource_gain)

    # Assert
    assert result == expected
