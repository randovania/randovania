import collections
import dataclasses
import re
import typing
from typing import DefaultDict

from randovania.game_description import data_reader, data_writer
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.world_list import WorldList
from randovania.generator.item_pool import pool_creator, PoolResults
from randovania.layout import filtered_database
from randovania.layout.base.base_configuration import BaseConfiguration

_ETM_NAME = "Energy Transfer Module"


def _pickup_assignment_to_item_locations(world_list: WorldList,
                                         pickup_assignment: PickupAssignment,
                                         num_players: int,
                                         ) -> dict[str, dict[str, str]]:
    items_locations: DefaultDict[str, dict[str, str]] = collections.defaultdict(dict)

    for world, area, node in world_list.all_worlds_areas_nodes:
        if not node.is_resource_node or not isinstance(node, PickupNode):
            continue

        if node.pickup_index in pickup_assignment:
            target = pickup_assignment[node.pickup_index]
            if num_players > 1:
                item_name = f"{target.pickup.name} for Player {target.player + 1}"
            else:
                item_name = f"{target.pickup.name}"
        else:
            item_name = _ETM_NAME

        world_name = world.dark_name if area.in_dark_aether else world.name
        items_locations[world_name][world_list.node_name(node)] = item_name

    return {
        world: {
            area: item
            for area, item in sorted(items_locations[world].items())
        }
        for world in sorted(items_locations.keys())
    }


def _find_area_with_teleporter(world_list: WorldList, teleporter: NodeIdentifier) -> Area:
    return world_list.area_by_area_location(teleporter.area_location)


def serialize_single(player_index: int, num_players: int, patches: GamePatches) -> dict:
    """
    Encodes a given GamePatches into a JSON-serializable dict.
    :param player_index:
    :param num_players:
    :param patches:
    :return:
    """
    game = filtered_database.game_description_for_layout(patches.configuration)
    world_list = game.world_list

    dock_weakness_to_type = {}
    for dock_type, weaknesses in game.dock_weakness_database.weaknesses.items():
        for weakness in weaknesses.values():
            dock_weakness_to_type[weakness] = dock_type

    result = {
        # This field helps schema migrations, if nothing else
        "game": patches.configuration.game.value,
        "starting_location": patches.starting_location.as_string,
        "starting_items": {
            resource_info.long_name: quantity
            for resource_info, quantity in patches.starting_items.as_resource_gain()
        },
        "teleporters": {
            source.identifier.as_string: connection.as_string
            for source, connection in patches.all_elevator_connections()
        },
        "dock_weakness": {
            dock.identifier.as_string: {
                "type": dock_weakness_to_type[weakness].short_name,
                "name": weakness.name,
            }
            for dock, weakness in patches.all_dock_weaknesses()
        },
        "configurable_nodes": {
            identifier.as_string: data_writer.write_requirement(requirement)
            for identifier, requirement in patches.configurable_nodes.items()
        },
        "locations": {
            key: value
            for key, value in _pickup_assignment_to_item_locations(world_list,
                                                                   patches.pickup_assignment,
                                                                   num_players).items()
        },
        "hints": {
            identifier.as_string: hint.as_json
            for identifier, hint in patches.hints.items()
        }
    }
    return result


def _area_name_to_area_location(world_list: WorldList, area_name: str) -> AreaIdentifier:
    world_name, area_name = re.match("([^/]+)/([^/]+)", area_name).group(1, 2)

    # Filter out dark world names
    world_name = world_list.world_with_name(world_name).name

    return AreaIdentifier(world_name, area_name)


def _find_pickup_with_name(item_pool: list[PickupEntry], pickup_name: str) -> PickupEntry:
    for pickup in item_pool:
        if pickup.name == pickup_name:
            return pickup

    names = {pickup.name for pickup in item_pool}
    raise ValueError(f"Unable to find a pickup with name {pickup_name}. Possible values: {sorted(names)}")


