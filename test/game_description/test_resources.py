from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.node import NodeContext
from randovania.game_description.game_description import calculate_interesting_resources
from randovania.game_description.pickup.pickup_entry import ResourceLock
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType

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
        progression=(),
        resource_lock=ResourceLock(resource_b, resource_b, resource_a),
        unlocks_resource=True,
    )
    current_resources = ResourceCollection()
    current_resources.add_resource_gain([(resource_a, 5)])

    # Run
    current_resources.add_resource_gain(pickup.resource_gain(current_resources))

    # Assert
    assert dict(current_resources.as_resource_gain()) == {resource_a: 0, resource_b: 5}


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


def test_resources_for_unsatisfied_damage_as_interesting(echoes_resource_database):
    db = echoes_resource_database
    req = ResourceRequirement.create(
        db.get_by_type_and_index(ResourceType.DAMAGE, "DarkWorld1"),
        100,
        False,
    )
    context = NodeContext(
        MagicMock(),
        ResourceCollection(),
        db,
        MagicMock(),
    )
    interesting_resources = calculate_interesting_resources(frozenset([RequirementList([req])]), context, 99)
    d_suit = db.get_item_by_name("Dark Suit")
    l_suit = db.get_item_by_name("Light Suit")
    e_tank = db.get_item_by_name("Energy Tank")

    assert d_suit in interesting_resources
    assert l_suit in interesting_resources
    assert e_tank in interesting_resources


def test_resources_for_satisfied_damage_as_interesting(echoes_resource_database):
    db = echoes_resource_database
    req = ResourceRequirement.create(
        db.get_by_type_and_index(ResourceType.DAMAGE, "DarkWorld1"),
        5,
        False,
    )

    context = NodeContext(
        MagicMock(),
        ResourceCollection(),
        db,
        MagicMock(),
    )
    interesting_resources = calculate_interesting_resources(frozenset([RequirementList([req])]), context, 99)
    d_suit = db.get_item_by_name("Dark Suit")
    l_suit = db.get_item_by_name("Light Suit")
    e_tank = db.get_item_by_name("Energy Tank")

    assert d_suit in interesting_resources
    assert l_suit in interesting_resources
    assert e_tank in interesting_resources
