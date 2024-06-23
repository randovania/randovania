from __future__ import annotations

import pytest

from randovania.game_description import data_reader, default_database, integrity_check
from randovania.games.game import RandovaniaGame
from randovania.lib.enum_lib import iterate_enum

_acceptable_database_errors: dict[RandovaniaGame, bool] = {}


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


def test_invalid_db():
    trivial_req = {"type": "and", "data": {"comment": "", "items": []}}
    sample_data = {
        "schema_version": 14,
        "game": "prime2",
        "resource_database": {
            "items": {"LightAmmo": {"long_name": "Light Ammo", "max_capacity": 1, "extra": {"item_id": 46}}},
            "events": {
                "Boss": {"long_name": "First Boss Killed", "extra": {}},
            },
            "tricks": {},
            "damage": {},
            "versions": {},
            "misc": {},
            "requirement_template": {
                "A": {
                    "type": "and",
                    "data": {
                        "comment": None,
                        "items": [
                            {
                                "type": "resource",
                                "data": {
                                    "type": "items",
                                    "name": "LightAmmo",
                                    "amount": 5,
                                    "negate": False,
                                },
                            },
                            {"type": "template", "data": "B"},
                        ],
                    },
                },
                "B": {"type": "template", "data": "A"},
            },
            "damage_reductions": [],
            "energy_tank_item_index": "LightAmmo",
            "item_percentage_index": "Power",
            "multiworld_magic_item_index": "Power",
        },
        "layers": ["default"],
        "starting_location": {"world_name": "World", "area_name": "Area 2", "node_name": "Generic Node"},
        "initial_states": {"Default": []},
        "minimal_logic": None,
        "victory_condition": {"type": "and", "data": {"comment": None, "items": []}},
        "dock_weakness_database": {
            "types": {
                "door": {
                    "name": "Door",
                    "extra": {},
                    "items": {
                        "Normal Door": {
                            "extra": {},
                            "requirement": {"type": "and", "data": {"comment": None, "items": []}},
                            "lock": None,
                        }
                    },
                    "dock_rando": {"unlocked": None, "locked": None, "change_from": [], "change_to": []},
                },
                "portal": {
                    "name": "Portal",
                    "extra": {},
                    "items": {},
                    "dock_rando": {"unlocked": None, "locked": None, "change_from": [], "change_to": []},
                },
                "morph_ball": {
                    "name": "Morph Ball Door",
                    "extra": {},
                    "items": {},
                    "dock_rando": {"unlocked": None, "locked": None, "change_from": [], "change_to": []},
                },
                "other": {
                    "name": "Other",
                    "extra": {},
                    "items": {
                        "Open Passage": {
                            "extra": {},
                            "requirement": {"type": "and", "data": {"comment": None, "items": []}},
                            "lock": None,
                        },
                        "Not Determined": {
                            "extra": {},
                            "requirement": {"type": "or", "data": {"comment": None, "items": []}},
                            "lock": None,
                        },
                    },
                    "dock_rando": {"unlocked": None, "locked": None, "change_from": [], "change_to": []},
                },
            },
            "default_weakness": {"type": "other", "name": "Not Determined"},
            "dock_rando": {
                "enable_one_way": False,
                "force_change_two_way": False,
                "resolver_attempts": 125,
                "to_shuffle_proportion": 1.0,
            },
        },
        "worlds": [
            {
                "name": "World",
                "extra": {},
                "areas": {
                    "Area 1": {
                        "default_node": None,
                        "extra": {},
                        "nodes": {
                            "Event - Foo": {
                                "node_type": "generic",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default", "unknown"],
                                "extra": {},
                                "valid_starting_location": False,
                                "connections": {"Event - Foo": trivial_req},
                            },
                            "Door to Area 2 (Generic)": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "dock_type": "other",
                                "default_connection": {
                                    "world_name": "World",
                                    "area_name": "Area 2",
                                    "node_name": "Generic Node",
                                },
                                "default_dock_weakness": "Open Passage",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {},
                            },
                            "Door to Area 2 (Dock)": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "dock_type": "other",
                                "default_connection": {
                                    "world_name": "World",
                                    "area_name": "Area 2",
                                    "node_name": "Door to Area 1",
                                },
                                "default_dock_weakness": "Open Passage",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {},
                            },
                        },
                    },
                    "Area 2": {
                        "default_node": "Generic Node",
                        "extra": {},
                        "nodes": {
                            "Generic Node": {
                                "node_type": "generic",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": True,
                                "connections": {},
                            },
                            "Door to Area 1": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": True,
                                "dock_type": "other",
                                "default_connection": {
                                    "world_name": "World",
                                    "area_name": "Area 1",
                                    "node_name": "Door to Area 2 (Generic)",
                                },
                                "default_dock_weakness": "Open Passage",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {},
                            },
                        },
                    },
                    "Warm": {
                        "default_node": None,
                        "extra": {},
                        "nodes": {
                            "Door to Hot": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "dock_type": "door",
                                "default_connection": {
                                    "world_name": "Lava World",
                                    "area_name": "Hot",
                                    "node_name": "Door to World (1)",
                                },
                                "default_dock_weakness": "Normal Door",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {},
                            },
                            "Door to Lava World": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "dock_type": "door",
                                "default_connection": {
                                    "world_name": "Lava World",
                                    "area_name": "Hot",
                                    "node_name": "Door to World (2)",
                                },
                                "default_dock_weakness": "Normal Door",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {},
                            },
                        },
                    },
                },
            },
            {
                "name": "Lava World",
                "extra": {},
                "areas": {
                    "Hot": {
                        "default_node": None,
                        "extra": {},
                        "nodes": {
                            "Door to World (1)": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {"different_strongly_connected_component": True},
                                "valid_starting_location": False,
                                "dock_type": "door",
                                "default_connection": {
                                    "world_name": "World",
                                    "area_name": "Warm",
                                    "node_name": "Door to Hot",
                                },
                                "default_dock_weakness": "Normal Door",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {
                                    "Door to World (2)": trivial_req,
                                    "Bad Event": trivial_req,
                                    "Pickup (Not A Pickup)": trivial_req,
                                    "Bad Pickup": trivial_req,
                                    "Door to Nowhere": trivial_req,
                                    "Pickup (Duplicate Id)": trivial_req,
                                },
                            },
                            "Door to World (2)": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "dock_type": "door",
                                "default_connection": {
                                    "world_name": "World",
                                    "area_name": "Warm",
                                    "node_name": "Door to Lava World",
                                },
                                "default_dock_weakness": "Normal Door",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {"Door to World (1)": trivial_req},
                            },
                            "Door to Nowhere": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {"different_strongly_connected_component": True},
                                "valid_starting_location": False,
                                "dock_type": "door",
                                "default_connection": {
                                    "world_name": "World",
                                    "area_name": "Nowhere",
                                    "node_name": "Random Door",
                                },
                                "default_dock_weakness": "Normal Door",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {"Door to World (1)": trivial_req},
                            },
                            "Bad Event": {
                                "node_type": "event",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "event_name": "Boss",
                                "connections": {"Door to World (1)": trivial_req},
                            },
                            "Pickup (Not A Pickup)": {
                                "node_type": "generic",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "connections": {"Door to World (1)": trivial_req},
                            },
                            "Bad Pickup": {
                                "node_type": "pickup",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "pickup_index": 5,
                                "major_location": False,
                                "connections": {"Door to World (1)": trivial_req},
                            },
                            "Pickup (Duplicate Id)": {
                                "node_type": "pickup",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "pickup_index": 5,
                                "major_location": False,
                                "connections": {"Door to World (1)": trivial_req},
                            },
                        },
                    }
                },
            },
        ],
    }
    gd = data_reader.decode_data(sample_data)

    # Run
    errors = integrity_check.find_database_errors(gd)

    # Assert
    assert errors == [
        "World/Area 1/Event - Foo has unknown layers {'unknown'}",
        "World/Area 1/Event - Foo is not an Event Node, but naming suggests it is",
        "World/Area 1/Event - Foo has a connection to itself",
        "World/Area 1/Door to Area 2 (Generic) should be named 'Other to Area 2'",
        "World/Area 1/Door to Area 2 (Dock) should be named 'Other to Area 2'",
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
        "Lava World/Hot/Pickup (Not A Pickup) is not a Pickup Node, but naming matches 'Pickup (...)'",
        "Lava World/Hot/Bad Pickup is a Pickup Node, but naming doesn't match 'Pickup (...)'",
        "Unknown strongly connected component detected containing 1 nodes:\n['World/Area 1/Event - Foo']",
        "Unknown strongly connected component detected containing 1 nodes:\n"
        "['World/Area 1/Door to Area 2 (Generic)']",
        "Unknown strongly connected component detected containing 1 nodes:\n['World/Area 2/Door to Area 1']",
        "Unknown strongly connected component detected containing 1 nodes:\n['World/Area 1/Door to Area 2 (Dock)']",
        "Checking A: Loop detected: ['A', 'B', 'A']",
        "Checking B: Loop detected: ['B', 'A', 'B']",
        "Lava World/Hot/Pickup (Duplicate Id) has PickupIndex 5, but it was already used in Lava World/Hot/Bad Pickup",
    ]
