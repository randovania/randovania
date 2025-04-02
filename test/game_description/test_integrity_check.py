from __future__ import annotations

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import data_reader, default_database, integrity_check
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
        "schema_version": 30,
        "game": "prime2",
        "resource_database": {
            "items": {
                "LightAmmo": {"long_name": "Light Ammo", "max_capacity": 1, "extra": {"item_id": 46}},
                "BombsItem": {"long_name": "Bombs", "max_capacity": 1, "extra": {"item_id": 47}},
            },
            "events": {"Boss": {"long_name": "First Boss Killed", "extra": {}}},
            "tricks": {
                "BombHoverTrick": {
                    "long_name": "Bomb Hovering",
                    "description": "Trick that allows you to hover with bombs",
                    "require_documentation_above": 0,
                    "extra": {},
                }
            },
            "damage": {},
            "versions": {},
            "misc": {},
            "requirement_template": {
                "A": {
                    "display_name": "A",
                    "requirement": {
                        "type": "and",
                        "data": {
                            "comment": None,
                            "items": [
                                {
                                    "type": "resource",
                                    "data": {"type": "items", "name": "LightAmmo", "amount": 5, "negate": False},
                                },
                                {"type": "template", "data": "B"},
                            ],
                        },
                    },
                },
                "B": {"display_name": "B", "requirement": {"type": "template", "data": "A"}},
                "Use Bombs": {
                    "display_name": "Use Bombs",
                    "requirement": {
                        "type": "resource",
                        "data": {"type": "items", "name": "BombsItem", "amount": 1, "negate": False},
                    },
                },
            },
            "damage_reductions": [],
            "energy_tank_item_index": "LightAmmo",
        },
        "layers": ["default"],
        "starting_location": {"region": "World", "area": "Area 2", "node": "Generic Node"},
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
                    "dock_rando": None,
                },
                "portal": {"name": "Portal", "extra": {"ignore_for_hints": True}, "items": {}, "dock_rando": None},
                "morph_ball": {"name": "Morph Ball Door", "extra": {}, "items": {}, "dock_rando": None},
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
                    "dock_rando": None,
                },
                "teleporter": {
                    "name": "Teleporter",
                    "extra": {"is_teleporter": True, "ignore_for_hints": True},
                    "items": {
                        "Teleporter": {
                            "extra": {},
                            "requirement": {"type": "and", "data": {"comment": None, "items": []}},
                            "lock": None,
                        }
                    },
                    "dock_rando": None,
                },
            },
            "default_weakness": {"type": "other", "name": "Not Determined"},
            "dock_rando": {"force_change_two_way": False, "resolver_attempts": 125, "to_shuffle_proportion": 1.0},
        },
        "hint_feature_database": {
            "redundant": {"long_name": "Redundant Feature", "hint_details": ["", ""]},
            "unnormalized": {"long_name": "Un-normalized Feature", "hint_details": ["", ""]},
        },
        "used_trick_levels": {"BombHoverTrick": [1]},
        "flatten_to_set_on_patch": False,
        "regions": [
            {
                "name": "World",
                "extra": {},
                "areas": {
                    "Area 1": {
                        "default_node": None,
                        "hint_features": [],
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
                                "default_connection": {"region": "World", "area": "Area 2", "node": "Generic Node"},
                                "default_dock_weakness": "Open Passage",
                                "exclude_from_dock_rando": False,
                                "incompatible_dock_weaknesses": [],
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "ui_custom_name": None,
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
                                "default_connection": {"region": "World", "area": "Area 2", "node": "Door to Area 1"},
                                "default_dock_weakness": "Open Passage",
                                "exclude_from_dock_rando": False,
                                "incompatible_dock_weaknesses": [],
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "ui_custom_name": None,
                                "connections": {},
                            },
                        },
                    },
                    "Area 2": {
                        "default_node": "Generic Node",
                        "hint_features": [],
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
                                    "region": "World",
                                    "area": "Area 1",
                                    "node": "Door to Area 2 (Generic)",
                                },
                                "default_dock_weakness": "Open Passage",
                                "exclude_from_dock_rando": False,
                                "incompatible_dock_weaknesses": [],
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "ui_custom_name": None,
                                "connections": {},
                            },
                        },
                    },
                    "Warm": {
                        "default_node": None,
                        "hint_features": [],
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
                                    "region": "Lava World",
                                    "area": "Hot",
                                    "node": "Door to World (1)",
                                },
                                "default_dock_weakness": "Normal Door",
                                "exclude_from_dock_rando": False,
                                "incompatible_dock_weaknesses": [],
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "ui_custom_name": None,
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
                                    "region": "Lava World",
                                    "area": "Hot",
                                    "node": "Door to World (2)",
                                },
                                "default_dock_weakness": "Normal Door",
                                "exclude_from_dock_rando": False,
                                "incompatible_dock_weaknesses": [],
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "ui_custom_name": None,
                                "connections": {},
                            },
                        },
                    },
                },
            },
            {
                "name": "Grass World",
                "extra": {},
                "areas": {
                    "Plains": {
                        "default_node": None,
                        "hint_features": [],
                        "extra": {},
                        "nodes": {
                            "Hut": {
                                "node_type": "generic",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": True,
                                "connections": {
                                    "Windmill": {
                                        "type": "or",
                                        "data": {
                                            "comment": None,
                                            "items": [
                                                {
                                                    "type": "resource",
                                                    "data": {
                                                        "type": "items",
                                                        "name": "BombsItem",
                                                        "amount": 0,
                                                        "negate": False,
                                                    },
                                                },
                                                {
                                                    "type": "resource",
                                                    "data": {
                                                        "type": "items",
                                                        "name": "BombsItem",
                                                        "amount": 1,
                                                        "negate": True,
                                                    },
                                                },
                                                {
                                                    "type": "resource",
                                                    "data": {
                                                        "type": "items",
                                                        "name": "BombsItem",
                                                        "amount": 2,
                                                        "negate": False,
                                                    },
                                                },
                                            ],
                                        },
                                    }
                                },
                            },
                            "Windmill": {
                                "node_type": "generic",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": ["default"],
                                "extra": {},
                                "valid_starting_location": False,
                                "connections": {
                                    "Hut": {
                                        "type": "or",
                                        "data": {
                                            "comment": None,
                                            "items": [
                                                {
                                                    "type": "resource",
                                                    "data": {
                                                        "type": "tricks",
                                                        "name": "BombHoverTrick",
                                                        "amount": 1,
                                                        "negate": False,
                                                    },
                                                },
                                                {
                                                    "type": "resource",
                                                    "data": {
                                                        "type": "items",
                                                        "name": "BombsItem",
                                                        "amount": 1,
                                                        "negate": False,
                                                    },
                                                },
                                            ],
                                        },
                                    }
                                },
                            },
                        },
                    }
                },
            },
            {
                "name": "Lava World",
                "extra": {},
                "areas": {
                    "Hot": {
                        "default_node": None,
                        "hint_features": ["redundant"],
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
                                "default_connection": {"region": "World", "area": "Warm", "node": "Door to Hot"},
                                "default_dock_weakness": "Normal Door",
                                "exclude_from_dock_rando": False,
                                "incompatible_dock_weaknesses": [],
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "ui_custom_name": None,
                                "connections": {
                                    "Door to World (2)": trivial_req,
                                    "Door to Nowhere": trivial_req,
                                    "Bad Event": trivial_req,
                                    "Pickup (Not A Pickup)": trivial_req,
                                    "Bad Pickup": trivial_req,
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
                                "default_connection": {"region": "World", "area": "Warm", "node": "Door to Lava World"},
                                "default_dock_weakness": "Normal Door",
                                "exclude_from_dock_rando": False,
                                "incompatible_dock_weaknesses": [],
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "ui_custom_name": None,
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
                                "default_connection": {"region": "World", "area": "Nowhere", "node": "Random Door"},
                                "default_dock_weakness": "Normal Door",
                                "exclude_from_dock_rando": False,
                                "incompatible_dock_weaknesses": [],
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "ui_custom_name": None,
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
                                "location_category": "minor",
                                "custom_index_group": None,
                                "hint_features": ["redundant", "unnormalized"],
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
                                "location_category": "minor",
                                "custom_index_group": None,
                                "hint_features": ["unnormalized"],
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
        'Grass World/Plains/Windmill -> Grass World/Plains/Hut contains "BombHoverTrick" but not "(\'BombsItem\',)"',
        (
            'Grass World/Plains/Windmill -> Grass World/Plains/Hut is using the resource "BombsItem" directly '
            "than using the template \"something along the lines of 'use bombs'\"."
        ),
    ]
