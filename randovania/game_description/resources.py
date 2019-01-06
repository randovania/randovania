from typing import NamedTuple, Tuple, Union, List, Dict, Iterator

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
ResourceGainTuple = Tuple[Tuple[ResourceInfo, int], ...]
ResourceGain = Iterator[Tuple[ResourceInfo, int]]
CurrentResources = Dict[ResourceInfo, int]


class PickupEntry(NamedTuple):
    name: str
    resources: ResourceGainTuple
    item_category: str
    probability_offset: int

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        return isinstance(other, PickupEntry) and self.name == other.name

    def resource_gain(self) -> ResourceGain:
        yield from self.resources

    def __str__(self):
        return "Pickup {}".format(self.name)


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
        "Resource with long_name '{}' not found in {}".format(long_name, info_list))


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


class PickupDatabase(NamedTuple):
    pickups: Dict[str, PickupEntry]
    original_pickup_mapping: PickupAssignment
    useless_pickup: PickupEntry

    @property
    def total_pickup_count(self) -> int:
        return len(self.original_pickup_mapping)

    @property
    def all_pickup_names(self) -> Iterator[str]:
        yield from self.pickups.keys()

    @property
    def all_useful_pickups(self) -> Iterator[PickupEntry]:
        for pickup in self.pickups.values():
            if pickup is not self.useless_pickup:
                yield pickup

    def original_quantity_for(self, pickup: PickupEntry) -> int:
        return sum(1 for original in self.original_pickup_mapping.values() if original == pickup)

    def original_index(self, pickup: PickupEntry) -> PickupIndex:
        for index, p in self.original_pickup_mapping.items():
            if p == pickup:
                return index
        raise ValueError("Unknown pickup: {}".format(pickup))

    def pickup_by_name(self, pickup_name: str) -> PickupEntry:
        return self.pickups[pickup_name]


def merge_resources(a: CurrentResources, b: CurrentResources) -> CurrentResources:
    return {
        resource: a.get(resource, 0) + b.get(resource, 0)
        for resource in a.keys() | b.keys()
    }
