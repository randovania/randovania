from build.lib.randovania.game_description.resources.resource_type import ResourceType
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
    db = data["resource_database"]

    find_resource = lambda res_type, index: filter(lambda item: item.index == index, db[res_type])[0]

    special_indices = {"energy_tank_item_index", "item_percentage_index", "multiworld_magic_item_index"}
    for name in special_indices:
        index = db[name]
        db[name] = find_resource("items", index)

    def migrate_reduction(reduction: dict) -> dict:
        reduction["name"] = find_resource(ResourceType.DAMAGE.value, reduction.pop("index"))
        for red in reduction["reductions"]:
            red["name"] = find_resource(ResourceType.ITEM.value, red.pop("index"))
        return reduction
    
    db["damage_reductions"] = [migrate_reduction(red) for red in db["damage_reductions"]]

    def migrate_requirement(requirement: dict) -> dict:
        data = requirement["data"]

        if requirement["type"] == "resource":
            data["type"] = ResourceType.from_index(data["type"]).value
            data["name"] = find_resource(data["type"], data.pop("index"))
        else:
            data["items"] = [migrate_requirement(req) for req in data["items"]]
        
        return {
            "type": requirement["type"],
            "data": data
        }
    
    db["requirement_template"] = {k: migrate_requirement(v) for k,v in db["requirement_template"].items()}
    data["victory_condition"] = migrate_requirement(data["victory_condition"])
    
    # TODO: move dock types to keys instead of indices as well?
    for dock_type in data["dock_weakness_database"]:
        for dock in dock_type:
            dock["requirement"] = migrate_requirement(dock["requirement"])
    
    for world in data["worlds"]:
        for area in world["areas"].values():
            for node in area["nodes"].values():
                node["connections"] = {k: migrate_requirement(v) for k,v in node["connections"].items()}
                
                node_type = node["node_type"]
                if node_type == "event":
                    node["event_name"] = find_resource(ResourceType.EVENT.value, node.pop("event_index"))
                if node_type == "translator_gate":
                    pass # TODO
                if node_type == "pickup":
                    pass # TODO

    lists_to_migrate = {restype for restype in ResourceType if restype < ResourceType._INDEXED}
    for name in lists_to_migrate:
        new_res_list = {resource.pop("short_name"): resource for resource in db[name]}
        for resource in new_res_list.items():
            resource.pop("index")
        db[name] = new_res_list
    
    return data

_MIGRATIONS = {
    1: _migrate_v1,
    2: _migrate_v2
}


def migrate_to_current(data: dict) -> dict:
    schema_version = data.get("schema_version", 1)

    while schema_version < CURRENT_DATABASE_VERSION:
        data = _MIGRATIONS[schema_version](data)
        schema_version += 1

    data["schema_version"] = schema_version

    return data
