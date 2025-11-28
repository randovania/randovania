from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import pytest

from randovania.game_description.pickup.pickup_entry import ResourceLock
from randovania.game_description.resources.resource_collection import ResourceCollection

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase


def wrap(db: ResourceDatabase, data):
    if isinstance(data, dict):
        return {db.get_item(key): value for key, value in data.items()}
    else:
        return [(db.get_item(key), value) for key, value in data]


@pytest.mark.parametrize(
    ("a", "b", "result"),
    [
        ({"Ammo": 5}, {"Health": 6}, {"Ammo": 5, "Health": 6}),
        ({"Ammo": 5}, {"Ammo": 6}, {"Ammo": 11}),
    ],
)
def test_add_resources_into_another(blank_game_description, a, b, result):
    blank_resource_db = blank_game_description.resource_database
    a = wrap(blank_resource_db, a)
    b = wrap(blank_resource_db, b)
    result = wrap(blank_resource_db, result)

    ac = ResourceCollection.from_dict(blank_resource_db, a)
    bc = ResourceCollection.from_dict(blank_resource_db, b)

    ac.add_resource_gain(bc.as_resource_gain())

    assert dict(ac.as_resource_gain()) == result


@pytest.mark.parametrize(
    ("resource_gain", "expected"),
    [
        ([], {}),
        ([("Ammo", 5), ("Health", 6)], {"Ammo": 5, "Health": 6}),
        ([("Ammo", 5), ("Ammo", 6)], {"Ammo": 11}),
        ([("Ammo", 5), ("Ammo", -5)], {"Ammo": 0}),
    ],
)
def test_convert_resource_gain_to_current_resources(blank_resource_db, resource_gain, expected):
    # Setup
    resource_gain = wrap(blank_resource_db, resource_gain)
    expected = wrap(blank_resource_db, expected)

    # Run
    result = ResourceCollection.from_resource_gain(blank_resource_db, resource_gain)

    # Assert
    assert dict(result.as_resource_gain()) == expected


def test_add_resource_gain_to_current_resources_convert(blank_resource_db, blank_pickup):
    # Setup
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.item[0]

    pickup = dataclasses.replace(
        blank_pickup,
        progression=(),
        resource_lock=ResourceLock(resource_b, resource_b, resource_a),
        unlocks_resource=True,
    )
    current_resources = ResourceCollection.with_resource_count(blank_resource_db, 0)
    current_resources.add_resource_gain([(resource_a, 5)])

    # Run
    current_resources.add_resource_gain(pickup.resource_gain(current_resources))

    # Assert
    assert dict(current_resources.as_resource_gain()) == {resource_a: 0, resource_b: 5}


def test_remove_resource_exists(echoes_game_description):
    db = echoes_game_description.resource_database
    m = db.get_item("Missile")
    beam = db.get_item("Light")
    col = ResourceCollection.from_dict(
        db,
        {
            m: 10,
            beam: 1,
        },
    )
    col.remove_resource(m)

    assert dict(col.as_resource_gain()) == {beam: 1}


def test_remove_resource_missing(echoes_game_description):
    db = echoes_game_description.resource_database
    m = db.get_item("Missile")
    beam = db.get_item("Light")
    col = ResourceCollection.from_dict(
        db,
        {
            beam: 1,
        },
    )
    col.remove_resource(m)

    assert dict(col.as_resource_gain()) == {beam: 1}


def test_duplicate_independence(blank_resource_db):
    """Test that duplicated ResourceCollections are independent."""
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.get_item("Health")

    original = ResourceCollection.with_resource_count(blank_resource_db, 0)
    original.add_resource_gain([(resource_a, 10), (resource_b, 5)])

    duplicate = original.duplicate()

    # Modify duplicate
    duplicate.add_resource_gain([(resource_a, 5), (resource_b, -2)])

    # Original should be unchanged
    assert original[resource_a] == 10
    assert original[resource_b] == 5

    # Duplicate should have changes
    assert duplicate[resource_a] == 15
    assert duplicate[resource_b] == 3


def test_set_resource(blank_resource_db):
    """Test setting resource quantities directly."""
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.get_item("Health")

    col = ResourceCollection.with_resource_count(blank_resource_db, 0)

    col.set_resource(resource_a, 42)
    col.set_resource(resource_b, 100)

    assert col[resource_a] == 42
    assert col[resource_b] == 100

    # Set to zero
    col.set_resource(resource_a, 0)
    assert col[resource_a] == 0


def test_set_resource_negative_clamped(blank_resource_db):
    """Test that negative values are clamped to 0."""
    resource_a = blank_resource_db.get_item("Ammo")

    col = ResourceCollection.with_resource_count(blank_resource_db, 0)
    col.set_resource(resource_a, -10)

    assert col[resource_a] == 0


def test_has_resource(blank_resource_db):
    """Test has_resource method."""
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.get_item("Health")

    col = ResourceCollection.with_resource_count(blank_resource_db, 0)
    col.add_resource_gain([(resource_a, 5)])

    assert col.has_resource(resource_a)
    assert not col.has_resource(resource_b)


