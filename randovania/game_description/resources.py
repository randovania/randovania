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
    world: str
    room: str
    item: str
    resources: Dict[SimpleResourceInfo, int]
    item_category: str

    def __hash__(self):
        return hash(self.item)

    @property
    def name(self) -> str:
        return self.item

    @classmethod
    def from_data(cls, data: Dict, database: "ResourceDatabase") -> "PickupEntry":
        return PickupEntry(
            world=data["world"],
            room=data["room"],
            item=data["item"],
            item_category=data["item_category"],
            resources={
                find_resource_info_with_long_name(database.item, name): quantity
                for name, quantity in data["resources"].items()
            },
        )

    def resource_gain(self) -> ResourceGain:
        yield from self.resources.items()

    def __str__(self):
        return "Pickup {}".format(self.item)


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


class PickupDatabase(NamedTuple):
    pickups: List[PickupEntry]

    def pickups_split_by_name(self) -> Dict[str, List[PickupEntry]]:
        result = {}
        for pickup in self.pickups:
            result[pickup.item] = result.get(pickup.item, [])
            result[pickup.item].append(pickup)
        return result


def merge_resources(a: CurrentResources, b: CurrentResources) -> CurrentResources:
    return {
        resource: a.get(resource, 0) + b.get(resource, 0)
        for resource in a.keys() | b.keys()
    }
