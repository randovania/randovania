import typing
from typing import NamedTuple, Tuple, Union, List, Dict


class SimpleResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str

    def __str__(self):
        return self.long_name


class DamageReduction(NamedTuple):
    inventory_index: int
    damage_multiplier: float


class DamageResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    reductions: Tuple[DamageReduction, ...]

    def __str__(self):
        return "Damage {}".format(self.long_name)


class PickupIndex(typing.NamedTuple):
    node: "PickupNode"
    index: int

    def __str__(self):
        return "PickupIndex {}".format(self.index)


ResourceInfo = Union[SimpleResourceInfo, DamageResourceInfo, PickupIndex]
ResourceGain = List[Tuple[ResourceInfo, int]]
CurrentResources = Dict[ResourceInfo, int]
