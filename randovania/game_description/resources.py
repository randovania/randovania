from enum import unique, Enum
from typing import NamedTuple, Tuple, Union, List, Dict, Iterator


class SimpleResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    resource_type: str

    def __str__(self):
        return "{}: {}".format(self.resource_type, self.long_name) if self.resource_type else self.long_name


class DamageReduction(NamedTuple):
    inventory_item: SimpleResourceInfo
    damage_multiplier: float


class DamageResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    reductions: Tuple[DamageReduction, ...]

    def __str__(self):
        return "Damage {}".format(self.long_name)


class PickupIndex:
    _index: int

    def __init__(self, index: int):
        self._index = index

    def __lt__(self, other: "PickupIndex") -> bool:
        return self._index < other._index

    def __repr__(self):
        return "PickupIndex {}".format(self._index)

    def __hash__(self):
        return self._index

    def __eq__(self, other):
        return isinstance(other, PickupIndex) and other._index == self._index

    @property
    def index(self) -> int:
        return self._index


ResourceInfo = Union[SimpleResourceInfo, DamageResourceInfo, PickupIndex]
ResourceGain = Iterator[Tuple[ResourceInfo, int]]
CurrentResources = Dict[ResourceInfo, int]


class PickupEntry(NamedTuple):
    name: str
    resources: Dict[SimpleResourceInfo, int]
    item_category: str

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        return isinstance(other, PickupEntry) and self.name == other.name

    @classmethod
    def from_data(cls, name: str, data: Dict, database: "ResourceDatabase") -> "PickupEntry":
        return PickupEntry(
            name=name,
            item_category=data["item_category"],
            resources={
                find_resource_info_with_long_name(database.item, name): quantity
                for name, quantity in data["resources"].items()
            },
        )

    def resource_gain(self) -> ResourceGain:
        yield from self.resources.items()

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


@unique
class ResourceType(Enum):
    ITEM = 0
    EVENT = 1
    TRICK = 2
    DAMAGE = 3
    VERSION = 4
    MISC = 5
    DIFFICULTY = 6


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
                "Invalid requirement_type: {}".format(resource_type))

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

    @property
    def total_pickup_count(self) -> int:
        return len(self.original_pickup_mapping)

    @property
    def all_pickup_names(self) -> Iterator[str]:
        yield from self.pickups.keys()

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
