import dataclasses

import pytest

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


def make(name: str) -> SimpleResourceInfo:
    return SimpleResourceInfo(name, name, ResourceType.ITEM)


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


@pytest.mark.parametrize("items", [
    [],
    [("Weapon", 1)],
    [("Weapon", 1), ("Ammo", 1)],
])
def test_assign_extra_initial_items_to_empty(empty_patches, items):
    db = empty_patches.game.resource_database
    items = wrap(db, items)

    # Run
    new_patches = empty_patches.assign_extra_initial_items(items)

    # Assert
    assert new_patches.starting_items == ResourceCollection.from_resource_gain(db, items)


@pytest.mark.parametrize(["initial", "new_items", "expected"], [
    ({}, {}, {}),
    ({"Weapon": 1}, {}, {"Weapon": 1}),
    ({"Weapon": 1}, {"Ammo": 1}, {"Weapon": 1, "Ammo": 1}),
    ({"Weapon": 1}, {"Weapon": 1}, {"Weapon": 2}),
])
def test_assign_extra_initial_items_merge(empty_patches, initial, new_items, expected):
    db = empty_patches.game.resource_database
    initial = wrap(db, initial)
    new_items = wrap(db, new_items)
    expected = wrap(db, expected)

    # Setup
    initial_patches = dataclasses.replace(empty_patches, starting_items=ResourceCollection.from_dict(db, initial))

    # Run
    new_patches = initial_patches.assign_extra_initial_items(
        ResourceCollection.from_dict(db, new_items).as_resource_gain(),
    )

    # Assert
    assert new_patches.starting_items == ResourceCollection.from_dict(db, expected)