def decode_single(player_index: int, all_pools: dict[int, PoolResults], game: GameDescription,
                  game_modifications: dict, configuration: BaseConfiguration) -> GamePatches:
    """
    Decodes a dict created by `serialize` back into a GamePatches.
    :param player_index:
    :param all_pools:
    :param game:
    :param game_modifications:
    :param configuration:
    :return:
    """
    world_list = game.world_list
    weakness_db = game.dock_weakness_database

    if game_modifications["game"] != game.game.value:
        raise ValueError(f"Expected '{game.game.value}', got '{game_modifications['game']}'")

    initial_pickup_assignment = all_pools[player_index].assignment

    # Starting Location
    starting_location = AreaIdentifier.from_string(game_modifications["starting_location"])

    # Initial items
    starting_items = ResourceCollection.from_dict(game.resource_database, {
        find_resource_info_with_long_name(game.resource_database.item, resource_name): quantity
        for resource_name, quantity in game_modifications["starting_items"].items()
    })

    # Elevators
    elevator_connection = [
        (world_list.get_teleporter_node(NodeIdentifier.from_string(source_name)),
         AreaIdentifier.from_string(target_name))
        for source_name, target_name in game_modifications["teleporters"].items()
    ]

    # Dock Weakness
    def get_dock(ni: NodeIdentifier):
        result = game.world_list.node_by_identifier(ni)
        assert isinstance(result, DockNode)
        return result

    dock_weakness = [
        (get_dock(NodeIdentifier.from_string(source_name)),
         weakness_db.get_by_weakness(
             weakness_data["type"],
             weakness_data["name"],
         ))
        for source_name, weakness_data in game_modifications["dock_weakness"].items()
    ]

    # Configurable Nodes
    configurable_nodes = {
        NodeIdentifier.from_string(identifier): data_reader.read_requirement(requirement, game.resource_database)
        for identifier, requirement in game_modifications["configurable_nodes"].items()
    }

    # Pickups
    target_name_re = re.compile(r"(.*) for Player (\d+)")

    pickup_assignment: PickupAssignment = {}
    for world_name, world_data in game_modifications["locations"].items():
        for area_node_name, target_name in typing.cast(dict[str, str], world_data).items():
            if target_name == _ETM_NAME:
                continue

            pickup_name_match = target_name_re.match(target_name)
            if pickup_name_match is not None:
                pickup_name = pickup_name_match.group(1)
                target_player = int(pickup_name_match.group(2)) - 1
            else:
                pickup_name = target_name
                target_player = 0

            node_identifier = NodeIdentifier.create(world_name, *area_node_name.split("/", 1))
            node = world_list.node_by_identifier(node_identifier)
            assert isinstance(node, PickupNode)
            if node.pickup_index in initial_pickup_assignment:
                pickup = initial_pickup_assignment[node.pickup_index]
                if (pickup_name, target_player) != (pickup.name, player_index):
                    raise ValueError(f"{area_node_name} should be vanilla based on configuration")

            elif pickup_name != _ETM_NAME:
                configuration_item_pool = all_pools[target_player].pickups
                pickup = _find_pickup_with_name(configuration_item_pool, pickup_name)
                configuration_item_pool.remove(pickup)
            else:
                pickup = None

            if pickup is not None:
                pickup_assignment[node.pickup_index] = PickupTarget(pickup, target_player)

    # Hints
    hints = {}
    for identifier_str, hint in game_modifications["hints"].items():
        hints[NodeIdentifier.from_string(identifier_str)] = Hint.from_json(hint)

    patches = GamePatches.create_from_game(game, player_index, configuration)
    patches = patches.assign_dock_weakness(dock_weakness)
    patches = patches.assign_elevators(elevator_connection)
    return dataclasses.replace(
        patches,
        pickup_assignment=pickup_assignment,  # PickupAssignment
        configurable_nodes=configurable_nodes,
        starting_items=starting_items,  # ResourceGainTuple
        starting_location=starting_location,  # AreaIdentifier
        hints=hints,
    )


def decode(game_modifications: list[dict],
           layout_configurations: dict[int, BaseConfiguration],
           ) -> dict[int, GamePatches]:
    all_games = {index: filtered_database.game_description_for_layout(configuration)
                 for index, configuration in layout_configurations.items()}
    all_pools = {index: pool_creator.calculate_pool_results(configuration, all_games[index])
                 for index, configuration in layout_configurations.items()}
    return {
        index: decode_single(index, all_pools, all_games[index], modifications, layout_configurations[index])
        for index, modifications in enumerate(game_modifications)
    }


def serialize(all_patches: dict[int, GamePatches]) -> list[dict]:
    return [
        serialize_single(index, len(all_patches), patches)
        for index, patches in all_patches.items()
    ]
