from __future__ import annotations

import typing

from randovania.lib.bitmask import Bitmask

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.graph.graph_requirement import GraphRequirementList

_ItemKey = tuple[int, int, bool]


class RequirementList:
    __slots__ = ("_bitmask", "_items", "_extra", "_cached_hash")
    _bitmask: Bitmask
    _items: dict[_ItemKey, ResourceRequirement]
    _extra: list[ResourceRequirement]
    _cached_hash: int | None

    def __copy__(self) -> typing.Self:
        return self

    def __deepcopy__(self, memodict: dict) -> RequirementList:
        return self

    def __init__(self, items: Iterable[ResourceRequirement]):
        self._items = {}
        self._extra = []
        self._bitmask = Bitmask.create()
        self._cached_hash = None

        for it in items:
            index = it.resource.resource_index
            self._items[(index, it.amount, it.negate)] = it
            if it.amount == 1 and not it.negate and not it.is_damage:
                self._bitmask.set_bit(index)
            else:
                self._extra.append(it)

    @classmethod
    def from_graph_requirement_list(
        cls, graph_list: GraphRequirementList, *, add_multiple_as_single: bool = False
    ) -> typing.Self:
        """
        Converts a GraphRequirementList into a RequirementList.
        :param graph_list:
        :param add_multiple_as_single: When set, any non-damage resource present with an amount higher
            than 1 is also present as 1. This improves `pickups_to_solve_list`.
        :return:
        """
        from randovania.game_description.requirements.resource_requirement import ResourceRequirement

        entries = []

        for resource in graph_list.all_resources():
            amount, negate = graph_list.get_requirement_for(resource)
            if add_multiple_as_single and amount > 1 and not resource.resource_type.is_damage():
                entries.append(ResourceRequirement.create(resource, 1, negate))
            entries.append(ResourceRequirement.create(resource, amount, negate))

        return cls(entries)

    def __reduce__(self) -> tuple[type[RequirementList], tuple[ResourceRequirement, ...]]:
        return RequirementList, tuple(self._items.values())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RequirementList) and self._items == other._items

    @property
    def as_stable_sort_tuple(self) -> tuple[int, list[_ItemKey]]:
        return len(self._items), sorted(self._items.keys())

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(tuple(self._items.keys()))
        return self._cached_hash

    def __repr__(self) -> str:
        return repr(list(self._items.values()))

    def __str__(self) -> str:
        if self._items:
            return ", ".join(sorted(str(item) for item in self._items.values()))
        else:
            return "Trivial"

    def values(self) -> Iterator[ResourceRequirement]:
        yield from self._items.values()
