from typing import List, Callable, TypeVar, Tuple, Dict, Optional

from randovania.game_description.area import Area
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.dock import DockWeakness, DockType, DockWeaknessDatabase
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import GenericNode, DockNode, TeleporterNode, PickupNode, EventNode, Node, \
    is_resource_node, DockConnection
from randovania.game_description.requirements import IndividualRequirement, RequirementList, RequirementSet
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import SimpleResourceInfo, DamageReduction, DamageResourceInfo, PickupIndex, \
    ResourceDatabase, find_resource_info_with_id, ResourceGainTuple, ResourceInfo
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList

X = TypeVar('X')
Y = TypeVar('Y')


def read_array(data: List[Y], item_reader: Callable[[Y], X]) -> List[X]:
    return [item_reader(item) for item in data]


def read_resource_info(data: Dict, resource_type: ResourceType) -> SimpleResourceInfo:
    return SimpleResourceInfo(data["index"], data["long_name"],
                              data["short_name"], resource_type)


def read_resource_info_array(data: List[Dict], resource_type: ResourceType) -> List[SimpleResourceInfo]:
    return read_array(data, lambda info: read_resource_info(info, resource_type=resource_type))


# Damage

def read_damage_reduction(data: Dict, items: List[SimpleResourceInfo]) -> DamageReduction:
    return DamageReduction(find_resource_info_with_id(items, data["index"]),
                           data["multiplier"])


def read_damage_reductions(data: List[Dict], items: List[SimpleResourceInfo]) -> Tuple[DamageReduction, ...]:
    return tuple(read_array(data, lambda info: read_damage_reduction(info, items)))


def read_damage_resource_info(data: Dict, items: List[SimpleResourceInfo]) -> DamageResourceInfo:
    return DamageResourceInfo(data["index"], data["long_name"],
                              data["short_name"],
                              read_damage_reductions(data["reductions"], items))


def read_damage_resource_info_array(data: List[Dict], items: List[SimpleResourceInfo]) -> List[DamageResourceInfo]:
    return read_array(data, lambda info: read_damage_resource_info(info, items))


# Requirement


def read_individual_requirement(data: Dict, resource_database: ResourceDatabase
                                ) -> IndividualRequirement:
    return IndividualRequirement.with_data(
        resource_database,
        ResourceType(data["requirement_type"]), data["requirement_index"],
        data["amount"], data["negate"])


def read_requirement_list(data: List[Dict],
                          resource_database: ResourceDatabase,
                          ) -> Optional[RequirementList]:
    individuals = read_array(data, lambda x: read_individual_requirement(x, resource_database=resource_database))
    return RequirementList.without_misc_resources(individuals, resource_database)


def read_requirement_set(data: List[List[Dict]],
                         resource_database: ResourceDatabase) -> RequirementSet:
    alternatives = read_array(data, lambda x: read_requirement_list(x, resource_database=resource_database))
    return RequirementSet(alternative for alternative in alternatives if alternative is not None)


# Resource Gain

def read_single_resource_gain(item: Dict, database: "ResourceDatabase") -> Tuple[ResourceInfo, int]:
    resource = database.get_by_type_and_index(ResourceType(item["resource_type"]),
                                              item["resource_index"])
    amount = item["amount"]

    return resource, amount


def read_resource_gain_tuple(data: List[Dict], database: "ResourceDatabase") -> ResourceGainTuple:
    return tuple(
        read_single_resource_gain(item, database)
        for item in data
    )


# Dock Weakness

def read_dock_weakness(item: Dict, resource_database: ResourceDatabase, dock_type: DockType) -> DockWeakness:
    return DockWeakness(item["index"],
                        item["name"],
                        item["is_blast_door"],
                        read_requirement_set(item["requirement_set"], resource_database),
                        dock_type)


def read_dock_weakness_database(data: Dict,
                                resource_database: ResourceDatabase,
                                ) -> DockWeaknessDatabase:
    door_types = read_array(data["door"], lambda item: read_dock_weakness(item, resource_database, DockType.DOOR))
    portal_types = read_array(data["portal"], lambda item: read_dock_weakness(item, resource_database, DockType.PORTAL))

    return DockWeaknessDatabase(
        door=door_types,
        morph_ball=[
            DockWeakness(0, "Morph Ball Door", False, RequirementSet.trivial(), DockType.MORPH_BALL_DOOR)
        ],
        other=[
            DockWeakness(0, "Other Door", False, RequirementSet.trivial(), DockType.OTHER)
        ],
        portal=portal_types)


