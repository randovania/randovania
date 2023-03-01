import pytest

from randovania.game_description import integrity_check, data_reader, default_database
from randovania.games.game import RandovaniaGame
from randovania.lib.enum_lib import iterate_enum

_acceptable_database_errors = {
    RandovaniaGame.METROID_DREAD: False,
}


@pytest.mark.parametrize("game_enum", [
    pytest.param(g, marks=pytest.mark.xfail if _acceptable_database_errors.get(
        g, not g.data.development_state.is_stable) else [])
    for g in iterate_enum(RandovaniaGame)
])
def test_find_database_errors(game_enum: RandovaniaGame):
    # Setup
    game = default_database.game_description_for(game_enum)

    # Run
    errors = integrity_check.find_database_errors(game)

    # Assert
    assert errors == []


def test_invalid_db():
    sample_data = {
        "schema_version": 14,
        "game": "prime2",
        "resource_database": {
            "items": {},
            "events": {},
            "tricks": {},
            "damage": {},
            "versions": {},
            "misc": {},
            "requirement_template": {},
            "damage_reductions": [],
            "energy_tank_item_index": "Power",
            "item_percentage_index": "Power",
            "multiworld_magic_item_index": "Power"
        },
        "layers": [
            "default"
        ],
        "starting_location": {
            "world_name": "World",
            "area_name": "Area 2",
            "node_name": "Generic Node"
        },
        "initial_states": {
            "Default": []
        },
        "minimal_logic": None,
        "victory_condition": {
            "type": "and",
            "data": {
                "comment": None,
                "items": []
            }
        },
        "dock_weakness_database": {
            "types": {
                "door": {
                    "name": "Door",
                    "extra": {},
                    "items": {},
                    "dock_rando": {
                        "unlocked": None,
                        "locked": None,
                        "change_from": [],
                        "change_to": []
                    }
                },
                "portal": {
                    "name": "Portal",
                    "extra": {},
                    "items": {},
                    "dock_rando": {
                        "unlocked": None,
                        "locked": None,
                        "change_from": [],
                        "change_to": []
                    }
                },
                "morph_ball": {
                    "name": "Morph Ball Door",
                    "extra": {},
                    "items": {},
                    "dock_rando": {
                        "unlocked": None,
                        "locked": None,
                        "change_from": [],
                        "change_to": []
                    }
                },
                "other": {
                    "name": "Other",
                    "extra": {},
                    "items": {
                        "Open Passage": {
                            "extra": {},
                            "requirement": {
                                "type": "and",
                                "data": {
                                    "comment": None,
                                    "items": []
                                }
                            },
                            "lock": None
                        },
                        "Not Determined": {
                            "extra": {},
                            "requirement": {
                                "type": "or",
                                "data": {
                                    "comment": None,
                                    "items": []
                                }
                            },
                            "lock": None
                        }
                    },
                    "dock_rando": {
                        "unlocked": None,
                        "locked": None,
                        "change_from": [],
                        "change_to": []
                    }
                }
            },
            "default_weakness": {
                "type": "other",
                "name": "Not Determined"
            },
            "dock_rando": {
                "enable_one_way": False,
                "force_change_two_way": False,
                "resolver_attempts": 125,
                "to_shuffle_proportion": 1.0
            }
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
                                "layers": [
                                    "default"
                                ],
                                "extra": {},
                                "valid_starting_location": False,
                                "connections": {
                                    "Event - Foo": {
                                        "type": "and",
                                        "data": {
                                            "comment": "",
                                            "items": []
                                        }
                                    }
                                }
                            },
                            "Door to Area 2 (Generic)": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": [
                                    "default"
                                ],
                                "extra": {},
                                "valid_starting_location": False,
                                "dock_type": "other",
                                "default_connection": {
                                    "world_name": "World",
                                    "area_name": "Area 2",
                                    "node_name": "Generic Node"
                                },
                                "default_dock_weakness": "Open Passage",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {}
                            },
                            "Door to Area 2 (Dock)": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": [
                                    "default"
                                ],
                                "extra": {},
                                "valid_starting_location": False,
                                "dock_type": "other",
                                "default_connection": {
                                    "world_name": "World",
                                    "area_name": "Area 2",
                                    "node_name": "Door to Area 1"
                                },
                                "default_dock_weakness": "Open Passage",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {}
                            }
                        }
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
                                "layers": [
                                    "default"
                                ],
                                "extra": {},
                                "valid_starting_location": True,
                                "connections": {}
                            },
                            "Door to Area 1": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "layers": [
                                    "default"
                                ],
                                "extra": {},
                                "valid_starting_location": True,
                                "dock_type": "other",
                                "default_connection": {
                                    "world_name": "World",
                                    "area_name": "Area 1",
                                    "node_name": "Door to Area 2 (Generic)"
                                },
                                "default_dock_weakness": "Open Passage",
                                "override_default_open_requirement": None,
                                "override_default_lock_requirement": None,
                                "connections": {}
                            }
                        }
                    }
                }
            }
        ]
    }
    gd = data_reader.decode_data(sample_data)

    # Run
    errors = integrity_check.find_database_errors(gd)

    # Assert
    assert errors == [
        "World - Area 1 - 'Event - Foo' is not an Event Node, but naming suggests it is",
        "World - Area 1 - Node 'Event - Foo' has a connection to itself",
        "World - Area 1 - 'Door to Area 2 (Generic)' should be named 'Other to Area 2 (...)'",
        "World - Area 1 - 'Door to Area 2 (Generic)' connects to 'world World/area Area 2/node Generic Node'"
        " which is not a DockNode",
        "World - Area 1 - 'Door to Area 2 (Dock)' should be named 'Other to Area 2 (...)'",
        "World - Area 1 - 'Door to Area 2 (Dock)' connects to 'world World/area Area 2/node Door to Area 1',"
        " but that dock connects to 'world World/area Area 1/node Door to Area 2 (Generic)' instead.",
        "World - Area 2 - 'Door to Area 1' should be named 'Other to Area 1'",
        "World - Area 2 - 'Door to Area 1' connects to 'world World/area Area 1/node Door to Area 2 (Generic)',"
        " but that dock connects to 'world World/area Area 2/node Generic Node' instead.",
        "World - Area 2 has multiple valid start nodes ['Generic Node', 'Door to Area 1'], but is not allowed for Metroid Prime 2: Echoes",

        "Unknown strongly connected component detected containing 1 nodes:\n"
        "['World/Area 1/Event - Foo']",
        "Unknown strongly connected component detected containing 1 nodes:\n"
        "['World/Area 1/Door to Area 2 (Generic)']",
        "Unknown strongly connected component detected containing 1 nodes:\n"
        "['World/Area 2/Door to Area 1']",
        "Unknown strongly connected component detected containing 1 nodes:\n"
        "['World/Area 1/Door to Area 2 (Dock)']"
    ]
