from dataclasses import dataclass
from enum import unique, Enum
from typing import NamedTuple, List

from randovania.game_description.requirements import Requirement


@unique
class DockType(Enum):
    DOOR = 0
    MORPH_BALL_DOOR = 1
    OTHER = 2
    PORTAL = 3


@unique
class DockLockType(Enum):
    FRONT_ALWAYS_BACK_FREE = 0
    FRONT_BLAST_BACK_FREE_UNLOCK = 1
    FRONT_BLAST_BACK_BLAST = 2


@dataclass(frozen=True, order=True)
class DockWeakness:
    index: int
    name: str
    lock_type: DockLockType
    requirement: Requirement
    dock_type: DockType

    def __hash__(self):
        return hash((self.index, self.name, self.dock_type))

    def __repr__(self):
        return self.name

    @property
    def long_name(self):
        return self.name


def _find_dock_weakness_with_id(info_list: List[DockWeakness],
                                index: int) -> DockWeakness:
    for info in info_list:
        if info.index == index:
            return info
    raise ValueError(
        "Dock weakness with index {} not found in {}".format(index, info_list))


class DockWeaknessDatabase(NamedTuple):
    door: List[DockWeakness]
    morph_ball: List[DockWeakness]
    other: List[DockWeakness]
    portal: List[DockWeakness]

    def get_by_type(self, dock_type: DockType) -> List[DockWeakness]:
        if dock_type == DockType.DOOR:
            return self.door
        elif dock_type == DockType.MORPH_BALL_DOOR:
            return self.morph_ball
        elif dock_type == DockType.OTHER:
            return self.other
        elif dock_type == DockType.PORTAL:
            return self.portal
        else:
            raise ValueError("Invalid dock_type: {}".format(dock_type))

    def get_by_type_and_index(self, dock_type: DockType,
                              weakness_index: int) -> DockWeakness:
        return _find_dock_weakness_with_id(
            self.get_by_type(dock_type), weakness_index)


@dataclass(frozen=True, order=True)
class DockConnection:
    area_asset_id: int
    dock_index: int

    def __repr__(self):
        return "{}/{}".format(self.area_asset_id, self.dock_index)
