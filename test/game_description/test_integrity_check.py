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
        "schema_version": 6,
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
        "starting_location": {
            "world_name": "World",
            "area_name": "Area 2"
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
                    "items": {}
                },
                "portal": {
                    "name": "Portal",
                    "extra": {},
                    "items": {}
                },
                "morph_ball": {
                    "name": "Morph Ball Door",
                    "extra": {},
                    "items": {}
                },
                "other": {
                    "name": "Other",
                    "extra": {},
                    "items": {
                        "Open Passage": {
                            "lock_type": 0,
                            "extra": {},
                            "requirement": {
                                "type": "and",
                                "data": {
                                    "comment": None,
                                    "items": []
                                }
                            }
                        },
                        "Not Determined": {
                            "lock_type": 0,
                            "extra": {},
                            "requirement": {
                                "type": "or",
                                "data": {
                                    "comment": None,
                                    "items": []
                                }
                            }
                        }
                    }
                }
            },
            "default_weakness": {
                "type": "other",
                "name": "Not Determined"
            }
        },
        "worlds": [
            {
                "name": "World",
                "extra": {},
                "areas": {
                    "Area 1": {
                        "default_node": None,
                        "valid_starting_location": False,
                        "extra": {},
                        "nodes": {
                            "Event - Foo": {
                                "node_type": "generic",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "extra": {},
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
                                "extra": {},
                                "destination": {
                                    "world_name": "World",
                                    "area_name": "Area 2",
                                    "node_name": "Generic Node"
                                },
                                "dock_type": "other",
                                "dock_weakness": "Open Passage",
                                "connections": {}
                            },
                            "Door to Area 2 (Dock)": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "extra": {},
                                "destination": {
                                    "world_name": "World",
                                    "area_name": "Area 2",
                                    "node_name": "Door to Area 1"
                                },
                                "dock_type": "other",
                                "dock_weakness": "Open Passage",
                                "connections": {}
                            }
                        }
                    },
                    "Area 2": {
                        "default_node": "Generic Node",
                        "valid_starting_location": False,
                        "extra": {},
                        "nodes": {
                            "Generic Node": {
                                "node_type": "generic",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "extra": {},
                                "connections": {}
                            },
                            "Door to Area 1": {
                                "node_type": "dock",
                                "heal": False,
                                "coordinates": None,
                                "description": "",
                                "extra": {},
                                "destination": {
                                    "world_name": "World",
                                    "area_name": "Area 1",
                                    "node_name": "Door to Area 2 (Generic)"
                                },
                                "dock_type": "other",
                                "dock_weakness": "Open Passage",
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

        "Unknown strongly connected component detected containing 1 nodes:\n"
        "['World/Area 1/Event - Foo']",
        "Unknown strongly connected component detected containing 1 nodes:\n"
        "['World/Area 1/Door to Area 2 (Generic)']",
        "Unknown strongly connected component detected containing 1 nodes:\n"
        "['World/Area 2/Door to Area 1']",
        "Unknown strongly connected component detected containing 1 nodes:\n"
        "['World/Area 1/Door to Area 2 (Dock)']"
    ]
