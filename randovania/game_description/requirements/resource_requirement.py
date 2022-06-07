from __future__ import annotations

import dataclasses
from math import ceil

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType


@dataclasses.dataclass(frozen=True, slots=True)
class ResourceRequirement(Requirement):
    resource: ResourceInfo
    amount: int
    negate: bool

    @classmethod
    def simple(cls, simple: ResourceInfo) -> ResourceRequirement:
        return cls(simple, 1, False)

    @classmethod
    def with_data(cls,
                  database: ResourceDatabase,
                  resource_type: ResourceType,
                  requirement_name: str,
                  amount: int,
                  negate: bool) -> ResourceRequirement:
        return cls(
            database.get_by_type_and_index(resource_type, requirement_name),
            amount,
            negate)

    @property
    def is_damage(self) -> bool:
        return self.resource.resource_type == ResourceType.DAMAGE

    def damage(self, current_resources: ResourceCollection, database: ResourceDatabase) -> int:
        if self.resource.resource_type == ResourceType.DAMAGE:
            return ceil(database.get_damage_reduction(self.resource, current_resources) * self.amount)
        else:
            return 0

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        """Checks if a given resources dict satisfies this requirement"""

        if self.resource.resource_type == ResourceType.DAMAGE:
            assert not self.negate, "Damage requirements shouldn't have the negate flag"

            return current_energy > self.damage(current_resources, database)

        has_amount = current_resources[self.resource] >= self.amount
        if self.negate:
            return not has_amount
        else:
            return has_amount

    def simplify(self, keep_comments: bool = False) -> Requirement:
        return self

    def __repr__(self):
        return "{} {} {}".format(
            self.resource,
            "<" if self.negate else "≥",
            self.amount)

    @property
    def pretty_text(self):
        if self.amount == 1:
            negated_prefix = self.resource.resource_type.negated_prefix
            non_negated_prefix = self.resource.resource_type.non_negated_prefix
            return "{}{}".format(negated_prefix if self.negate else non_negated_prefix, self.resource)
        else:
            return str(self)

    @property
    def _as_comparison_tuple(self):
        return self.resource.resource_type, self.resource.short_name, self.amount, self.negate

    def __lt__(self, other: ResourceRequirement) -> bool:
        return self._as_comparison_tuple < other._as_comparison_tuple

    def multiply_amount(self, multiplier: float) -> ResourceRequirement:
        return ResourceRequirement(
            self.resource,
            self.amount * multiplier,
            self.negate,
        )

    def patch_requirements(self, static_resources: ResourceCollection, damage_multiplier: float,
                           database: ResourceDatabase) -> Requirement:
        if static_resources.is_resource_set(self.resource):
            if self.satisfied(static_resources, 0, database):
                return Requirement.trivial()
            else:
                return Requirement.impossible()
        else:
            if self.is_damage:
                return self.multiply_amount(damage_multiplier)
            else:
                return self

    def as_set(self, database: ResourceDatabase) -> RequirementSet:
        return RequirementSet([
            RequirementList([
                self
            ])
        ])

    def iterate_resource_requirements(self, database: ResourceDatabase):
        yield self
