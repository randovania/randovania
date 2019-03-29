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
class ResourceConversion:
    source: SimpleResourceInfo
    target: SimpleResourceInfo
    clear_source: bool = True
    overwrite_target: bool = False


MAXIMUM_PICKUP_CONDITIONAL_RESOURCES = 3
MAXIMUM_PICKUP_RESOURCES = 8
MAXIMUM_PICKUP_CONVERSION = 1


@dataclass(frozen=True)
class PickupEntry:
    name: str
    model_index: int
    item_category: ItemCategory
    resources: Tuple[ConditionalResources, ...]
    convert_resources: Tuple[ResourceConversion, ...] = tuple()
    probability_offset: int = 0

    def __post_init__(self):
        if not isinstance(self.resources, tuple):
            raise ValueError("resources should be a tuple, got {}".format(self.resources))

        if len(self.resources) < 1:
            raise ValueError("resources should have at least 1 value")

        if len(self.resources) > MAXIMUM_PICKUP_CONDITIONAL_RESOURCES:
            raise ValueError(f"resources should have at most {MAXIMUM_PICKUP_CONDITIONAL_RESOURCES} "
                             f"values, got {len(self.resources)}")

        for i, conditional in enumerate(self.resources):
            if not isinstance(conditional, ConditionalResources):
                raise ValueError(f"Conditional at {i} should be a ConditionalResources")

            if len(conditional.resources) > MAXIMUM_PICKUP_RESOURCES:
                raise ValueError(f"Conditional at {i} should have at most {MAXIMUM_PICKUP_RESOURCES} "
                                 f"resources, got {len(conditional.resources)}")

            if i == 0:
                if conditional.item is not None:
                    raise ValueError("Conditional at 0 should not have a condition")
            else:
                if conditional.item is None:
                    raise ValueError(f"Conditional at {i} should have a condition")

        if len(self.convert_resources) > MAXIMUM_PICKUP_CONVERSION:
            raise ValueError(f"convert_resources should have at most {MAXIMUM_PICKUP_CONVERSION} value")

        for i, conversion in enumerate(self.convert_resources):
            if not conversion.clear_source or conversion.overwrite_target:
                raise ValueError(f"clear_source and overwrite_target should be True and False, "
                                 f"got {conversion.clear_source} and {conversion.overwrite_target} for index {i}")

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

        for conversion in self.convert_resources:
            quantity = current_resources.get(conversion.source, 0)
            yield conversion.source, -quantity
            yield conversion.target, quantity

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


def add_resource_gain_to_current_resources(resource_gain: ResourceGain, resources: CurrentResources):
    """
    Adds all resources from the given gain to the given CurrentResources
    :param resource_gain:
    :param resources:
    :return:
    """
    for resource, quantity in resource_gain:
        resources[resource] = resources.get(resource, 0) + quantity


def add_resources_into_another(target: CurrentResources, source: CurrentResources) -> None:
    resource_gain: ResourceGain = source.items()
    add_resource_gain_to_current_resources(resource_gain, target)
