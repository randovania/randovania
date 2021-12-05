from dataclasses import dataclass
from enum import unique, Enum
from typing import Iterator

from frozendict import frozendict

from randovania.game_description.requirements import Requirement


@unique
class DockLockType(Enum):
    FRONT_ALWAYS_BACK_FREE = 0
    FRONT_BLAST_BACK_FREE_UNLOCK = 1
    FRONT_BLAST_BACK_BLAST = 2
    FRONT_BLAST_BACK_IMPOSSIBLE = 3


@dataclass(frozen=True, order=True)
class DockWeakness:
    name: str
    lock_type: DockLockType
    extra: frozendict
    requirement: Requirement

    def __hash__(self):
        return hash((self.name, self.lock_type, self.extra))

    def __repr__(self):
        return self.name

    @property
    def long_name(self):
        return self.name


@dataclass(frozen=True)
class DockType:
    short_name: str
    long_name: str
    extra: frozendict


@dataclass(frozen=True)
class DockWeaknessDatabase:
    dock_types: list[DockType]
    weaknesses: dict[DockType, dict[str, DockWeakness]]
    default_weakness: tuple[DockType, DockWeakness]

    def find_type(self, dock_type_name: str) -> DockType:
        for dock_type in self.dock_types:
            if dock_type.short_name == dock_type_name:
                return dock_type
        raise KeyError(f"Unknown dock_type_name: {dock_type_name}")

    def get_by_type(self, dock_type: DockType) -> Iterator[DockWeakness]:
        yield from self.weaknesses[dock_type].values()

    def get_by_weakness(self, dock_type_name: str, weakness_name: str) -> DockWeakness:
        return self.weaknesses[self.find_type(dock_type_name)][weakness_name]

    @property
    def all_weaknesses(self) -> Iterator[DockWeakness]:
        for weakness_dict in self.weaknesses.values():
            yield from weakness_dict.values()
