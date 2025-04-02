from __future__ import annotations

import collections
import dataclasses
import re
import typing

from randovania.game_description import default_database
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.game_patches import GamePatches, StartingEquipment
from randovania.game_description.hint import BaseHint
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.generator.pickup_pool import PoolResults, pool_creator
from randovania.layout import filtered_database

if typing.TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.layout.base.base_configuration import BaseConfiguration

_ETM_NAME = "Energy Transfer Module"


def _pickup_assignment_to_item_locations(
    region_list: RegionList,
    pickup_assignment: PickupAssignment,
    num_players: int,
) -> dict[str, dict[str, str]]:
    items_locations: collections.defaultdict[str, dict[str, str]] = collections.defaultdict(dict)

    for region, area, node in region_list.all_regions_areas_nodes:
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

        items_locations[region.correct_name(area.in_dark_aether)][region_list.node_name(node)] = item_name

    return {region: dict(sorted(items_locations[region].items())) for region in sorted(items_locations.keys())}


def _find_area_with_teleporter(region_list: RegionList, teleporter: NodeIdentifier) -> Area:
    return region_list.area_by_area_location(teleporter.area_identifier)


def serialize_single(player_index: int, num_players: int, patches: GamePatches) -> dict:
    """
    Encodes a given GamePatches into a JSON-serializable dict.
    :param player_index:
    :param num_players:
    :param patches:
    :return:
    """
    game = filtered_database.game_description_for_layout(patches.configuration)
    region_list = game.region_list

    dock_weakness_to_type = {}
    for dock_type, weaknesses in game.dock_weakness_database.weaknesses.items():
        for weakness in weaknesses.values():
            dock_weakness_to_type[weakness] = dock_type

    equipment_value: dict | list
    if isinstance(patches.starting_equipment, ResourceCollection):
        equipment_name = "items"
        equipment_value = {
            resource_info.long_name: quantity
            for resource_info, quantity in patches.starting_equipment.as_resource_gain()
        }
    else:
        equipment_name = "pickups"
        equipment_value = [pickup.name for pickup in patches.starting_equipment]

    result: dict = {
        # This field helps schema migrations, if nothing else
        "game": patches.configuration.game.value,
        "starting_equipment": {
            equipment_name: equipment_value,
        },
        "starting_location": patches.starting_location.as_string,
        "dock_connections": {
            dock.identifier.as_string: target.identifier.as_string for dock, target in patches.all_dock_connections()
        },
        "dock_weakness": {
            dock.identifier.as_string: {
                "type": dock_weakness_to_type[weakness].short_name,
                "name": weakness.name,
            }
            for dock, weakness in patches.all_dock_weaknesses()
        },
        "locations": dict(
            _pickup_assignment_to_item_locations(region_list, patches.pickup_assignment, num_players).items()
        ),
        "hints": {identifier.as_string: hint.as_json for identifier, hint in patches.hints.items()},
        "game_specific": patches.game_specific,
    }

    if patches.custom_patcher_data:
        result["custom_patcher_data"] = patches.custom_patcher_data

    return result


def _area_name_to_area_location(region_list: RegionList, area_name: str) -> AreaIdentifier:
    name_match = re.match("([^/]+)/([^/]+)", area_name)
    assert name_match is not None
    region_name, area_name = name_match.group(1, 2)

    # Filter out dark db names
    region_name = region_list.region_with_name(region_name).name

    return AreaIdentifier(region_name, area_name)


def _find_pickup_with_name(item_pool: list[PickupEntry], pickup_name: str) -> PickupEntry:
    for pickup in item_pool:
        if pickup.name == pickup_name:
            return pickup

    names = {pickup.name for pickup in item_pool}
    raise ValueError(f"Unable to find a pickup with name {pickup_name}. Possible values: {sorted(names)}")


def _get_pickup_from_pool(pickup_list: list[PickupEntry], name: str) -> PickupEntry:
    pickup = _find_pickup_with_name(pickup_list, name)
    pickup_list.remove(pickup)
    return pickup


def _decode_pickup_assignment(
    player_index: int,
    all_pools: dict[int, PoolResults],
    region_list: RegionList,
    locations: dict,
) -> PickupAssignment:
    """Decodes the `locations` key."""
    target_name_re = re.compile(r"(.*) for Player (\d+)")

    pickup_assignment: PickupAssignment = {}

    initial_pickup_assignment = all_pools[player_index].assignment

    for world_name, world_data in locations.items():
        for area_node_name, target_name in typing.cast("dict[str, str]", world_data).items():
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
            node = region_list.typed_node_by_identifier(node_identifier, PickupNode)
            pickup: PickupEntry | None

            if node.pickup_index in initial_pickup_assignment:
                pickup = initial_pickup_assignment[node.pickup_index]
                if (pickup_name, target_player) != (pickup.name, player_index):
                    raise ValueError(f"{area_node_name} should be vanilla based on configuration")

            elif pickup_name != _ETM_NAME:
                pickup = _get_pickup_from_pool(all_pools[target_player].to_place, pickup_name)
            else:
                pickup = None

            if pickup is not None:
                pickup_assignment[node.pickup_index] = PickupTarget(pickup, target_player)

    return pickup_assignment


