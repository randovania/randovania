from __future__ import annotations

import typing

from randovania.game_description.requirements.base import Requirement

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement


class RequirementArrayBase(Requirement):
    __slots__ = ("items", "comment", "_cached_hash")
    items: tuple[Requirement, ...]
    comment: str | None
    _cached_hash: int | None

    def __init__(self, items: Iterable[Requirement], comment: str | None = None):
        self.items = tuple(items)
        self.comment = comment
        self._cached_hash = None

    def __copy__(self) -> typing.Self:
        return type(self)(self.items, self.comment)

    def __reduce__(self) -> tuple[type[RequirementArrayBase], tuple[tuple[Requirement, ...], str | None]]:
        return type(self), (self.items, self.comment)

    def damage(self, context: NodeContext) -> int:
        raise NotImplementedError

    def satisfied(self, context: NodeContext, current_energy: int) -> bool:
        raise NotImplementedError

    def patch_requirements(self, damage_multiplier: float, context: NodeContext) -> Requirement:
        return type(self)(
            (item.patch_requirements(damage_multiplier, context) for item in self.items),
            comment=self.comment,
        )

    def simplify(self, keep_comments: bool = False) -> Requirement:
        raise NotImplementedError

    def as_set(self, context: NodeContext) -> RequirementSet:
        raise NotImplementedError

    @property
    def sorted(self) -> tuple[Requirement, ...]:
        return tuple(sorted(self.items))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.items == other.items

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.items)
        return self._cached_hash

    def __repr__(self) -> str:
        return repr(self.items)

    def iterate_resource_requirements(self, context: NodeContext) -> Iterator[ResourceRequirement]:
        for item in self.items:
            yield from item.iterate_resource_requirements(context)

    def __str__(self) -> str:
        if self.items:
            visual_items = [str(item) for item in self.items]
            return f"({self.combinator().join(sorted(visual_items))})"
        else:
            return self._str_no_items()

    @classmethod
    def combinator(cls) -> str:
        raise NotImplementedError

    @classmethod
    def _str_no_items(cls) -> str:
        raise NotImplementedError


def mergeable_array(req: RequirementArrayBase, keep_comments: bool) -> bool:
    if keep_comments:
        return req.comment is None
    else:
        return True


def expand_items(
    items: tuple[Requirement, ...], cls: type[RequirementArrayBase], exclude: Requirement, keep_comments: bool
) -> list[Requirement]:
    expanded = []

    def _add(_item: Requirement) -> None:
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
