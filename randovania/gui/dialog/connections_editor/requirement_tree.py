from __future__ import annotations

from typing import Any, cast

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType

from .path import Path


def tuple_insert(items: tuple, idx: int, value: Any) -> tuple:
    return (*items[:idx], value, *items[idx:])


def tuple_remove(items: tuple, idx: int) -> tuple:
    return (*items[:idx], *items[idx + 1 :])


def tuple_replace(items: tuple, idx: int, value: Any) -> tuple:
    return (*items[:idx], value, *items[idx + 1 :])


def insert_at_path(root: RequirementArrayBase, path: Path, requirement: Requirement) -> Requirement:
    if len(path) == 1:
        new_items = tuple_insert(root.items, path.row(), requirement)
        return type(root)(new_items, root.comment)

    idx = path.head()
    next_root = cast(RequirementArrayBase, root.items[idx])
    child = insert_at_path(next_root, path.tail(), requirement)
    new_items = tuple_replace(root.items, idx, child)
    return type(root)(new_items, root.comment)


def remove_at_path(root: RequirementArrayBase, path: Path) -> Requirement:
    idx = path.head()

    if len(path) == 1:
        new_items = tuple_remove(root.items, idx)
        return type(root)(new_items, root.comment)

    next_root = cast(RequirementArrayBase, root.items[idx])
    child = remove_at_path(next_root, path.tail())
    new_items = tuple_replace(root.items, idx, child)
    return type(root)(new_items, root.comment)


def replace_at_path(root: RequirementArrayBase, path: Path, requirement: Requirement) -> Requirement:
    if len(path) == 0:
        return requirement

    next_root = root.items[path.head()]
    child = (
        requirement
        if not isinstance(next_root, RequirementArrayBase)
        else replace_at_path(next_root, path.tail(), requirement)
    )

    new_items = tuple_replace(root.items, path.head(), child)
    return type(root)(new_items, root.comment)


def default_from_type(
    from_type: ResourceType | type[Requirement], db: ResourceDatabase, region_list: RegionList
) -> Requirement:
    if isinstance(from_type, ResourceType):
        resource_info: ResourceInfo = next(iter(db.get_by_type(from_type)))
        return ResourceRequirement.simple(resource_info)

    if issubclass(from_type, RequirementArrayBase):
        print("Hello")
        return RequirementAnd([], None)

    if from_type == RequirementTemplate:
        template_name = next(iter(db.requirement_template))
        return RequirementTemplate(template_name)

    if from_type == NodeRequirement:
        node_id: NodeIdentifier = next(region_list.iterate_nodes()).identifier
        return NodeRequirement(node_id)

    raise RuntimeError(f"Unknown requirement type: {from_type}")


def change_to_type(current: Requirement, to_type: type, db: ResourceDatabase, region_list: RegionList) -> Requirement:
    """Wrapper to retain data when changing between array types"""
    if isinstance(current, RequirementArrayBase) and issubclass(type(to_type), RequirementArrayBase):
        return to_type(current.items, current.comment)
    return default_from_type(to_type, db, region_list)


def _at_path(requirement: Requirement, path: Path) -> Requirement:
    if len(path) == 0:
        return requirement
    return _at_path(cast(RequirementArrayBase, requirement).items[path.head()], path.tail())
