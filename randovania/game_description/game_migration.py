from __future__ import annotations

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import migration_data
from randovania.lib import migration_lib


def _migrate_v6(data: dict, game: RandovaniaGame) -> None:
    lore_types = {"luminoth-lore": "requires-item", "luminoth-warrior": "specific-pickup", "pirate-lore": "generic"}
    for world in data["worlds"]:
        for area in world["areas"].values():
            for node in area["nodes"].values():
                if node["node_type"] == "logbook":
                    node["lore_type"] = lore_types.get(node["lore_type"], node["lore_type"])


def _migrate_v7(data: dict, game: RandovaniaGame) -> None:
    if data["minimal_logic"] is not None:
        data["minimal_logic"]["description"] = "Unknown text"


def _migrate_v8(data: dict, game: RandovaniaGame) -> None:
    lock_type_mapping = {
        1: "front-blast-back-free-unlock",
        2: "front-blast-back-blast",
        3: "front-blast-back-impossible",
    }
    if game == RandovaniaGame.METROID_DREAD:
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


def _migrate_v9(data: dict, game: RandovaniaGame) -> None:
    data["layers"] = ["default"]

    for world in data["worlds"]:
        for area in world["areas"].values():
            for node in area["nodes"].values():
                node["layers"] = ["default"]


def _migrate_v10(data: dict, game: RandovaniaGame) -> None:
    for dock_type in data["dock_weakness_database"]["types"].values():
        dock_type["dock_rando"] = {"unlocked": None, "locked": None, "change_from": [], "change_to": []}


def _migrate_v11(data: dict, game: RandovaniaGame) -> None:
    data["dock_weakness_database"]["dock_rando"] = {
        "enable_one_way": False,
        "force_change_two_way": False,
        "resolver_attempts": 125,
        "to_shuffle_proportion": 1.0,
    }


def _migrate_v12(data: dict, game: RandovaniaGame) -> None:
    for world in data["worlds"]:
        for area in world["areas"].values():
            for node in area["nodes"].values():
                if node["node_type"] == "player_ship":
                    node["node_type"] = "teleporter_network"
                    node["network"] = "default"
                    node["requirement_to_activate"] = {"type": "and", "data": {"comment": None, "items": []}}

                elif node["node_type"] == "logbook":
                    node["node_type"] = "hint"
                    lore_type = node.pop("lore_type")

                    required_items = []

                    if game == RandovaniaGame.METROID_PRIME_ECHOES:
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
                                    "data": {"type": "items", "name": item, "amount": 1, "negate": False},
                                }
                                for item in required_items
                            ],
                        },
                    }


def _migrate_v13(data: dict, game: RandovaniaGame) -> None:
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


def _migrate_v14(data: dict, game: RandovaniaGame) -> None:
    for world in data["worlds"]:
        for area_name, area in world["areas"].items():
            for node_name, node in area["nodes"].items():
                if node["node_type"] == "pickup":
                    node["location_category"] = "major" if node.pop("major_location") else "minor"


def _migrate_v15(data: dict, game: RandovaniaGame) -> None:
    del data["dock_weakness_database"]["dock_rando"]["enable_one_way"]


def _migrate_v16(data: dict, game: RandovaniaGame) -> None:
    for world in data["worlds"]:
        for area_name, area in world["areas"].items():
            for node_name, node in area["nodes"].items():
                if node["node_type"] == "dock":
                    node["exclude_from_dock_rando"] = node["extra"].pop("exclude_from_dock_rando", False)
                    node["incompatible_dock_weaknesses"] = node["extra"].pop("excluded_dock_weaknesses", [])


def _migrate_v17(data: dict, game: RandovaniaGame) -> None:
    if "worlds" in data:
        data["regions"] = data.pop("worlds")

    def _fix(target: dict) -> None:
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


def _migrate_v18(data: dict, game: RandovaniaGame) -> None:
    data["resource_database"].pop("item_percentage_index")
    data["resource_database"].pop("multiworld_magic_item_index")


