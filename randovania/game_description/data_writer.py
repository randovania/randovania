from __future__ import annotations

import copy
import re
from typing import TYPE_CHECKING, TypeVar

from randovania.game_description import game_migration
from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node import GenericNode, Node
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.teleporter_network_node import TeleporterNetworkNode
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.lib import frozen_lib, json_lib

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from pathlib import Path

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.dock import DockLock, DockRandoParams, DockWeakness, DockWeaknessDatabase
    from randovania.game_description.db.region import Region
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription, MinimalLogicData
    from randovania.game_description.requirements.array_base import RequirementArrayBase
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceGainTuple, ResourceInfo
    from randovania.game_description.resources.resource_type import ResourceType
    from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
    from randovania.game_description.resources.trick_resource_info import TrickResourceInfo

    _Resource = TypeVar("_Resource", SimpleResourceInfo, ItemResourceInfo, TrickResourceInfo)

REGION_NAME_TO_FILE_NAME_RE = re.compile(r"[^a-zA-Z0-9\- ]")


def write_resource_requirement(requirement: ResourceRequirement) -> dict:
    return {
        "type": "resource",
        "data": {
            "type": requirement.resource.resource_type.as_string,
            "name": requirement.resource.short_name,
            "amount": requirement.amount,
            "negate": requirement.negate,
        },
    }


def write_requirement_array(requirement: RequirementArrayBase, type_name: str) -> dict:
    return {
        "type": type_name,
        "data": {"comment": requirement.comment, "items": [write_requirement(item) for item in requirement.items]},
    }


def write_requirement_template(requirement: RequirementTemplate) -> dict:
    return {"type": "template", "data": requirement.template_name}


def write_requirement(requirement: Requirement) -> dict:
    if isinstance(requirement, ResourceRequirement):
        return write_resource_requirement(requirement)

    elif isinstance(requirement, RequirementOr):
        return write_requirement_array(requirement, "or")

    elif isinstance(requirement, RequirementAnd):
        return write_requirement_array(requirement, "and")

    elif isinstance(requirement, RequirementTemplate):
        return write_requirement_template(requirement)

    else:
        raise ValueError(f"Unknown requirement type: {type(requirement)}")


def write_optional_requirement(requirement: Requirement | None) -> dict | None:
    if requirement is None:
        return None
    else:
        return write_requirement(requirement)


# Resource


def write_resource_gain(resource_gain: ResourceGain) -> list:
    def sorter(item: tuple[ResourceInfo, int]) -> tuple[ResourceType, str, int]:
        return item[0].resource_type, item[0].short_name, item[1]

    return [
        {
            "resource_type": resource.resource_type.as_string,
            "resource_name": resource.short_name,
            "amount": gain,
        }
        for resource, gain in sorted(resource_gain, key=sorter)
    ]


def write_simple_resource(resource: SimpleResourceInfo) -> dict:
    return {
        "long_name": resource.long_name,
        "extra": frozen_lib.unwrap(resource.extra),
    }


def write_item_resource(resource: ItemResourceInfo) -> dict:
    return {
        "long_name": resource.long_name,
        "max_capacity": resource.max_capacity,
        "extra": frozen_lib.unwrap(resource.extra),
    }


def write_trick_resource(resource: TrickResourceInfo) -> dict:
    return {
        "long_name": resource.long_name,
        "description": resource.description,
        "extra": frozen_lib.unwrap(resource.extra),
    }


def write_array(array: list[_Resource], writer: Callable[[_Resource], dict]) -> dict:
    return {item.short_name: writer(item) for item in array}


def check_for_duplicated_index(array: Iterable[ResourceInfo], field: str) -> Iterator[str]:
    indices_seen = set()
    for item in array:
        if getattr(item, field) in indices_seen:
            yield f"Duplicated index {getattr(item, field)} with {item.long_name}"
        else:
            indices_seen.add(getattr(item, field))


