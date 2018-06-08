from functools import partial
from typing import List, Callable, TypeVar, Tuple, Dict

from randovania.games.prime.log_parser import Elevator
from randovania.resolver.dock import DockWeakness, DockType, DockWeaknessDatabase
from randovania.resolver.game_description import World, Area, GameDescription
from randovania.resolver.node import GenericNode, DockNode, TeleporterNode, PickupNode, EventNode, Node, \
    is_resource_node
from randovania.resolver.requirements import IndividualRequirement, RequirementList, RequirementSet
from randovania.resolver.resources import SimpleResourceInfo, DamageReduction, DamageResourceInfo, PickupIndex, \
    ResourceGain, PickupEntry, find_resource_info_with_long_name, ResourceType, ResourceDatabase

X = TypeVar('X')
Y = TypeVar('Y')


def read_array(data: List[Y], item_reader: Callable[[Y], X]) -> List[X]:
    return [item_reader(item) for item in data]


def read_damage_reduction(data: Dict) -> DamageReduction:
    return DamageReduction(data["index"], data["multiplier"])


def read_damage_reductions(data: List[Dict]) -> Tuple[DamageReduction, ...]:
    return tuple(read_array(data, read_damage_reduction))


def read_resource_info(data: Dict) -> SimpleResourceInfo:
    return SimpleResourceInfo(data["index"], data["long_name"],
                              data["short_name"])


def read_resource_info_array(data: List[Dict]) -> List[SimpleResourceInfo]:
    return read_array(data, read_resource_info)


def read_damage_resource_info(data: Dict) -> DamageResourceInfo:
    return DamageResourceInfo(data["index"], data["long_name"],
                              data["short_name"],
                              read_damage_reductions(data["reductions"]))


def read_damage_resource_info_array(data: List[Dict]) -> List[DamageResourceInfo]:
    return read_array(data, read_damage_resource_info)


def read_pickup_info_array(data: List[Dict]) -> List[PickupEntry]:
    return read_array(data, lambda pickup: PickupEntry(**pickup))


# Requirement


def read_individual_requirement(data: Dict, resource_database: ResourceDatabase
                                ) -> IndividualRequirement:
    return IndividualRequirement.with_data(
        resource_database,
        ResourceType(data["requirement_type"]), data["requirement_index"],
        data["amount"], data["negate"])


def read_requirement_list(data: List[Dict],
                          resource_database: ResourceDatabase) -> RequirementList:
    return RequirementList(
        read_array(data,
                   partial(
                       read_individual_requirement,
                       resource_database=resource_database)))


def read_requirement_set(data: List[List[Dict]],
                         resource_database: ResourceDatabase) -> RequirementSet:
    return RequirementSet(
        read_array(data,
                   partial(
                       read_requirement_list,
                       resource_database=resource_database)))


def add_requirement_to_set(
        requirement_set: RequirementSet,
        new_requirement: IndividualRequirement) -> RequirementSet:
    return RequirementSet(
        RequirementList(requirement_list.union([new_requirement]))
        for requirement_list in requirement_set.alternatives)


# Dock Weakness


def read_dock_weakness_database(data: Dict,
                                resource_database: ResourceDatabase) -> DockWeaknessDatabase:
    def read_dock_weakness(item: Dict) -> DockWeakness:
        return DockWeakness(item["index"], item["name"], item["is_blast_door"],
                            read_requirement_set(item["requirement_set"],
                                                 resource_database).simplify({}, resource_database))

    door_types = read_array(data["door"], read_dock_weakness)
    portal_types = read_array(data["portal"], read_dock_weakness)
    return DockWeaknessDatabase(
        door=door_types,
        morph_ball=[
            DockWeakness(0, "Morph Ball Door", False, RequirementSet.trivial())
        ],
        other=[DockWeakness(0, "Other Door", False, RequirementSet.trivial())],
        portal=portal_types)


class WorldReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    elevators: Dict[int, Elevator]
    generic_index: int = 0

    def __init__(self,
                 resource_database: ResourceDatabase,
                 dock_weakness_database: DockWeaknessDatabase,
                 elevators: List[Elevator]):
        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database
        self.elevators = {
            elevator.instance_id: elevator
            for elevator in elevators
        }

    def read_node(self, data: Dict) -> Node:
        name = data["name"]
        heal = data["heal"]
        node_type = data["node_type"]

        if node_type == 0:
            self.generic_index += 1
            return GenericNode(name, heal, self.generic_index)

        elif node_type == 1:
            return DockNode(
                name, heal, data["dock_index"],
                data["connected_area_asset_id"], data["connected_dock_index"],
                self.dock_weakness_database.get_by_type_and_index(
                    DockType(data["dock_type"]), data["dock_weakness_index"]))

        elif node_type == 2:
            return PickupNode(name, heal, PickupIndex(data["pickup_index"]))

        elif node_type == 3:
            instance_id = data["teleporter_instance_id"]
            if instance_id in self.elevators:
                elevator = self.elevators[instance_id]
                destination_world_asset_id = elevator.connected_elevator.world_asset_id
                destination_area_asset_id = elevator.connected_elevator.area_asset_id
            else:
                destination_world_asset_id = data["destination_world_asset_id"]
                destination_area_asset_id = data["destination_area_asset_id"]

            return TeleporterNode(name, heal,
                                  destination_world_asset_id,
                                  destination_area_asset_id,
                                  instance_id)

        elif node_type == 4:
            return EventNode(name, heal, data["event_index"])

        else:
            raise Exception("Unknown node type: {}".format(node_type))

    def read_area(self, data: Dict) -> Area:
        name = data["name"]
        nodes = read_array(data["nodes"], self.read_node)

        connections = {}
        for i, origin in enumerate(data["connections"]):
            connections[nodes[i]] = {}
            extra_requirement = None

            if is_resource_node(nodes[i]):
                extra_requirement = IndividualRequirement(
                    nodes[i].resource(self.resource_database),
                    1,
                    False)

            for j, target in enumerate(origin):
                if target:
                    the_set = read_requirement_set(target,
                                                   self.resource_database)
                    if extra_requirement is not None:
                        the_set = add_requirement_to_set(the_set, extra_requirement)
                    connections[nodes[i]][nodes[j]] = the_set

        return Area(name, data["asset_id"], data["default_node_index"], nodes,
                    connections)

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
        difficulty=read_resource_info_array(data["difficulty"]),
        pickups=read_pickup_info_array(data["pickups"])
    )


def _convert_to_resource_gain(data: Dict[str, int], resource_database: ResourceDatabase) -> ResourceGain:
    return [
        (find_resource_info_with_long_name(resource_database.item, resource_long_name), quantity)
        for resource_long_name, quantity in data.items()
    ]


def decode_data(data: Dict, elevators: List[Elevator]) -> GameDescription:
    game = data["game"]
    game_name = data["game_name"]

    resource_database = read_resource_database(data["resource_database"])
    dock_weakness_database = read_dock_weakness_database(data["dock_weakness_database"], resource_database)

    worlds = WorldReader(resource_database,
                         dock_weakness_database,
                         elevators).read_world_list(data["worlds"])

    starting_world_asset_id = data["starting_world_asset_id"]
    starting_area_asset_id = data["starting_area_asset_id"]
    victory_condition = read_requirement_set(data["victory_condition"], resource_database)
    starting_items = _convert_to_resource_gain(data["starting_items"], resource_database)
    item_loss_items = _convert_to_resource_gain(data["item_loss_items"], resource_database)

    return GameDescription(
        game=game,
        game_name=game_name,
        resource_database=resource_database,
        dock_weakness_database=dock_weakness_database,
        worlds=worlds,
        victory_condition=victory_condition,
        starting_world_asset_id=starting_world_asset_id,
        starting_area_asset_id=starting_area_asset_id,
        starting_items=starting_items,
        item_loss_items=item_loss_items,
    )