def _migrate_v19(data: dict, game: RandovaniaGame) -> None:
    if game in {RandovaniaGame.BLANK, RandovaniaGame.CAVE_STORY, RandovaniaGame.AM2R}:
        return

    # changes TeleporterNode to DockNode
    def change_node(node_to_change: dict, regions_data: dict) -> None:
        node_to_change["node_type"] = "dock"
        node_to_change["default_connection"] = node_to_change.pop("destination")

        # find the default node
        target_region_data = next(
            region for region in regions_data if region["name"] == node_to_change["default_connection"]["region"]
        )
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
    def add_dock_weakness(data: dict, _game: RandovaniaGame) -> None:
        teleporter_weakness = {
            "name": "Teleporter",
            "extra": {"is_teleporter": True, "ignore_for_hints": True},
            "items": {
                "Teleporter": {
                    "extra": {},
                    "requirement": {"type": "and", "data": {"comment": None, "items": []}},
                    "lock": None,
                }
            },
            "dock_rando": {"unlocked": None, "locked": None, "change_from": [], "change_to": []},
        }

        data["dock_weakness_database"]["types"]["teleporter"] = teleporter_weakness
        if _game == RandovaniaGame.METROID_PRIME_ECHOES:
            data["dock_weakness_database"]["types"]["portal"]["extra"]["ignore_for_hints"] = True

    regions_data = data["regions"]

    # iterate overall nodes and checks if they are teleporter nodes
    all_nodes = [
        node
        for region in regions_data
        for area_name, area in region["areas"].items()
        for node_name, node in area["nodes"].items()
        if node["node_type"] == "teleporter"
    ]
    for node in all_nodes:
        change_node(node, regions_data)

    add_dock_weakness(data, game)


def _migrate_v20(data: dict, game: RandovaniaGame) -> None:
    for type_data in data["dock_weakness_database"]["types"].values():
        if type_data["dock_rando"] is not None and type_data["dock_rando"]["locked"] is None:
            type_data["dock_rando"] = None


def _migrate_v21(data: dict, game: RandovaniaGame) -> None:
    data["used_trick_levels"] = None


def _migrate_v22(data: dict, game: RandovaniaGame) -> None:
    data["resource_database"]["requirement_template"] = {
        name: {
            "display_name": name,
            "requirement": requirement,
        }
        for name, requirement in data["resource_database"]["requirement_template"].items()
    }


def _migrate_v23(data: dict, game: RandovaniaGame) -> None:
    for trick in data["resource_database"]["tricks"].values():
        trick["require_documentation_above"] = 0


def _migrate_v24(data: dict, game: RandovaniaGame) -> None:
    regions_data = data["regions"]
    migration_dict = migration_data.get_raw_data(game)
    elevator_custom_name: dict[str, str] | None = migration_dict.get("elevator_custom_names", None)

    for region in regions_data:
        for area_name, area in region["areas"].items():
            for node_name, node in area["nodes"].items():
                if node["node_type"] == "dock":
                    full_qualified_name = f"{region['name']}/{area_name}/{node_name}"
                    if (
                        elevator_custom_name is not None
                        and elevator_custom_name.get(full_qualified_name, None) is not None
                    ):
                        node["ui_custom_name"] = elevator_custom_name[full_qualified_name]
                    else:
                        node["ui_custom_name"] = None


def _migrate_v25(data: dict, game: RandovaniaGame) -> None:
    data["flatten_to_set_on_patch"] = False


def _migrate_v26(data: dict, game: RandovaniaGame) -> None:
    data.pop("initial_states")


def _migrate_v27(data: dict, game: RandovaniaGame) -> None:
    data["hint_feature_database"] = {}
    for region in data["regions"]:
        for area in region["areas"].values():
            area["hint_features"] = []
            for node in area["nodes"].values():
                if node["node_type"] == "pickup":
                    node["hint_features"] = []


def _migrate_v28(data: dict, game: RandovaniaGame) -> None:
    hint_types = {
        "generic": "generic",
        "specific-pickup": "specific-location",
        "specific-item": "specific-pickup",
    }
    for region in data["regions"]:
        for area in region["areas"].values():
            for node in area["nodes"].values():
                if node["node_type"] == "hint":
                    node["kind"] = hint_types[node["kind"]]


def _migrate_v29(data: dict, game: RandovaniaGame) -> None:
    for region in data["regions"]:
        for area in region["areas"].values():
            for node in area["nodes"].values():
                if node["node_type"] == "pickup":
                    custom_index_group = None
                    # while Cave Story uses this flag, it actually wants to consider it separate regions
                    if game.value == "prime2":
                        if area["extra"]["in_dark_aether"]:
                            custom_index_group = region["name"]
                    node["custom_index_group"] = custom_index_group


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
    _migrate_v22,
    _migrate_v23,  # add require_documentation_above
    _migrate_v24,
    _migrate_v25,  # flatten_to_set_on_patch
    _migrate_v26,  # remove initial_states
    _migrate_v27,  # add hint features
    _migrate_v28,  # rename HintNodeKind
    _migrate_v29,  # add custom_index_group
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def migrate_to_current(data: dict, game: RandovaniaGame) -> dict:
    return migration_lib.apply_migrations_with_game(data, _MIGRATIONS, game, copy_before_migrating=True)
