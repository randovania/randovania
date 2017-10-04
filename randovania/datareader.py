from collections import defaultdict
from functools import partial
from typing import List, Callable, TypeVar, BinaryIO, Tuple, Dict

from randovania import prime_binary_decoder
from randovania.game_description import DamageReduction, SimpleResourceInfo, DamageResourceInfo, \
    IndividualRequirement, \
    DockWeakness, RequirementSet, World, Area, Node, GenericNode, DockNode, TeleporterNode, ResourceNode, \
    GameDescription, ResourceType, ResourceDatabase, DockType, DockWeaknessDatabase, RequirementList
from randovania.log_parser import PickupEntry
from randovania.pickup_database import pickup_name_to_resource_gain

X = TypeVar('X')
Y = TypeVar('Y')


def read_array(data: List[Y], item_reader: Callable[[Y], X]) -> List[X]:
    return [
        item_reader(item)
        for item in data
    ]


def read_damage_reduction(data: Dict) -> DamageReduction:
    return DamageReduction(data["index"], data["multiplier"])


def read_damage_reductions(data: List[Dict]) -> Tuple[DamageReduction, ...]:
    return tuple(read_array(data, read_damage_reduction))


def read_resource_info(data: Dict) -> SimpleResourceInfo:
    return SimpleResourceInfo(data["index"], data["long_name"], data["short_name"])


def read_resource_info_array(data: List[Dict]) -> List[SimpleResourceInfo]:
    return read_array(data, read_resource_info)


def read_damage_resource_info(data: Dict) -> DamageResourceInfo:
    return DamageResourceInfo(data["index"], data["long_name"], data["short_name"],
                              read_damage_reductions(data["reductions"]))


def read_damage_resource_info_array(data: List[Dict]) -> List[DamageResourceInfo]:
    return read_array(data, read_damage_resource_info)


# Requirement

def read_individual_requirement(data: Dict, resource_database: ResourceDatabase) -> IndividualRequirement:
    return IndividualRequirement.with_data(
        resource_database,
        ResourceType(data["requirement_type"]),
        data["requirement_index"],
        data["amount"],
        data["negate"])


def read_requirement_list(data: List[Dict],
                          resource_database: ResourceDatabase) -> Tuple[IndividualRequirement, ...]:
    return RequirementList(read_array(data, partial(read_individual_requirement, resource_database=resource_database)))


def read_requirement_set(data: List[List[Dict]], resource_database: ResourceDatabase) -> RequirementSet:
    return RequirementSet(
        tuple(read_array(data, partial(read_requirement_list, resource_database=resource_database))))


# Dock Weakness

def read_dock_weakness_database(data: Dict, resource_database: ResourceDatabase) -> DockWeaknessDatabase:
    def read_dock_weakness(item: Dict) -> DockWeakness:
        return DockWeakness(item["index"], item["name"], item["is_blast_door"],
                            read_requirement_set(item["requirement_set"], resource_database))

    door_types = read_array(data["door"], read_dock_weakness)
    portal_types = read_array(data["portal"], read_dock_weakness)
    return DockWeaknessDatabase(
        door=door_types,
        morph_ball=[DockWeakness(0, "Morph Ball Door", False, RequirementSet.empty())],
        other=[DockWeakness(0, "Other Door", False, RequirementSet.empty())],
        portal=portal_types
    )


class WorldReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    pickup_entries: List[PickupEntry]
    generic_index: int = 0

    def __init__(self, resource_database: ResourceDatabase, dock_weakness_database: DockWeaknessDatabase,
                 pickup_entries: List[PickupEntry]):
        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database
        self.pickup_entries = pickup_entries

    def read_node(self, data: Dict) -> Node:
        name = data["name"]
        heal = data["heal"]
        node_type = data["node_type"]

        if node_type == 0:
            self.generic_index += 1
            return GenericNode(name, heal, self.generic_index)

        elif node_type == 1:
            return DockNode(name,
                            heal,
                            data["dock_index"],
                            data["connected_area_asset_id"],
                            data["connected_dock_index"],
                            self.dock_weakness_database.get_by_type_and_index(
                                DockType(data["dock_type"]),
                                data["dock_weakness_index"]))

        elif node_type == 2:
            return ResourceNode(name, heal, self.pickup_entries[data["pickup_index"]])

        elif node_type == 3:
            return TeleporterNode(name, heal,
                                  data["destination_world_asset_id"],
                                  data["destination_area_asset_id"],
                                  data["teleporter_instance_id"])

        elif node_type == 4:
            return ResourceNode(name, heal,
                                self.resource_database.get_by_type_and_index(
                                    ResourceType.EVENT,
                                    data["event_index"]))

        else:
            raise Exception("Unknown node type: {}".format(node_type))

    def read_area(self, data: Dict) -> Area:
        name = data["name"]
        nodes = read_array(data["nodes"], self.read_node)

        for node in nodes:  # type: PickupNode
            if isinstance(node, ResourceNode) and isinstance(node.resource, PickupEntry):
                if node.resource.room != name:
                    raise ValueError(
                        "Pickup at {}/{} has area name mismatch ({})".format(name, node.name, node.resource.room))

        connections = {}
        for i, origin in enumerate(data["connections"]):
            connections[nodes[i]] = {}
            for j, target in enumerate(origin):
                if target:
                    connections[nodes[i]][nodes[j]] = read_requirement_set(
                        target, self.resource_database)

        return Area(name, data["asset_id"], data["default_node_index"],
                    nodes, connections)

    def read_area_list(self, data: List[Dict]) -> List[Area]:
        return read_array(data, self.read_area)

    def read_world(self, data: Dict) -> World:
        return World(data["name"], data["asset_id"],
                     self.read_area_list(data["areas"]))

    def read_world_list(self, data: List[Dict]) -> List[World]:
        return read_array(data, self.read_world)


def read_resource_database(data: Dict) -> ResourceDatabase:
    return ResourceDatabase(
        item=read_resource_info_array(data["items"]),
        event=read_resource_info_array(data["events"]),
        trick=read_resource_info_array(data["tricks"]),
        damage=read_damage_resource_info_array(data["damage"]),
        version=read_resource_info_array(data["versions"]),
        misc=read_resource_info_array(data["misc"]),
        difficulty=read_resource_info_array(data["difficulty"]))


def decode_data(data: Dict, pickup_entries: List[PickupEntry]) -> GameDescription:
    game = data["game"]
    game_name = data["game_name"]

    resource_database = read_resource_database(data["resource_database"])
    dock_weakness_database = read_dock_weakness_database(
        data["dock_weakness_database"], resource_database)

    world_reader = WorldReader(resource_database, dock_weakness_database, pickup_entries)
    worlds = world_reader.read_world_list(data["worlds"])

    final_boss = [event for event in resource_database.event if event.long_name == "Emperor Ing"][0]
    victory_condition = RequirementSet(tuple([
        RequirementList([IndividualRequirement(final_boss, 1, False)])
    ]))

    available_resources = defaultdict(int)

    nodes_to_area = {}
    nodes_to_world = {}
    for world in worlds:
        for area in world.areas:
            for node in area.nodes:
                if node in nodes_to_area:
                    raise ValueError("Trying to map {} to {}, but already mapped to {}".format(
                        node, area, nodes_to_area[node]
                    ))
                nodes_to_area[node] = area
                nodes_to_world[node] = world

                if isinstance(node, ResourceNode):
                    available_resources[node.resource] += 1
                    if isinstance(node.resource, PickupEntry):
                        for resource, quantity in pickup_name_to_resource_gain(node.resource.item, resource_database):
                            available_resources[resource] += quantity

    return GameDescription(
        game=game,
        game_name=game_name,
        resource_database=resource_database,
        dock_weakness_database=dock_weakness_database,
        worlds=worlds,
        nodes_to_area=nodes_to_area,
        nodes_to_world=nodes_to_world,
        available_resources=available_resources,
        victory_condition=victory_condition
    )


def patch_data(data: Dict):
    for world in data["worlds"]:
        for area in world["areas"]:
            # Aerie Transport Station has default_node_index not set
            if area["asset_id"] == 3136899603:
                area["default_node_index"] = 2

            # Hive Temple Access has incorrect requirements for unlocking Hive Temple gate
            if area["asset_id"] == 3968294891:
                area["connections"][1][2] = [[
                    {
                        "requirement_type": 0,
                        "requirement_index": 38 + i,
                        "amount": 1,
                        "negate": False,
                    }
                    for i in range(3)
                ]]


def read(path, pickup_entries: List[PickupEntry]) -> GameDescription:
    with open(path, "rb") as x:  # type: BinaryIO
        data = prime_binary_decoder.decode(x)

    patch_data(data)

    return decode_data(data, pickup_entries)
