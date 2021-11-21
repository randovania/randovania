from randovania.game_description import migration_data
from randovania.games.game import RandovaniaGame

CURRENT_DATABASE_VERSION = 3


def _migrate_v1(data: dict) -> dict:
    game = RandovaniaGame(data["game"])

    data["starting_location"] = migration_data.convert_area_loc_id_to_name(game, data["starting_location"])

    for world in data["worlds"]:
        world_name = world["name"]
        new_areas = {}

        if world.get("extra") is None:
            world["extra"] = {}

        world["extra"]["asset_id"] = world.pop("asset_id")
        if (dark_name := world.pop("dark_name")) is not None:
            world["extra"]["dark_name"] = dark_name

        for area in world["areas"]:
            area_name = area.pop("name")
            if area_name in new_areas:
                raise ValueError("Name conflict in {}: {}".format(world["name"], area_name))

            # extra = JsonEncodedValue,
            area["default_node"] = None
            if (default_node_index := area.pop("default_node_index")) is not None:
                area["default_node"] = area["nodes"][default_node_index]["name"]

            if area.get("extra") is None:
                area["extra"] = {}

            area["extra"]["asset_id"] = area.pop("asset_id")
            if dark_name is not None:
                area["extra"]["in_dark_aether"] = area.pop("in_dark_aether")

            new_nodes = {}
            for node in area["nodes"]:
                node_name = node.pop("name")

                if node_name in new_nodes:
                    raise ValueError("Name conflict in {} - {}: {}".format(world["name"], area_name, node_name))

                if node.get("extra") is None:
                    node["extra"] = {}

                if node["node_type"] == "dock":
                    node["connected_area_name"] = migration_data.get_area_name_from_id(
                        game, world_name, node.pop("connected_area_asset_id"))

                elif node["node_type"] == "teleporter":
                    dest = {
                        "world_asset_id": node.pop("destination_world_asset_id"),
                        "area_asset_id": node.pop("destination_area_asset_id"),
                    }
                    node["destination"] = migration_data.convert_area_loc_id_to_name(game, dest)
                    node["extra"]["scan_asset_id"] = node.pop("scan_asset_id")
                    node["extra"]["teleporter_instance_id"] = node.pop("teleporter_instance_id")

                new_nodes[node_name] = node

            area["nodes"] = new_nodes
            new_areas[area_name] = area

        world["areas"] = new_areas

    return data


def _migrate_v2(data: dict) -> dict:
    should_keep_index = data["game"] in {"prime1", "prime2", "prime3"}

    for world in data["worlds"]:
        world_name: str = world["name"]
        areas: dict[str, dict] = world["areas"]
        dock_index_to_name = {}

        for area_name, area in areas.items():
            nodes: dict[str, dict] = area["nodes"]
            dock_index_to_name[area_name] = {}

            for node_name, node in nodes.items():
                node["description"] = ""
                if node["node_type"] == "dock":
                    dock_index = node.pop("dock_index")
                    dock_index_to_name[area_name][dock_index] = node_name
                    if should_keep_index:
                        node["extra"]["dock_index"] = dock_index

        for area_name, area in areas.items():
            nodes: dict[str, dict] = area["nodes"]
            for node_name, node in nodes.items():
                if node["node_type"] == "dock":
                    area_name = node.pop("connected_area_name")
                    node["destination"] = {
                        "world_name": world_name,
                        "area_name": area_name,
                        "node_name": dock_index_to_name[area_name][node.pop("connected_dock_index")],
                    }

    return data


_MIGRATIONS = {
    1: _migrate_v1,
    2: _migrate_v2,
}


def migrate_to_current(data: dict) -> dict:
    schema_version = data.get("schema_version", 1)

    while schema_version < CURRENT_DATABASE_VERSION:
        data = _MIGRATIONS[schema_version](data)
        schema_version += 1

    data["schema_version"] = schema_version

    return data
