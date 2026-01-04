from __future__ import annotations

import functools
import math
from typing import TYPE_CHECKING

from randovania.game_description.requirements.base import Requirement

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.game_description.resources.resource_type import ResourceType


class ResourceRequirement(Requirement):
    __slots__ = ("resource", "amount", "negate")
    resource: ResourceInfo
    amount: int
    negate: bool

    def __copy__(self) -> ResourceRequirement:
        return type(self)(self.resource, self.amount, self.negate)

    def __reduce__(self) -> tuple[type[ResourceRequirement], tuple[ResourceInfo, int, bool]]:
        return type(self), (self.resource, self.amount, self.negate)

    def __init__(self, resource: ResourceInfo, amount: int, negate: bool):
        self.resource = resource
        self.amount = amount
        self.negate = negate

    @classmethod
    def create(cls, resource: ResourceInfo, amount: int, negate: bool) -> ResourceRequirement:
        return ResourceRequirement(resource, amount, negate)

    @classmethod
    @functools.cache
    def simple(cls, simple: ResourceInfo) -> ResourceRequirement:
        return cls.create(simple, 1, False)

    @classmethod
    def with_data(
        cls, database: ResourceDatabase, resource_type: ResourceType, requirement_name: str, amount: int, negate: bool
    ) -> ResourceRequirement:
        return cls.create(
            database.get_by_type_and_index(resource_type, requirement_name),
            amount,
            negate,
        )

    @property
    def is_damage(self) -> bool:
        return self.resource.resource_type.is_damage()

    def simplify(self, keep_comments: bool = False) -> Requirement:
        return self

    def __repr__(self) -> str:
        return "{} {} {}".format(self.resource, "<" if self.negate else "≥", self.amount)

    @property
    def pretty_text(self) -> str:
        if self.amount == 1:
            negated_prefix = self.resource.resource_type.negated_prefix
            non_negated_prefix = self.resource.resource_type.non_negated_prefix
            return f"{negated_prefix if self.negate else non_negated_prefix}{self.resource}"
        else:
            return str(self)

    @property
    def _as_comparison_tuple(self) -> tuple[ResourceType, str, int, bool, int]:
        return (
            self.resource.resource_type,
            self.resource.short_name,
            self.amount,
            self.negate,
            self.resource.resource_index,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResourceRequirement):
            return False
        return self._as_comparison_tuple == other._as_comparison_tuple

    def __lt__(self, other: Requirement) -> bool:
        assert isinstance(other, ResourceRequirement)
        return self._as_comparison_tuple < other._as_comparison_tuple

    def __hash__(self) -> int:
        return hash(self._as_comparison_tuple)

    def multiply_amount(self, multiplier: float) -> ResourceRequirement:
        return self

    def iterate_resource_requirements(self, context: NodeContext) -> Iterator[ResourceRequirement]:
        yield self

    def is_obsoleted_by(self, other: ResourceRequirement) -> bool:
        return self.resource == other.resource and self.negate == other.negate and self.amount <= other.amount

    def damage(self, resources: ResourceCollection) -> int:
        return math.ceil(resources.get_damage_reduction(self.resource.resource_index) * self.amount)

    def satisfied(self, resources: ResourceCollection, current_energy: int) -> bool:
        if self.negate:
            return resources[self.resource] < self.amount
        elif self.is_damage:
            return self.damage(resources) < current_energy
        else:
            return resources[self.resource] >= self.amount
