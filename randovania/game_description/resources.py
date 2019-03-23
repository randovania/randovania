from dataclasses import dataclass
from typing import NamedTuple, Tuple, Union, List, Dict, Iterator, Optional

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resource_type import ResourceType


class SimpleResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    resource_type: ResourceType

    def __str__(self):
        short_resource_name = self.resource_type.short_name
        if short_resource_name is not None:
            return "{}: {}".format(short_resource_name, self.long_name)
        else:
            return self.long_name


class DamageReduction(NamedTuple):
    inventory_item: SimpleResourceInfo
    damage_multiplier: float


class DamageResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    reductions: Tuple[DamageReduction, ...]

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.DAMAGE

    def __str__(self):
        return "Damage {}".format(self.long_name)


class PickupIndex:
    _index: int

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.PICKUP_INDEX

    @property
    def long_name(self) -> str:
        return "PickupIndex {}".format(self._index)

    def __init__(self, index: int):
        self._index = index

    def __lt__(self, other: "PickupIndex") -> bool:
        return self._index < other._index

    def __repr__(self):
        return self.long_name

    def __hash__(self):
        return self._index

    def __eq__(self, other):
        return isinstance(other, PickupIndex) and other._index == self._index

    @property
    def index(self) -> int:
        return self._index


ResourceInfo = Union[SimpleResourceInfo, DamageResourceInfo, PickupIndex]
ResourceQuantity = Tuple[ResourceInfo, int]
ResourceGainTuple = Tuple[ResourceQuantity, ...]
ResourceGain = Iterator[ResourceQuantity]
CurrentResources = Dict[ResourceInfo, int]


@dataclass(frozen=True)
class ConditionalResources:
    name: Optional[str]
    item: Optional[SimpleResourceInfo]
    resources: ResourceGainTuple


@dataclass(frozen=True)
class PickupEntry:
    name: str
    model_index: int
    item_category: ItemCategory
    resources: Tuple[ConditionalResources, ...]
    probability_offset: int = 0

    def __post_init__(self):
        if not isinstance(self.resources, tuple):
            raise ValueError("resources should be a tuple, got {}".format(self.resources))

        if len(self.resources) < 1:
            raise ValueError("resources should have at least 1 value")

        for i, conditional in enumerate(self.resources):
            if not isinstance(conditional, ConditionalResources):
                raise ValueError(f"Resource at {i} should be a ConditionalResources")

            if i == 0:
                if conditional.item is not None:
                    raise ValueError("Resource at 0 should not have a condition")
            else:
                if conditional.item is None:
                    raise ValueError(f"Resource at {i} should have a condition")

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name < other.name

    def resource_gain(self, current_resources) -> ResourceGain:
        last_resource_gain = None

        for conditional in self.resources:
            if conditional.item is None or current_resources.get(conditional.item, 0) > 0:
                last_resource_gain = conditional.resources
            else:
                break

        assert last_resource_gain is not None
        yield from last_resource_gain

    def __str__(self):
        return "Pickup {}".format(self.name)

    @property
    def all_resources(self) -> Iterator[ResourceQuantity]:
        for conditional in self.resources:
            yield from conditional.resources


def find_resource_info_with_id(info_list: List[ResourceInfo], index: int):
    for info in info_list:
        if info.index == index:
            return info
    raise ValueError(
        "Resource with index {} not found in {}".format(index, info_list))


def find_resource_info_with_long_name(info_list: List[ResourceInfo], long_name: str):
    for info in info_list:
        if info.long_name == long_name:
            return info
    raise ValueError(
        "Resource with long_name '{}' not found in {} resources".format(long_name, len(info_list)))


class ResourceDatabase(NamedTuple):
    item: List[SimpleResourceInfo]
    event: List[SimpleResourceInfo]
    trick: List[SimpleResourceInfo]
    damage: List[DamageResourceInfo]
    version: List[SimpleResourceInfo]
    misc: List[SimpleResourceInfo]
    difficulty: List[SimpleResourceInfo]

    def get_by_type(self, resource_type: ResourceType) -> List[ResourceInfo]:
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
        elif resource_type == ResourceType.DIFFICULTY:
            return self.difficulty
        else:
            raise ValueError(
                "Invalid resource_type: {}".format(resource_type))

    def get_by_type_and_index(self, resource_type: ResourceType,
                              index: int) -> ResourceInfo:
        return find_resource_info_with_id(
            self.get_by_type(resource_type), index)

    def trivial_resource(self) -> ResourceInfo:
        return self.get_by_type_and_index(ResourceType.MISC, 0)

    def impossible_resource(self) -> ResourceInfo:
        return self.get_by_type_and_index(ResourceType.MISC, 1)

    def item_percentage(self) -> ResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, 47)

    @property
    def difficulty_resource(self) -> ResourceInfo:
        return self.get_by_type_and_index(ResourceType.DIFFICULTY, 0)

    @property
    def energy_tank(self):
        return self.get_by_type_and_index(ResourceType.ITEM, 42)


PickupAssignment = Dict[PickupIndex, PickupEntry]


def merge_resources(a: CurrentResources, b: CurrentResources) -> CurrentResources:
    return {
        resource: a.get(resource, 0) + b.get(resource, 0)
        for resource in a.keys() | b.keys()
    }
