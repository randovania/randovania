import dataclasses

import pytest

from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


def make(name: str) -> SimpleResourceInfo:
    return SimpleResourceInfo(ord(name[0]), name, name, ResourceType.ITEM)


@pytest.mark.parametrize("items", [
    {},
    {make("A"): 1},
    {make("A"): 1, make("B"): 1},
])
def test_assign_extra_initial_items_to_empty(empty_patches, items):
    # Run
    new_patches = empty_patches.assign_extra_initial_items(items)

    # Assert
    assert new_patches.starting_items == items


@pytest.mark.parametrize(["initial", "new_items", "expected"], [
    ({}, {}, {}),
    ({make("A"): 1}, {}, {make("A"): 1}),
    ({make("A"): 1}, {make("B"): 1}, {make("A"): 1, make("B"): 1}),
    ({make("A"): 1}, {make("A"): 1}, {make("A"): 2}),
])
def test_assign_extra_initial_items_merge(empty_patches, initial, new_items, expected):
    # Setup
    initial_patches = dataclasses.replace(empty_patches, starting_items=initial)

    # Run
    new_patches = initial_patches.assign_extra_initial_items(new_items)

    # Assert
    assert new_patches.starting_items == expected
