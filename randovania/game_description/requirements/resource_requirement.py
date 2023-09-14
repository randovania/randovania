from __future__ import annotations

import functools
from math import ceil
from typing import TYPE_CHECKING

from randovania.game_description.requirements.base import MAX_DAMAGE, Requirement
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_type import ResourceType

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


class ResourceRequirement(Requirement):
    __slots__ = ("resource", "amount", "negate")
    resource: ResourceInfo
    amount: int
    negate: bool

    def __post_init__(self) -> None:
        assert TypeError("No ResourceRequirement should be directly created")

    def __copy__(self) -> ResourceRequirement:
        return type(self)(self.resource, self.amount, self.negate)

    def __reduce__(self) -> tuple[type[ResourceRequirement], tuple[ResourceInfo, int, bool]]:
        return type(self), (self.resource, self.amount, self.negate)

    def __init__(self, resource: ResourceInfo, amount: int, negate: bool):
        self.resource = resource
        self.amount = amount
        self.negate = negate
        self.__post_init__()

    @classmethod
    def create(cls, resource: ResourceInfo, amount: int, negate: bool) -> ResourceRequirement:
        if resource.resource_type == ResourceType.DAMAGE:
            return DamageResourceRequirement(resource, amount, negate)

        if negate:
            return NegatedResourceRequirement(resource, amount, negate)

        return PositiveResourceRequirement(resource, amount, negate)

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
        return False

    def damage(self, current_resources: ResourceCollection, database: ResourceDatabase) -> int:
        if self.satisfied(current_resources, MAX_DAMAGE, database):
            return 0
        else:
            return MAX_DAMAGE

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        """Checks if a given resource collection satisfies this requirement"""
        raise NotImplementedError

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
    def _as_comparison_tuple(self) -> tuple[ResourceType, str, int, bool]:
        return self.resource.resource_type, self.resource.short_name, self.amount, self.negate

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

    def patch_requirements(
        self, static_resources: ResourceCollection, damage_multiplier: float, database: ResourceDatabase
    ) -> Requirement:
        if static_resources.is_resource_set(self.resource):
            if self.satisfied(static_resources, 0, database):
                return Requirement.trivial()
            elif not isinstance(self.resource, ItemResourceInfo) or self.resource.max_capacity <= 1:
                return Requirement.impossible()
            else:
                return self
        else:
            return self.multiply_amount(damage_multiplier)

    def as_set(self, database: ResourceDatabase) -> RequirementSet:
        return RequirementSet([RequirementList([self])])

    def iterate_resource_requirements(self, database: ResourceDatabase) -> Iterator[ResourceRequirement]:
        yield self

    def is_obsoleted_by(self, other: ResourceRequirement) -> bool:
        return self.resource == other.resource and self.negate == other.negate and self.amount <= other.amount


class DamageResourceRequirement(ResourceRequirement):
    resource: SimpleResourceInfo

    def __post_init__(self) -> None:
        # Make sure this requirement received an actual resource
        assert self.resource.resource_type == ResourceType.DAMAGE
        assert not self.negate, "Damage requirements shouldn't have the negate flag"

    @property
    def is_damage(self) -> bool:
        return True

    def damage(self, current_resources: ResourceCollection, database: ResourceDatabase) -> int:
        return ceil(database.get_damage_reduction(self.resource, current_resources) * self.amount)

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        return current_energy > self.damage(current_resources, database)

    def multiply_amount(self, multiplier: float) -> ResourceRequirement:
        return DamageResourceRequirement(
            self.resource,
            int(self.amount * multiplier),
            self.negate,
        )


class NegatedResourceRequirement(ResourceRequirement):
    def __post_init__(self) -> None:
        # Make sure this requirement received an actual resource
        assert self.resource.resource_type != ResourceType.DAMAGE
        assert self.negate

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        return current_resources[self.resource] < self.amount


class PositiveResourceRequirement(ResourceRequirement):
    def __post_init__(self) -> None:
        # Make sure this requirement received an actual resource
        assert self.resource.resource_type != ResourceType.DAMAGE
        assert not self.negate

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        return current_resources[self.resource] >= self.amount