def test_is_resource_set(blank_resource_db):
    """Test is_resource_set method."""
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.get_item("Health")

    col = ResourceCollection.with_resource_count(blank_resource_db, 0)

    assert not col.is_resource_set(resource_a)
    assert not col.is_resource_set(resource_b)

    col.add_resource_gain([(resource_a, 5)])

    assert col.is_resource_set(resource_a)
    assert not col.is_resource_set(resource_b)

    col.add_resource_gain([(resource_b, 0)])

    assert col.is_resource_set(resource_a)
    assert col.is_resource_set(resource_b)


def test_num_resources(blank_resource_db):
    """Test num_resources property."""
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.get_item("Health")

    col = ResourceCollection.with_resource_count(blank_resource_db, 0)

    assert col.num_resources == 0

    col.add_resource_gain([(resource_a, 5)])
    assert col.num_resources == 1

    col.add_resource_gain([(resource_b, 10)])
    assert col.num_resources == 2

    col.remove_resource(resource_a)
    assert col.num_resources == 1


def test_equality(blank_resource_db):
    """Test equality between ResourceCollections."""
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.get_item("Health")

    col1 = ResourceCollection.with_resource_count(blank_resource_db, 0)
    col1.add_resource_gain([(resource_a, 10), (resource_b, 5)])

    col2 = ResourceCollection.with_resource_count(blank_resource_db, 0)
    col2.add_resource_gain([(resource_a, 10), (resource_b, 5)])

    col3 = ResourceCollection.with_resource_count(blank_resource_db, 0)
    col3.add_resource_gain([(resource_a, 10), (resource_b, 6)])

    assert col1 == col2
    assert col1 != col3
    assert hash(col1) == hash(col2)


def test_from_dict_empty(blank_resource_db):
    """Test creating ResourceCollection from empty dict."""
    col = ResourceCollection.from_dict(blank_resource_db, {})

    assert col.num_resources == 0
    assert dict(col.as_resource_gain()) == {}


def test_resource_collection_copy_semantic(blank_resource_db):
    """Test that __copy__ returns a proper duplicate."""
    import copy

    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.get_item("Health")

    original = ResourceCollection.with_resource_count(blank_resource_db, 0)
    original.add_resource_gain([(resource_a, 10), (resource_b, 5)])

    copied = copy.copy(original)

    # Should be equal but independent
    assert copied == original
    assert copied is not original

    # Modify copied
    copied.add_resource_gain([(resource_a, 5)])

    assert copied[resource_a] == 15
    assert original[resource_a] == 10


def test_multiple_add_resource_gain_calls(blank_resource_db):
    """Test multiple sequential add_resource_gain calls."""
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.get_item("Health")

    col = ResourceCollection.with_resource_count(blank_resource_db, 0)

    col.add_resource_gain([(resource_a, 5)])
    col.add_resource_gain([(resource_a, 3)])
    col.add_resource_gain([(resource_b, 10)])
    col.add_resource_gain([(resource_a, -2)])

    assert col[resource_a] == 6
    assert col[resource_b] == 10


def test_resource_gain_ordering(blank_resource_db):
    """Test that as_resource_gain preserves resource information."""
    resource_a = blank_resource_db.get_item("Ammo")
    resource_b = blank_resource_db.get_item("Health")
    resource_c = blank_resource_db.item[0]

    col = ResourceCollection.with_resource_count(blank_resource_db, 0)
    col.add_resource_gain([(resource_a, 5), (resource_b, 10), (resource_c, 3)])

    result = dict(col.as_resource_gain())

    assert result[resource_a] == 5
    assert result[resource_b] == 10
    assert result[resource_c] == 3


def test_get_nonexistent_resource(blank_resource_db):
    """Test getting a resource that was never set returns 0."""
    resource_a = blank_resource_db.get_item("Ammo")

    col = ResourceCollection.with_resource_count(blank_resource_db, 0)

    assert col[resource_a] == 0
    assert col.get(resource_a) == 0


def test_large_resource_quantities(blank_resource_db):
    """Test handling large resource quantities."""
    resource_a = blank_resource_db.get_item("Ammo")

    col = ResourceCollection.with_resource_count(blank_resource_db, 0)
    col.set_resource(resource_a, 1000000)

    assert col[resource_a] == 1000000

    col.add_resource_gain([(resource_a, 500000)])
    assert col[resource_a] == 1500000


def test_resource_collection_with_many_resources(blank_resource_db):
    """Test ResourceCollection with many different resources."""
    col = ResourceCollection.with_resource_count(blank_resource_db, 0)

    # Add many resources
    resources = []
    for i in range(min(50, len(blank_resource_db.item))):
        resource = blank_resource_db.item[i]
        value = i * 10
        resources.append((resource, value))

    col.add_resource_gain(resources)

    # Verify all were added
    for resource, expected_value in resources:
        assert col[resource] == expected_value

    assert col.num_resources == len(resources)


def test_duplicate_preserves_all_state(blank_resource_db):
    """Test that duplicate preserves all state."""
    resource_a = blank_resource_db.get_item("Ammo")

    original = ResourceCollection.with_resource_count(blank_resource_db, 0)
    original.add_resource_gain([(resource_a, 10)])

    duplicate = original.duplicate()

    assert duplicate[resource_a] == 10

    duplicate.add_resource_gain([(resource_a, 10)])
    assert original[resource_a] == 10