def decode_single(
    player_index: int,
    all_pools: dict[int, PoolResults],
    game: GameDescription,
    game_modifications: dict,
    configuration: BaseConfiguration,
    all_games: dict[int, GameDescription],
) -> GamePatches:
    """
    Decodes a dict created by `serialize` back into a GamePatches.
    :param player_index:
    :param all_pools:
    :param game:
    :param game_modifications:
    :param configuration:
    :param all_games:
    :return:
    """
    region_list = game.region_list
    weakness_db = game.dock_weakness_database

    if game_modifications["game"] != game.game.value:
        raise ValueError(f"Expected '{game.game.value}', got '{game_modifications['game']}'")

    if "custom_patcher_data" in game_modifications:
        custom_patcher_data = game_modifications["custom_patcher_data"]
    else:
        custom_patcher_data = []

    game_specific = game_modifications["game_specific"]

    # Starting Location
    starting_location = NodeIdentifier.from_string(game_modifications["starting_location"])

    # Starting Equipment
    starting_equipment: StartingEquipment
    if "items" in game_modifications["starting_equipment"]:
        starting_equipment = ResourceCollection.from_dict(
            game.resource_database,
            {
                find_resource_info_with_long_name(game.resource_database.item, resource_name): quantity
                for resource_name, quantity in game_modifications["starting_equipment"]["items"].items()
            },
        )
    else:
        player_pool = all_pools[player_index]
        starting_equipment = []
        for starting in game_modifications["starting_equipment"]["pickups"]:
            try:
                pickup = _get_pickup_from_pool(player_pool.starting, starting)
            except ValueError:
                pickup = _get_pickup_from_pool(player_pool.to_place, starting)
            starting_equipment.append(pickup)

    # Dock Connection
    def get_dock_source(ni: NodeIdentifier) -> DockNode:
        return game.region_list.typed_node_by_identifier(ni, DockNode)

    def get_dock_target(ni: NodeIdentifier) -> Node:
        return game.region_list.node_by_identifier(ni)

    dock_connections = [
        (
            get_dock_source(NodeIdentifier.from_string(source_name)),
            get_dock_target(NodeIdentifier.from_string(target_name)),
        )
        for source_name, target_name in game_modifications["dock_connections"].items()
    ]

    # Dock Weakness

    dock_weakness = [
        (
            get_dock_source(NodeIdentifier.from_string(source_name)),
            weakness_db.get_by_weakness(
                weakness_data["type"],
                weakness_data["name"],
            ),
        )
        for source_name, weakness_data in game_modifications["dock_weakness"].items()
    ]

    # Pickups
    pickup_assignment = _decode_pickup_assignment(
        player_index,
        all_pools,
        region_list,
        game_modifications["locations"],
    )

    # Hints
    hints = {}
    for identifier_str, hint in game_modifications["hints"].items():
        extra: dict = {}
        if hint["hint_type"] == "location":
            pickup_db = default_database.pickup_database_for_game(game.game)

            def get_target_pickup_db(target: PickupTarget) -> PickupDatabase:
                target_game = all_games[target.player]
                target_pickup_db = default_database.pickup_database_for_game(target_game.game)
                return target_pickup_db

            if (relative := hint["precision"].get("relative")) is not None:
                if "other_index" in relative:
                    other_target = pickup_assignment.get(PickupIndex(relative["other_index"]))
                    if other_target is not None:
                        extra["other_pickup_db"] = get_target_pickup_db(other_target)
                    else:
                        extra["other_pickup_db"] = pickup_db

            extra["game"] = game
            target = pickup_assignment.get(PickupIndex(hint["target"]))

            if target is not None:
                extra["pickup_db"] = get_target_pickup_db(target)
            else:
                extra["pickup_db"] = pickup_db

        hints[NodeIdentifier.from_string(identifier_str)] = BaseHint.from_json(hint, **extra)

    patches = GamePatches.create_from_game(game, player_index, configuration)
    patches = patches.assign_dock_connections(dock_connections)
    patches = patches.assign_dock_weakness(dock_weakness)
    return dataclasses.replace(
        patches,
        pickup_assignment=pickup_assignment,  # PickupAssignment
        starting_equipment=starting_equipment,
        starting_location=starting_location,  # NodeIdentifier
        hints=hints,
        custom_patcher_data=custom_patcher_data,
        game_specific=game_specific,
    )


def decode(
    game_modifications: list[dict],
    layout_configurations: dict[int, BaseConfiguration],
) -> dict[int, GamePatches]:
    all_games = {
        index: filtered_database.game_description_for_layout(configuration)
        for index, configuration in layout_configurations.items()
    }
    all_pools = {
        index: pool_creator.calculate_pool_results(configuration, all_games[index])
        for index, configuration in layout_configurations.items()
    }
    return {
        index: decode_single(index, all_pools, all_games[index], modifications, layout_configurations[index], all_games)
        for index, modifications in enumerate(game_modifications)
    }


def serialize(all_patches: dict[int, GamePatches]) -> list[dict]:
    return [serialize_single(index, len(all_patches), patches) for index, patches in all_patches.items()]
