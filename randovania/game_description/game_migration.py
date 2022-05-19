from randovania.lib import migration_lib

CURRENT_VERSION = 10


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


_MIGRATIONS = {
    1: migration_lib.unsupported_migration,
    2: migration_lib.unsupported_migration,
    3: migration_lib.unsupported_migration,
    4: migration_lib.unsupported_migration,
    5: migration_lib.unsupported_migration,
    6: _migrate_v6,
    7: _migrate_v7,
    8: _migrate_v8,
    9: _migrate_v9,
}


def migrate_to_current(data: dict):
    return migration_lib.migrate_to_version(data, CURRENT_VERSION, _MIGRATIONS,
                                            copy_before_migrating=True)
