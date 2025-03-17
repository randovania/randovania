from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.pickup.pickup_entry import PickupModel
from randovania.game_description.resources import search
from randovania.game_description.resources.resource_type import ResourceType

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.damage_reduction import DamageReduction
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
    from randovania.game_description.resources.trick_resource_info import TrickResourceInfo


def default_base_damage_reduction(db: ResourceDatabase, current_resources: ResourceCollection) -> float:
    return 1.0


_ALL_TYPES = (
    ResourceType.ITEM,
    ResourceType.EVENT,
    ResourceType.TRICK,
    ResourceType.DAMAGE,
    ResourceType.VERSION,
    ResourceType.MISC,
)


@dataclasses.dataclass(frozen=True)
class NamedRequirementTemplate:
    display_name: str
    requirement: Requirement


@dataclasses.dataclass(frozen=True)
class ResourceDatabase:
    game_enum: RandovaniaGame
    item: list[ItemResourceInfo]
    event: list[SimpleResourceInfo]
    trick: list[TrickResourceInfo]
    damage: list[SimpleResourceInfo]
    version: list[SimpleResourceInfo]
    misc: list[SimpleResourceInfo]
    requirement_template: dict[str, NamedRequirementTemplate]
    damage_reductions: dict[SimpleResourceInfo, list[DamageReduction]]
    energy_tank_item: ItemResourceInfo
    base_damage_reduction: Callable[[ResourceDatabase, ResourceCollection], float] = default_base_damage_reduction
    resource_by_index: list[ResourceInfo | None] = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        # Reserve index 0 as a placeholder for things without index
        max_index = max(
            max((resource.resource_index for resource in self.get_by_type(resource_type)), default=0)
            for resource_type in _ALL_TYPES
        )
        self.resource_by_index.clear()
        self.resource_by_index.extend([None] * (max_index + 1))

        for resource_type in _ALL_TYPES:
            for resource in self.get_by_type(resource_type):
                assert resource.resource_type == resource_type
                assert self.resource_by_index[resource.resource_index] is None
                self.resource_by_index[resource.resource_index] = resource

    def get_by_type(
        self,
        resource_type: ResourceType,
    ) -> list[ItemResourceInfo] | list[SimpleResourceInfo] | list[TrickResourceInfo]:
        if resource_type == ResourceType.ITEM:
            return self.item
        elif resource_type == ResourceType.EVENT:
            return self.event
        elif resource_type == ResourceType.TRICK:
            return self.trick
        elif resource_type == ResourceType.DAMAGE:
            return self.damage
        elif resource_type == ResourceType.VERSION:
            return self.version
        elif resource_type == ResourceType.MISC:
            return self.misc
        else:
            raise ValueError(f"Invalid resource_type: {resource_type}")

    def get_by_type_and_index(self, resource_type: ResourceType, name: str) -> ResourceInfo:
        return search.find_resource_info_with_id(
            typing.cast("list[ResourceInfo]", self.get_by_type(resource_type)), name, resource_type
        )

    def get_item(self, short_name: str) -> ItemResourceInfo:
        return search.find_resource_info_with_id(self.item, short_name, ResourceType.ITEM)

    def get_event(self, short_name: str) -> SimpleResourceInfo:
        return search.find_resource_info_with_id(self.event, short_name, ResourceType.EVENT)

    def get_trick(self, short_name: str) -> TrickResourceInfo:
        return search.find_resource_info_with_id(self.trick, short_name, ResourceType.TRICK)

    def get_damage(self, short_name: str) -> SimpleResourceInfo:
        return search.find_resource_info_with_id(self.damage, short_name, ResourceType.DAMAGE)

    def get_item_by_name(self, name: str) -> ItemResourceInfo:
        return search.find_resource_info_with_long_name(self.item, name)

    def get_pickup_model(self, name: str) -> PickupModel:
        return PickupModel(
            game=self.game_enum,
            name=name,
        )

    @property
    def energy_tank(self) -> ItemResourceInfo:
        return self.energy_tank_item

    def get_damage_reduction(self, resource: SimpleResourceInfo, current_resources: ResourceCollection) -> float:
        cached_result = current_resources.get_damage_reduction_cache(resource)
        if cached_result is not None:
            return cached_result

        base_reduction = self.base_damage_reduction(self, current_resources)

        damage_multiplier = 1.0
        for reduction in self.damage_reductions.get(resource, []):
            if reduction.inventory_item is None or current_resources[reduction.inventory_item] > 0:
                damage_multiplier = min(damage_multiplier, reduction.damage_multiplier)

        damage_reduction = damage_multiplier * base_reduction
        current_resources.add_damage_reduction_cache(resource, damage_reduction)

        return damage_reduction

    def first_unused_resource_index(self) -> int:
        return len(self.resource_by_index)
