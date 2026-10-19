from __future__ import annotations

import dataclasses
import typing

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import data_reader, data_writer, default_database, integrity_check
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.lib import json_lib
from randovania.lib.enum_lib import iterate_enum

_acceptable_database_errors: dict[RandovaniaGame, bool] = {}


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "game_enum",
    [
        pytest.param(g, marks=[pytest.mark.xfail] if _acceptable_database_errors.get(g, False) else [])
        for g in iterate_enum(RandovaniaGame)
    ],
)
def test_find_database_errors(game_enum: RandovaniaGame):
    # Setup
    game = default_database.game_description_for(game_enum)

    # Run
    errors = integrity_check.find_database_errors(game)

    # Assert
    assert errors == []


def test_invalid_db(test_files_dir, acceptance_check):
    data_path = test_files_dir.joinpath("integrity_check_invalid_db.json")
    sample_data = typing.cast("dict", json_lib.read_path(data_path))
    gd = data_reader.decode_data(sample_data)

    acceptance_check(data_path, data_writer.write_game_description(gd))

    # Run
    errors = integrity_check.find_database_errors(gd)
    errors.extend(integrity_check.check_for_resources_to_use_together(gd, {"BombHoverTrick": ("BombsItem",)}))
    errors.extend(
        integrity_check.check_for_items_to_be_replaced_by_templates(
            gd, {"BombsItem": "something along the lines of 'use bombs'"}
        )
    )

    # Assert
    assert errors == [
        "World/Area 1/Event - Foo has unknown layers {'unknown'}",
        "World/Area 1/Event - Foo is not an Event Node, but naming suggests it is",
        "World/Area 1/Event - Foo has a connection to itself",
        "World/Area 1/Door to Area 2 (Generic) should be named 'Other to Area 2'",
        "World/Area 1/Door to Area 2 (Dock) should be named 'Other to Area 2'",
        "World/Area 1/Door to Area 2 (Dock) has layers ['alternate'], but connected dock "
        "'region World/area Area 2/node Door to Area 1' has layers ['default'].",
        "World/Area 1/Door to Area 2 (Dock) connects to 'region World/area Area 2/node Door to Area 1', "
        "but that dock connects to 'region World/area Area 1/node Door to Area 2 (Generic)' instead.",
        "World/Area 2/Door to Area 1 should be named 'Other to Area 1'",
        "World/Area 2/Door to Area 1 connects to 'region World/area Area 1/node Door to Area 2 (Generic)',"
        " but that dock connects to 'region World/area Area 2/node Generic Node' instead.",
        "World/Area 2 has multiple valid start nodes ['Generic Node', 'Door to Area 1'],"
        " but is not allowed for Metroid Prime 2: Echoes",
        "Lava World/Hot/Door to Nowhere is a Dock Node, but connection 'region World/area Nowhere/node Random Door'"
        " is invalid: 'Unknown name: Nowhere'",
        "Lava World/Hot/Bad Event is an Event Node, but naming doesn't start with 'Event -'",
        "Lava World/Hot/Bad Specific Location Hint points to PickupIndex 2403, which does not exist.",
        "Lava World/Hot/Bad Specific Pickup Hint points to some_invalid_hint_id, which does not exist.",
        "Lava World/Hot/Pickup (Not A Pickup) is not a Pickup Node, but naming matches 'Pickup (...)'",
        "Lava World/Hot/Bad Pickup shares the hint feature 'Redundant Feature' with the area it's in.",
        "Lava World/Hot/Bad Pickup is a Pickup Node, but naming doesn't match 'Pickup (...)'",
        (
            "Lava World/Hot's pickups all share the hint feature 'Un-normalized Feature'. "
            "Add feature to the area and remove from the pickups."
        ),
        "Unknown strongly connected component detected containing 1 nodes:\n['World/Area 1/Event - Foo']",
        "Unknown strongly connected component detected containing 1 nodes:\n['World/Area 1/Door to Area 2 (Generic)']",
        "Unknown strongly connected component detected containing 1 nodes:\n['World/Area 2/Door to Area 1']",
        "Unknown strongly connected component detected containing 1 nodes:\n['World/Area 1/Door to Area 2 (Dock)']",
        (
            "Unknown strongly connected component detected containing 2 nodes:\n"
            "['Grass World/Plains/Hut', 'Grass World/Plains/Windmill']"
        ),
        "Checking A: Loop detected: ['A', 'B', 'A']",
        "Checking B: Loop detected: ['B', 'A', 'B']",
        "Lava World/Hot/Pickup (Duplicate Id) has PickupIndex 5, but it was already used in Lava World/Hot/Bad Pickup",
        "Discord media linked in Lava World/Hot/Door to World (1) -> Bad Connection Comment.",
        "YouTube Playlist linked in Lava World/Hot/Bad Connection Comment -> Door to World (1).",
        'Grass World/Plains/Windmill -> Grass World/Plains/Hut contains "BombHoverTrick" but not "(\'BombsItem\',)"',
        (
            'Grass World/Plains/Windmill -> Grass World/Plains/Hut is using the resource "BombsItem" directly '
            "than using the template \"something along the lines of 'use bombs'\"."
        ),
    ]


def test_find_grants_on_collect_errors(blank_game_description):
    # Setup
    db = blank_game_description.resource_database
    region_list = blank_game_description.region_list
    event_node = region_list.node_by_identifier(NodeIdentifier.create("Intro", "Boss Arena", "Event - Boss"))
    pickup_node = region_list.node_by_identifier(NodeIdentifier.create("Intro", "Boss Arena", "Pickup (Free Loot)"))
    ammo = db.get_item("Ammo")

    bad_event = dataclasses.replace(
        event_node,
        grants_on_collect=((ammo, 5), (ammo, 1), (event_node.event, 1)),
    )
    bad_pickup = dataclasses.replace(
        pickup_node,
        grants_on_collect=((db.get_item("Weapon"), 2), (db.get_event("KeySwitch1"), 0), (db.get_trick("Combat"), 1)),
    )
    good_pickup = dataclasses.replace(pickup_node, grants_on_collect=((ammo, 500), (db.get_event("KeySwitch1"), 1)))

    # Run
    event_errors = list(integrity_check.find_grants_on_collect_errors(bad_event))
    pickup_errors = list(integrity_check.find_grants_on_collect_errors(bad_pickup))
    good_errors = list(integrity_check.find_grants_on_collect_errors(good_pickup))

    # Assert
    assert event_errors == [
        "Event - Boss grants Missile more than once",
        "Event - Boss grants its own event First Boss Killed",
    ]
    assert pickup_errors == [
        "Pickup (Free Loot) grants 2 of Weapon, more than its capacity of 1",
        "Pickup (Free Loot) grants 0 of Key Switch 1, which must be positive",
        "Pickup (Free Loot) grants Combat, which is neither an item nor an event",
    ]
    assert good_errors == []


def test_find_node_errors_includes_grants_on_collect(blank_game_description):
    # Setup
    region_list = blank_game_description.region_list
    node = region_list.node_by_identifier(NodeIdentifier.create("Intro", "Boss Arena", "Pickup (Free Loot)"))
    node = dataclasses.replace(
        node, grants_on_collect=((blank_game_description.resource_database.get_item("Ammo"), 0),)
    )

    # Run
    errors = list(integrity_check.find_node_errors(blank_game_description, node))

    # Assert
    assert "Pickup (Free Loot) grants 0 of Missile, which must be positive" in errors
