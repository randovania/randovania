from __future__ import annotations

from randovania.lib import migration_lib


def _migrate_v6(data: dict) -> dict:
    lore_types = {
        "luminoth-lore": "requires-item",
        "luminoth-warrior": "specific-pickup",
        "pirate-lore": "generic"
    }
    for world in data["worlds"]:
        for area in world["areas"].values():
            for node in area["nodes"].values():
                if node["node_type"] == "logbook":
                    node["lore_type"] = lore_types.get(node["lore_type"], node["lore_type"])
    return data


def _migrate_v7(data: dict) -> dict:
    if data["minimal_logic"] is not None:
        data["minimal_logic"]["description"] = "Unknown text"
    return data


def _migrate_v8(data: dict) -> dict:
    lock_type_mapping = {
        1: "front-blast-back-free-unlock",
        2: "front-blast-back-blast",
        3: "front-blast-back-impossible",
    }
    if data["game"] == "dread":
        lock_type_mapping[3] = "front-blast-back-if-matching"

    for dock_type in data["dock_weakness_database"]["types"].values():
        for dock_weakness in dock_type["items"].values():
            lock_type = dock_weakness.pop("lock_type")
            if lock_type == 0:
                dock_weakness["lock"] = None
            else:
                dock_weakness["lock"] = {
                    "lock_type": lock_type_mapping[lock_type],
                    "requirement": dock_weakness["requirement"],
                }
                # Trivial
                dock_weakness["requirement"] = {"type": "and", "data": {"comment": None, "items": []}}

    for world in data["worlds"]:
        for area in world["areas"].values():
            for node in area["nodes"].values():
                if node["node_type"] == "dock":
                    node["default_connection"] = node.pop("destination")
                    node["default_dock_weakness"] = node.pop("dock_weakness")
                    node["override_default_open_requirement"] = None
                    node["override_default_lock_requirement"] = None

    return data


def _migrate_v9(data: dict) -> dict:
    data["layers"] = ["default"]

    for world in data["worlds"]:
        for area in world["areas"].values():
            for node in area["nodes"].values():
                node["layers"] = ["default"]

    return data


def _migrate_v10(data: dict) -> dict:
    for dock_type in data["dock_weakness_database"]["types"].values():
        dock_type["dock_rando"] = {
            "unlocked": None,
            "locked": None,
            "change_from": [],
            "change_to": []
        }

    return data


def _migrate_v11(data: dict) -> dict:
    data["dock_weakness_database"]["dock_rando"] = {
        "enable_one_way": False,
        "force_change_two_way": False,
        "resolver_attempts": 125,
        "to_shuffle_proportion": 1.0
    }
    return data


def _migrate_v12(data: dict) -> dict:
    for world in data["worlds"]:
        for area in world["areas"].values():
            for node in area["nodes"].values():
                if node["node_type"] == "player_ship":
                    node["node_type"] = "teleporter_network"
                    node["network"] = "default"

                    node["requirement_to_activate"] = {
                        "type": "and",
                        "data": {
                            "comment": None,
                            "items": [
                            ]
                        }
                    }
                    if data["game"] == "prime3":
                        node["requirement_to_activate"]["data"]["items"].append({
                            "type": "resource",
                            "data": {
                                "type": "items",
                                "name": "CommandVisor",
                                "amount": 1,
                                "negate": False
                            }
                        })

                elif node["node_type"] == "logbook":
                    node["node_type"] = "hint"
                    lore_type = node.pop("lore_type")

                    required_items = []

                    if data["game"] == "prime2":
                        required_items.append("Scan")

                    if lore_type == "requires-item":
                        required_items.append(node["extra"]["translator"])
                        lore_type = "generic"

                    node["extra"]["string_asset_id"] = node.pop("string_asset_id")
                    node["kind"] = lore_type
                    node["requirement_to_collect"] = {
                        "type": "and",
                        "data": {
                            "comment": None,
                            "items": [
                                {
                                    "type": "resource",
                                    "data": {
                                        "type": "items",
                                        "name": item,
                                        "amount": 1,
                                        "negate": False
                                    }
                                }
                                for item in required_items
                            ]
                        }
                    }

    return data


def _migrate_v13(data: dict) -> dict:
    for world in data["worlds"]:
        for area_name, area in world["areas"].items():
            old_valid_starting_location = area["valid_starting_location"]
            start_node_name = area["default_node"]

            starting_location = data["starting_location"]
            if world["name"] == starting_location["world_name"] and area_name == starting_location["area_name"]:
                starting_location["node_name"] = start_node_name

            for node_name, node in area["nodes"].items():
                if old_valid_starting_location and node_name == start_node_name:
                    node["valid_starting_location"] = True
                else:
                    node["valid_starting_location"] = False
            del area["valid_starting_location"]
    return data


