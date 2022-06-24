from __future__ import annotations

import typing
from typing import Iterable

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection

if typing.TYPE_CHECKING:
    from randovania.game_description.requirements.requirement_and import RequirementAnd
    from randovania.game_description.requirements.requirement_or import RequirementOr
    from randovania.game_description.requirements.requirement_set import RequirementSet


class RequirementArrayBase(Requirement):
    __slots__ = ("items", "comment", "_cached_hash")
    items: tuple[Requirement, ...]
    comment: str | None
    _cached_hash: int | None

    def __init__(self, items: Iterable[Requirement], comment: str | None = None):
        self.items = tuple(items)
        self.comment = comment
        self._cached_hash = None

    def damage(self, current_resources: ResourceCollection, database: ResourceDatabase) -> int:
        raise NotImplementedError()

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        raise NotImplementedError()

    def patch_requirements(self, static_resources: ResourceCollection, damage_multiplier: float,
                           database: ResourceDatabase) -> Requirement:
        return type(self)(
            item.patch_requirements(static_resources, damage_multiplier, database) for item in self.items
        )

    def simplify(self, keep_comments: bool = False) -> Requirement:
        raise NotImplementedError()

    def as_set(self, database: ResourceDatabase) -> RequirementSet:
        raise NotImplementedError()

    @property
    def sorted(self) -> tuple[Requirement, ...]:
        return tuple(sorted(self.items))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.items == other.items

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.items)
        return self._cached_hash

    def __repr__(self):
        return repr(self.items)

    def iterate_resource_requirements(self, database: ResourceDatabase):
        for item in self.items:
            yield from item.iterate_resource_requirements(database)

    def __str__(self) -> str:
        if self.items:
            visual_items = [str(item) for item in self.items]
            return f"({self.combinator().join(sorted(visual_items))})"
        else:
            return self._str_no_items()

    @classmethod
    def combinator(cls):
        raise NotImplementedError()

    @classmethod
    def _str_no_items(cls):
        raise NotImplementedError()


def mergeable_array(req: RequirementAnd | RequirementOr, keep_comments: bool) -> bool:
    if keep_comments:
        return req.comment is None
    else:
        return True


def expand_items(items: tuple[Requirement, ...],
                 cls: type[RequirementAnd | RequirementOr],
                 exclude: Requirement,
                 keep_comments: bool) -> list[Requirement]:
    expanded = []

    def _add(_item):
        if _item not in expanded and _item != exclude:
            expanded.append(_item)

    for item in items:
        simplified = item.simplify(keep_comments=keep_comments)
        if isinstance(simplified, cls) and mergeable_array(simplified, keep_comments):
            for new_item in simplified.items:
                _add(new_item)
        else:
            _add(simplified)
    return expanded
