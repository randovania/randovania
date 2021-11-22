from typing import Callable, Optional, Union
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description import migration_data
from randovania.game_description.world.node import LoreType
from randovania.games.game import RandovaniaGame

CURRENT_DATABASE_VERSION = 4
CURRENT_ITEMDB_VERSION = 2

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

def _migrate_v3(data: dict) -> dict:
    game = RandovaniaGame(data["game"])
    db = data["resource_database"]

    keep_res_index = game.value in {"prime1", "prime2", "prime3", "super_metroid"}

    def find_resource(res_type: Union[ResourceType, str], index: Optional[int]):
        if index is None:
            return None
        if isinstance(res_type, str):
            res_type = ResourceType(res_type)
        return migration_data.get_resource_name_from_index(game, index, res_type)

    special_indices = {"energy_tank_item_index", "item_percentage_index", "multiworld_magic_item_index"}
    for name in special_indices:
        index = db[name]
        db[name] = find_resource(ResourceType.ITEM, index)

    def migrate_reduction(reduction: dict) -> dict:
        reduction["name"] = find_resource(ResourceType.DAMAGE, reduction.pop("index"))
        for red in reduction["reductions"]:
            red["name"] = find_resource(ResourceType.ITEM, red.pop("index"))
        return reduction
    
    db["damage_reductions"] = [migrate_reduction(red) for red in db["damage_reductions"]]

    def migrate_requirement(requirement: dict) -> dict:
        data = requirement["data"]

        if requirement["type"] == "resource":
            data["type"] = migration_data.get_resource_type_from_index(data["type"]).value
            data["name"] = find_resource(data["type"], data.pop("index"))
        elif requirement["type"] != "template":
            data["items"] = [migrate_requirement(req) for req in data["items"]]
        
        return {
            "type": requirement["type"],
            "data": data
        }
    
    db["requirement_template"] = {k: migrate_requirement(v) for k,v in db["requirement_template"].items()}
    data["victory_condition"] = migrate_requirement(data["victory_condition"])
    
    for key, state in data["initial_states"].items():
        data["initial_states"][key] = [{
            "resource_type": migration_data.get_resource_type_from_index(resource["resource_type"]).value,
            "resource_name": find_resource(migration_data.get_resource_type_from_index(resource["resource_type"]), resource.pop("resource_index")),
            "amount": resource["amount"]
        } for resource in state]
    
    minimal = data["minimal_logic"]
    if minimal is not None:
        minimal["items_to_exclude"] = [{
            "name": find_resource(ResourceType.ITEM, item["index"]),
            "when_shuffled": item["when_shuffled"]
        } for item in minimal["items_to_exclude"]]
        minimal["custom_item_amount"] = [{
            "name": find_resource(ResourceType.ITEM, item["index"]),
            "value": item["value"]
        } for item in minimal["custom_item_amount"]]
        minimal["events_to_exclude"] = [{
            "name": find_resource(ResourceType.EVENT, item["index"]),
            "reason": item["reason"]
        } for item in minimal["events_to_exclude"]]

    # TODO: move dock types to keys instead of indices as well?
    for dock_type in data["dock_weakness_database"].values():
        for dock in dock_type:
            dock["requirement"] = migrate_requirement(dock["requirement"])
    
    for world in data["worlds"]:
        for area in world["areas"].values():
            for node in area["nodes"].values():
                node["connections"] = {k: migrate_requirement(v) for k,v in node["connections"].items()}
                
                node_type = node["node_type"]
                if node_type == "event":
                    node["event_name"] = find_resource(ResourceType.EVENT, node.pop("event_index"))

                if node_type == "logbook":
                    lore_type = LoreType(node["lore_type"])
                    if lore_type == LoreType.LUMINOTH_LORE:
                        node["extra"]["translator"] = find_resource(ResourceType.ITEM, node.pop("lore_extra"))
                    if lore_type in {LoreType.LUMINOTH_WARRIOR, LoreType.SKY_TEMPLE_KEY_HINT}:
                        node["extra"]["hint_index"] = node.pop("lore_extra")
                
                if node_type == "player_ship":
                    node["is_unlocked"] = migrate_requirement(node["is_unlocked"])

                if node_type == "translator_gate":
                    pass # TODO

                if node_type == "pickup":
                    pass # TODO

    lists_to_migrate = {restype for restype in ResourceType if restype < ResourceType._INDEXED}
    for name in lists_to_migrate:
        new_res_list = {resource.pop("short_name"): resource for resource in db[name]}
        for resource in new_res_list.values():
            if name == ResourceType.ITEM:
                extra = resource["extra"]
                resource["extra"] = {}
                if extra is not None:
                    resource["extra"]["specific"] = extra
                if keep_res_index:
                    resource["extra"]["item_id"] = resource["index"]
            else:
                resource["extra"] = {}
            resource.pop("index")
        db[name] = new_res_list
    
    return data

_MIGRATIONS = {
    1: _migrate_v1,
    2: _migrate_v2,
    3: _migrate_v3,
}

def _migrate_item_v1(data: dict) -> dict:
    game = RandovaniaGame(data["game"])
    for item in data["items"].values():
        item["progression"] = [migration_data.get_resource_name_from_index(game, progression, ResourceType.ITEM) for progression in item["progression"]]
        ammo = item.get("ammo")
        if ammo is not None:
            item["ammo"] = [migration_data.get_resource_name_from_index(game, ammo, ResourceType.ITEM) for ammo in item["ammo"]]
    for ammo in data["ammo"].values():
        ammo["items"] = [migration_data.get_resource_name_from_index(game, item, ResourceType.ITEM) for item in ammo["items"]]
        unlock = ammo.get("unlocked_by")
        if unlock is not None:
            ammo["unlocked_by"] = migration_data.get_resource_name_from_index(game, ammo["unlocked_by"], ResourceType.ITEM)
        temporary = ammo.get("temporary")
        if temporary is not None:
            ammo["temporary"] = migration_data.get_resource_name_from_index(game, ammo["temporary"], ResourceType.ITEM)
    return data

_ITEM_MIGRATIONS = {
    1: _migrate_item_v1
}

def _migrate_to_current(data: dict, version: int, migrations: dict[int, Callable[[dict], dict]]) -> dict:
    schema_version = data.get("schema_version", 1)

    while schema_version < version:
        data = migrations[schema_version](data)
        schema_version += 1

    data["schema_version"] = schema_version

    return data

def migrate_to_current(data: dict):
    return _migrate_to_current(data, CURRENT_DATABASE_VERSION, _MIGRATIONS)

def migrate_items_to_current(data: dict):
    return _migrate_to_current(data, CURRENT_ITEMDB_VERSION, _ITEM_MIGRATIONS)
