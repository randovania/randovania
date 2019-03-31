import pytest

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import PickupIndex, PickupEntry, ConditionalResources, \
    ResourceConversion, SimpleResourceInfo, add_resource_gain_to_current_resources, add_resources_into_another


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


def test_add_resource_gain_to_current_resources_convert():
    # Setup
    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    resource_b = SimpleResourceInfo(2, "B", "B", ResourceType.ITEM)

    pickup = PickupEntry(
        name="P1", model_index=1, item_category=ItemCategory.SUIT,
        resources=(ConditionalResources(None, None, ()),),
        convert_resources=(ResourceConversion(resource_a, resource_b),)
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
