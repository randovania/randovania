from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import unique, Enum
from typing import Iterator

from frozendict import frozendict

from randovania.game_description.requirements.base import Requirement


@unique
class DockLockType(Enum):
    """
    Represents how dock locks handle being opened from the back. This usually varies per-game.

    FRONT_BLAST_BACK_FREE_UNLOCK:
        opening from the back removes the lock permanently. Used by Metroid Prime 2: Echoes.

    FRONT_BLAST_BACK_BLAST:
        blocks access from the back, but can be destroyed normally from the back. Used by Metroid Prime.

    FRONT_BLAST_BACK_IMPOSSIBLE:
        blocks access from the back, must be opened from that side.

    FRONT_BLAST_BACK_IF_MATCHING:
        blocks access from the back. Can be destroyed from the back if both sides of the dock matches.
        Used by Metroid Dread.
    """
    FRONT_BLAST_BACK_FREE_UNLOCK = "front-blast-back-free-unlock"
    FRONT_BLAST_BACK_BLAST = "front-blast-back-blast"
    FRONT_BLAST_BACK_IMPOSSIBLE = "front-blast-back-impossible"
    FRONT_BLAST_BACK_IF_MATCHING = "front-blast-back-if-matching"


@dataclass(frozen=True, order=True, slots=True)
class DockLock:
    """
    Represents the dock has a lock that must be destroyed before it can be used.
    Used by things like `Door locked by Missiles`.
    """
    lock_type: DockLockType
    requirement: Requirement

    def __repr__(self):
        return self.lock_type.name


@dataclass(frozen=True, order=True, slots=True)
class DockWeakness:
    """
    Represents one specific type of dock with an specific requirement. Can be things like `Door locked by Plasma Beam`,
    `Tunnel you can slide through`, `Portal activated by Scan Visor`.
    The requirements for the weakness is required for every single use, but
    only from the front. The lock's requirement (if a lock is present) only needs to be satisfied once.
    """
    weakness_index: int = dataclasses.field(compare=False)
    name: str
    extra: frozendict
    requirement: Requirement
    lock: DockLock | None

    def __hash__(self):
        return hash((self.name, self.extra))

    def __repr__(self):
        return self.name

    @property
    def long_name(self):
        return self.extra.get("display_name", self.name)

    def can_unlock_from_back(self: DockWeakness, back_weak: DockWeakness | None) -> bool:
        if back_weak is not None and back_weak.lock is not None:
            opens_from_back = {DockLockType.FRONT_BLAST_BACK_FREE_UNLOCK,
                               DockLockType.FRONT_BLAST_BACK_BLAST}
            if self == back_weak:
                opens_from_back.add(DockLockType.FRONT_BLAST_BACK_IF_MATCHING)

            return back_weak.lock.lock_type in opens_from_back

        return False


@dataclass(frozen=True, slots=True)
class DockRandoParams:
    unlocked: DockWeakness
    locked: DockWeakness
    change_from: set[DockWeakness]
    change_to: set[DockWeakness]


@dataclass(frozen=True, slots=True, order=True)
class DockType:
    """Represents a kind of dock for the game. Can be things like Door, Tunnel, Portal."""
    short_name: str
    long_name: str
    extra: frozendict


@dataclass(frozen=True, slots=True)
class DockWeaknessDatabase:
    dock_types: list[DockType]
    weaknesses: dict[DockType, dict[str, DockWeakness]]
    dock_rando_params: dict[DockType, DockRandoParams]
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