class WorldReader:
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    generic_index: int = 0

    def __init__(self,
                 resource_database: ResourceDatabase,
                 dock_weakness_database: DockWeaknessDatabase,
                 add_self_as_requirement_to_resources: bool,
                 ):

        self.resource_database = resource_database
        self.dock_weakness_database = dock_weakness_database
        self.add_self_as_requirement_to_resources = add_self_as_requirement_to_resources

    def read_node(self, data: Dict) -> Node:
        name: str = data["name"]
        heal: bool = data["heal"]
        node_type: int = data["node_type"]

        if node_type == 0:
            self.generic_index += 1
            return GenericNode(name, heal, self.generic_index)

        elif node_type == 1:
            return DockNode(name, heal, data["dock_index"],
                            DockConnection(data["connected_area_asset_id"], data["connected_dock_index"]),
                            self.dock_weakness_database.get_by_type_and_index(DockType(data["dock_type"]),
                                                                              data["dock_weakness_index"]))

        elif node_type == 2:
            return PickupNode(name, heal, PickupIndex(data["pickup_index"]))

        elif node_type == 3:
            instance_id = data["teleporter_instance_id"]

            destination_world_asset_id = data["destination_world_asset_id"]
            destination_area_asset_id = data["destination_area_asset_id"]

            return TeleporterNode(name, heal, instance_id,
                                  AreaLocation(destination_world_asset_id, destination_area_asset_id))

        elif node_type == 4:
            return EventNode(name, heal,
                             self.resource_database.get_by_type_and_index(ResourceType.EVENT, data["event_index"]))

        else:
            raise Exception("Unknown node type: {}".format(node_type))

    def read_area(self, data: Dict) -> Area:
        name = data["name"]
        nodes = read_array(data["nodes"], self.read_node)
        nodes_by_name = {node.name: node for node in nodes}

        connections = {}
        for i, origin_data in enumerate(data["nodes"]):
            origin = nodes[i]
            connections[origin] = {}

            extra_requirement = None
            if is_resource_node(origin) and self.add_self_as_requirement_to_resources:
                extra_requirement = RequirementList.with_single_resource(origin.resource())

            for target_name, target_requirements in origin_data["connections"].items():
                the_set = read_requirement_set(target_requirements, self.resource_database)
                if extra_requirement is not None:
                    the_set = the_set.union(RequirementSet([extra_requirement]))

                if the_set != RequirementSet.impossible():
                    connections[origin][nodes_by_name[target_name]] = the_set

        return Area(name, data["asset_id"], data["default_node_index"], nodes,
                    connections)

    def read_area_list(self, data: List[Dict]) -> List[Area]:
        return read_array(data, self.read_area)

    def read_world(self, data: Dict) -> World:
        return World(data["name"], data["asset_id"],
                     self.read_area_list(data["areas"]))

    def read_world_list(self, data: List[Dict]) -> WorldList:
        return WorldList(read_array(data, self.read_world))


def read_resource_database(data: Dict) -> ResourceDatabase:
    item = read_resource_info_array(data["items"], ResourceType.ITEM)
    return ResourceDatabase(
        item=item,
        event=read_resource_info_array(data["events"], ResourceType.EVENT),
        trick=read_resource_info_array(data["tricks"], ResourceType.TRICK),
        damage=read_damage_resource_info_array(data["damage"], item),
        version=read_resource_info_array(data["versions"], ResourceType.VERSION),
        misc=read_resource_info_array(data["misc"], ResourceType.MISC),
        difficulty=read_resource_info_array(data["difficulty"], ResourceType.DIFFICULTY),
    )


def read_initial_states(data: Dict[str, List], resource_database: ResourceDatabase) -> Dict[str, ResourceGainTuple]:
    return {
        name: read_resource_gain_tuple(item, resource_database)
        for name, item in data.items()
    }


def decode_data_with_world_reader(data: Dict,
                                  add_self_as_requirement_to_resources: bool,
                                  ) -> Tuple[WorldReader, GameDescription]:
    game = data["game"]
    game_name = data["game_name"]

    resource_database = read_resource_database(data["resource_database"])
    dock_weakness_database = read_dock_weakness_database(data["dock_weakness_database"], resource_database)

    world_reader = WorldReader(resource_database, dock_weakness_database, add_self_as_requirement_to_resources)
    world_list = world_reader.read_world_list(data["worlds"])

    victory_condition = read_requirement_set(data["victory_condition"], resource_database)
    starting_location = AreaLocation.from_json(data["starting_location"])
    initial_states = read_initial_states(data["initial_states"], resource_database)

    return world_reader, GameDescription(
        game=game,
        game_name=game_name,
        resource_database=resource_database,
        dock_weakness_database=dock_weakness_database,
        world_list=world_list,
        victory_condition=victory_condition,
        starting_location=starting_location,
        initial_states=initial_states,
        add_self_as_requirement_to_resources=add_self_as_requirement_to_resources,
    )


def decode_data(data: Dict, add_self_as_requirement_to_resources: bool = True) -> GameDescription:
    return decode_data_with_world_reader(data, add_self_as_requirement_to_resources)[1]
