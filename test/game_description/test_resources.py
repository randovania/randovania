import dataclasses

import pytest

from randovania.game_description.resources.pickup_entry import ResourceLock
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType


def wrap(db: ResourceDatabase, data):
    if isinstance(data, dict):
        return {
            db.get_item(key): value
            for key, value in data.items()
        }
    else:
        return [
            (db.get_item(key), value)
            for key, value in data
        ]


@pytest.mark.parametrize(["a", "b", "result"], [
    ({"Ammo": 5}, {"Health": 6}, {"Ammo": 5, "Health": 6}),
    ({"Ammo": 5}, {"Ammo": 6}, {"Ammo": 11}),
])
def test_add_resources_into_another(blank_resource_db, a, b, result):
    a = wrap(blank_resource_db, a)
    b = wrap(blank_resource_db, b)
    result = wrap(blank_resource_db, result)

    ac = ResourceCollection.from_dict(blank_resource_db, a)
    bc = ResourceCollection.from_dict(blank_resource_db, b)

    ac.add_resource_gain(bc.as_resource_gain())

    assert dict(ac.as_resource_gain()) == result


def test_pickup_index_equality():
    assert PickupIndex(1) == PickupIndex(1)


def test_pickup_index_has():
    d = {PickupIndex(1): True}
    assert PickupIndex(1) in d


def test_add_resource_gain_to_current_resources_convert(blank_resource_db, blank_pickup):
    # Setup
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.item[0]

    pickup = dataclasses.replace(
        blank_pickup,
        progression=(), resource_lock=ResourceLock(resource_b, resource_b, resource_a), unlocks_resource=True,
    )
    current_resources = ResourceCollection()
    current_resources.add_resource_gain([(resource_a, 5)])

    # Run
    current_resources.add_resource_gain(pickup.resource_gain(current_resources))

    # Assert
    assert dict(current_resources.as_resource_gain()) == {
        resource_a: 0,
        resource_b: 5
    }


@pytest.mark.parametrize(["resource_gain", "expected"], [
    ([], {}),
    ([("Ammo", 5), ("Health", 6)], {"Ammo": 5, "Health": 6}),
    ([("Ammo", 5), ("Ammo", 6)], {"Ammo": 11}),
    ([("Ammo", 5), ("Ammo", -5)], {"Ammo": 0}),
])
def test_convert_resource_gain_to_current_resources(blank_resource_db, resource_gain, expected):
    # Setup
    db = blank_resource_db
    resource_gain = wrap(db, resource_gain)
    expected = wrap(db, expected)

    # Run
    result = ResourceCollection.from_resource_gain(db, resource_gain)

    # Assert
    assert dict(result.as_resource_gain()) == expected


def test_resource_type_from_index():
    # Run
    result = ResourceType.from_index(0)

    # Assert
    assert result == ResourceType.ITEM