def _migrate_v14(data: dict) -> dict:
    for world in data["worlds"]:
        for area_name, area in world["areas"].items():
            for node_name, node in area["nodes"].items():
                if node["node_type"] == "pickup":
                    node["location_category"] = "major" if node.pop("major_location") else "minor"

    return data


def _migrate_v15(data: dict) -> dict:
    del data["dock_weakness_database"]["dock_rando"]["enable_one_way"]
    return data


def _migrate_v16(data: dict) -> dict:
    for world in data["worlds"]:
        for area_name, area in world["areas"].items():
            for node_name, node in area["nodes"].items():
                if node["node_type"] == "dock":
                    node["exclude_from_dock_rando"] = node["extra"].pop("exclude_from_dock_rando", False)
                    node["incompatible_dock_weaknesses"] = node["extra"].pop("excluded_dock_weaknesses", [])

    return data


def _migrate_v17(data: dict) -> dict:
    if "worlds" in data:
        data["regions"] = data.pop("worlds")

    def _fix(target):
        target["region"] = target.pop("world_name")
        target["area"] = target.pop("area_name")
        if "node_name" in target:
            target["node"] = target.pop("node_name")

    _fix(data["starting_location"])
    for world in data["regions"]:
        for area_name, area in world["areas"].items():
            for node_name, node in area["nodes"].items():
                if node["node_type"] == "dock":
                    _fix(node["default_connection"])
                elif node["node_type"] == "teleporter":
                    _fix(node["destination"])

    return data


def _migrate_v18(data: dict) -> dict:
    data["resource_database"].pop("item_percentage_index")
    data["resource_database"].pop("multiworld_magic_item_index")
    return data


def _migrate_v19(data: dict) -> dict:
    game = data["game"]
    if game in {"blank", "cave_story", "am2r"}:
        return data

    # changes TeleporterNode to DockNode
    def change_node(node_to_change, regions_data: dict):
        node_to_change["node_type"] = "dock"
        node_to_change["default_connection"] = node_to_change.pop("destination")

        # find the default node
        target_region_data = next(region for region in regions_data if region["name"]
                                  == node_to_change["default_connection"]["region"])
        area_data = target_region_data["areas"][node_to_change["default_connection"]["area"]]
        node_to_change["default_connection"]["node"] = area_data["default_node"]

        node_to_change["default_dock_weakness"] = "Teleporter"
        node_to_change["exclude_from_dock_rando"] = False
        node_to_change["incompatible_dock_weaknesses"] = []
        node_to_change["override_default_open_requirement"] = None
        node_to_change["override_default_lock_requirement"] = None
        node_to_change["extra"]["keep_name_when_vanilla"] = node_to_change.pop("keep_name_when_vanilla")
        node_to_change["extra"]["editable"] = node_to_change.pop("editable")
        node_to_change["dock_type"] = "teleporter"

    # adds the required weaknesses
    def add_dock_weakness(data: dict, game):
        teleporter_weakness = {
            "name": "Teleporter",
            "extra": {"is_teleporter": True, "ignore_for_hints": True},
            "items": {
                "Teleporter": {
                    "extra": {},
                    "requirement": {
                        "type": "and",
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

        data["dock_weakness_database"]["types"]["teleporter"] = teleporter_weakness
        if game == "prime2":
            data["dock_weakness_database"]["types"]["portal"]["extra"]["ignore_for_hints"] = True

    regions_data = data["regions"]

    # iterate overall nodes and checks if they are teleporter nodes
    all_nodes = [
        node
        for region in regions_data
        for area_name, area in region["areas"].items()
        for node_name, node in area["nodes"].items() if node["node_type"] == "teleporter"
    ]
    for node in all_nodes:
        change_node(node, regions_data)

    add_dock_weakness(data, game)

    return data


def _migrate_v20(data: dict) -> dict:
    for type_data in data["dock_weakness_database"]["types"].values():
        if type_data["dock_rando"] is not None and type_data["dock_rando"]["locked"] is None:
            type_data["dock_rando"] = None

    return data


def _migrate_v21(data: dict) -> dict:
    data["used_trick_levels"] = None

    return data


_MIGRATIONS = [
    None,
    None,
    None,
    None,
    None,
    _migrate_v6,
    _migrate_v7,
    _migrate_v8,
    _migrate_v9,
    _migrate_v10,
    _migrate_v11,
    _migrate_v12,
    _migrate_v13,
    _migrate_v14,
    _migrate_v15,
    _migrate_v16,
    _migrate_v17,
    _migrate_v18,
    _migrate_v19,
    _migrate_v20,
    _migrate_v21,
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def migrate_to_current(data: dict):
    return migration_lib.apply_migrations(data, _MIGRATIONS,
                                          copy_before_migrating=True)