def write_resource_database(resource_database: ResourceDatabase) -> dict:
    errors: list[str] = []

    for array in (
        resource_database.item,
        resource_database.event,
        resource_database.trick,
        resource_database.damage,
        resource_database.version,
        resource_database.misc,
    ):
        assert isinstance(array, list)
        errors.extend(check_for_duplicated_index(array, "short_name"))

    if errors:
        raise ValueError("Errors in resource database: {}".format("\n".join(errors)))

    return {
        "items": write_array(resource_database.item, write_item_resource),
        "events": write_array(resource_database.event, write_simple_resource),
        "tricks": write_array(resource_database.trick, write_trick_resource),
        "damage": write_array(resource_database.damage, write_simple_resource),
        "versions": write_array(resource_database.version, write_simple_resource),
        "misc": write_array(resource_database.misc, write_simple_resource),
        "requirement_template": {
            name: {
                "display_name": requirement.display_name,
                "requirement": write_requirement(requirement.requirement),
            }
            for name, requirement in resource_database.requirement_template.items()
        },
        "damage_reductions": [
            {
                "name": resource.short_name,
                "reductions": [
                    {
                        "name": reduction.inventory_item.short_name if reduction.inventory_item is not None else None,
                        "multiplier": reduction.damage_multiplier,
                    }
                    for reduction in reductions
                ],
            }
            for resource, reductions in resource_database.damage_reductions.items()
        ],
        "energy_tank_item_index": resource_database.energy_tank_item.short_name,
    }


# Dock Weakness Database


def write_dock_lock(dock_lock: DockLock | None) -> dict | None:
    if dock_lock is None:
        return None

    return {"lock_type": dock_lock.lock_type.value, "requirement": write_requirement(dock_lock.requirement)}


def write_dock_weakness(dock_weakness: DockWeakness) -> dict:
    return {
        "extra": frozen_lib.unwrap(dock_weakness.extra),
        "requirement": write_requirement(dock_weakness.requirement),
        "lock": write_dock_lock(dock_weakness.lock),
    }


def write_dock_rando_params(dock_rando: DockRandoParams) -> dict:
    return {
        "unlocked": dock_rando.unlocked.name,
        "locked": dock_rando.locked.name,
        "change_from": sorted(weakness.name for weakness in dock_rando.change_from),
        "change_to": sorted(weakness.name for weakness in dock_rando.change_to),
    }


def write_dock_weakness_database(database: DockWeaknessDatabase) -> dict:
    return {
        "types": {
            dock_type.short_name: {
                "name": dock_type.long_name,
                "extra": frozen_lib.unwrap(dock_type.extra),
                "items": {
                    name: write_dock_weakness(weakness) for name, weakness in database.weaknesses[dock_type].items()
                },
                "dock_rando": (
                    write_dock_rando_params(database.dock_rando_params[dock_type])
                    if dock_type in database.dock_rando_params
                    else None
                ),
            }
            for dock_type in database.dock_types
        },
        "default_weakness": {
            "type": database.default_weakness[0].short_name,
            "name": database.default_weakness[1].name,
        },
        "dock_rando": {
            "force_change_two_way": database.dock_rando_config.force_change_two_way,
            "resolver_attempts": database.dock_rando_config.resolver_attempts,
            "to_shuffle_proportion": database.dock_rando_config.to_shuffle_proportion,
        },
    }


# Region/Area/Nodes


def write_node(node: Node) -> dict:
    """
    :param node:
    :return:
    """

    data: dict = {}
    common_fields = {
        "heal": node.heal,
        "coordinates": {"x": node.location.x, "y": node.location.y, "z": node.location.z} if node.location else None,
        "description": node.description,
        "layers": frozen_lib.unwrap(node.layers),
        "extra": frozen_lib.unwrap(node.extra),
        "valid_starting_location": frozen_lib.unwrap(node.valid_starting_location),
    }

    if isinstance(node, GenericNode):
        data["node_type"] = "generic"
        data.update(common_fields)

    elif isinstance(node, DockNode):
        data["node_type"] = "dock"
        data.update(common_fields)
        data["dock_type"] = node.dock_type.short_name
        data["default_connection"] = node.default_connection.as_json
        data["default_dock_weakness"] = node.default_dock_weakness.name
        data["exclude_from_dock_rando"] = node.exclude_from_dock_rando
        data["incompatible_dock_weaknesses"] = [weak.name for weak in node.incompatible_dock_weaknesses]
        data["override_default_open_requirement"] = write_optional_requirement(node.override_default_open_requirement)
        data["override_default_lock_requirement"] = write_optional_requirement(node.override_default_lock_requirement)

    elif isinstance(node, PickupNode):
        data["node_type"] = "pickup"
        data.update(common_fields)
        data["pickup_index"] = node.pickup_index.index
        data["location_category"] = node.location_category.value

    elif isinstance(node, EventNode):
        data["node_type"] = "event"
        data.update(common_fields)
        data["event_name"] = node.event.short_name

    elif isinstance(node, ConfigurableNode):
        data["node_type"] = "configurable_node"
        data.update(common_fields)

    elif isinstance(node, HintNode):
        data["node_type"] = "hint"
        data.update(common_fields)
        data["kind"] = node.kind.value
        data["requirement_to_collect"] = write_requirement(node.requirement_to_collect)

    elif isinstance(node, TeleporterNetworkNode):
        data["node_type"] = "teleporter_network"
        data.update(common_fields)
        data["is_unlocked"] = write_requirement(node.is_unlocked)
        data["network"] = node.network
        data["requirement_to_activate"] = write_requirement(node.requirement_to_activate)

    else:
        raise ValueError(f"Unknown node class: {node}")

    return data


def write_area(area: Area) -> dict:
    """
    :param area:
    :return:
    """
    errors = []

    nodes = {}
    for node in area.nodes:
        if node.is_derived_node:
            continue
        try:
            data = write_node(node)
            data["connections"] = {
                target_node.name: write_requirement(area.connections[node][target_node])
                for target_node in area.nodes
                if not target_node.is_derived_node and target_node in area.connections[node]
            }
            nodes[node.name] = data
        except ValueError as e:
            errors.append(str(e))

    if errors:
        raise ValueError("Area {} nodes has the following errors:\n* {}".format(area.name, "\n* ".join(errors)))

    extra = frozen_lib.unwrap(area.extra)
    return {
        "default_node": area.default_node,
        "extra": extra,
        "nodes": nodes,
    }


def write_region(region: Region) -> dict:
    errors = []
    areas = {}
    for area in region.areas:
        try:
            areas[area.name] = write_area(area)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        raise ValueError("Region {} has the following errors:\n> {}".format(region.name, "\n\n> ".join(errors)))

    return {
        "name": region.name,
        "extra": frozen_lib.unwrap(region.extra),
        "areas": areas,
    }


def write_region_list(region_list: RegionList) -> list:
    errors = []
    known_indices: dict[PickupIndex, str] = {}

    regions = []
    for region in region_list.regions:
        try:
            regions.append(write_region(region))

            for node in region.all_nodes:
                if isinstance(node, PickupNode):
                    name = region_list.node_name(node, with_region=True, distinguish_dark_aether=True)
                    if node.pickup_index in known_indices:
                        errors.append(
                            f"{name} has {node.pickup_index}, "
                            f"but it was already used in {known_indices[node.pickup_index]}"
                        )
                    else:
                        known_indices[node.pickup_index] = name

        except ValueError as e:
            errors.append(str(e))

    if errors:
        raise ValueError("\n\n".join(errors))

    return regions


# Game Description


def write_initial_states(initial_states: dict[str, ResourceGainTuple]) -> dict:
    return {name: write_resource_gain(initial_state) for name, initial_state in initial_states.items()}


def write_minimal_logic_db(db: MinimalLogicData | None) -> dict | None:
    if db is None:
        return None

    return {
        "items_to_exclude": [{"name": it.name, "when_shuffled": it.reason} for it in db.items_to_exclude],
        "custom_item_amount": [{"name": index, "value": value} for index, value in db.custom_item_amount.items()],
        "events_to_exclude": [{"name": it.name, "reason": it.reason} for it in db.events_to_exclude],
        "description": db.description,
    }


def write_used_trick_levels(game: GameDescription) -> dict[str, list[int]] | None:
    try:
        return {
            trick.short_name: sorted(levels) for trick, levels in game.get_used_trick_levels(ignore_cache=True).items()
        }
    except (RecursionError, KeyError):
        return None


def write_game_description(game: GameDescription) -> dict:
    return {
        "schema_version": game_migration.CURRENT_VERSION,
        "game": game.game.value,
        "resource_database": write_resource_database(game.resource_database),
        "layers": frozen_lib.unwrap(game.layers),
        "starting_location": game.starting_location.as_json,
        "initial_states": write_initial_states(game.initial_states),
        "minimal_logic": write_minimal_logic_db(game.minimal_logic),
        "victory_condition": write_requirement(game.victory_condition),
        "dock_weakness_database": write_dock_weakness_database(game.dock_weakness_database),
        "used_trick_levels": write_used_trick_levels(game),
        "regions": write_region_list(game.region_list),
    }


def write_as_split_files(data: dict, base_path: Path) -> None:
    data = copy.copy(data)
    regions = data.pop("regions")
    data["regions"] = []

    base_path.mkdir(parents=True, exist_ok=True)

    for region in regions:
        name = REGION_NAME_TO_FILE_NAME_RE.sub(r"", region["name"])
        data["regions"].append(f"{name}.json")
        json_lib.write_path(base_path.joinpath(f"{name}.json"), region, compress=True)

    json_lib.write_path(base_path.joinpath("header.json"), data, compress=True)
