from functools import lru_cache
from typing import NamedTuple, Optional, Set, Iterable, FrozenSet

from randovania.resolver.resources import ResourceInfo, CurrentResources, DamageResourceInfo, ResourceType, \
    ResourceDatabase


class IndividualRequirement(NamedTuple):
    resource: ResourceInfo
    amount: int
    negate: bool

    @classmethod
    def with_data(cls,
                  database: ResourceDatabase,
                  resource_type: ResourceType,
                  requirement_index: int,
                  amount: int,
                  negate: bool) -> "IndividualRequirement":
        return cls(
            database.get_by_type_and_index(resource_type, requirement_index),
            amount,
            negate)

    def satisfied(self, current_resources: CurrentResources) -> bool:
        """Checks if a given resources dict satisfies this requirement"""
        if isinstance(self.resource, DamageResourceInfo):
            # TODO: actually implement the damage resources
            return True
        has_amount = current_resources.get(self.resource, 0) >= self.amount
        if self.negate:
            return not has_amount
        else:
            return has_amount

    def __repr__(self):
        return "{} {} {}".format(
            self.resource,
            "<" if self.negate else ">=",
            self.amount)

    def __lt__(self, other: "IndividualRequirement") -> bool:
        return str(self.resource) < str(other.resource)


class RequirementList(frozenset):
    def amount_unsatisfied(self, current_resources: CurrentResources) -> bool:
        return sum(not requirement.satisfied(current_resources)
                   for requirement in self)

    def satisfied(self, current_resources: CurrentResources) -> bool:
        return all(requirement.satisfied(current_resources)
                   for requirement in self)

    def simplify(self, static_resources: CurrentResources,
                 database: ResourceDatabase) -> Optional["RequirementList"]:
        items = []
        for item in self:  # type: IndividualRequirement
            if item.resource == database.impossible_resource():
                return None
            if item.resource in static_resources:
                if not item.satisfied(static_resources):
                    return None
            elif item.resource != database.trivial_resource():
                items.append(item)
        return RequirementList(items)

    def values(self) -> Set[IndividualRequirement]:
        the_set = self  # type: Set[IndividualRequirement]
        return the_set


class RequirementSet:
    alternatives: Set[RequirementList]

    def __init__(self, alternatives: Iterable[RequirementList]):
        input_set = frozenset(alternatives)
        self.alternatives = frozenset(
            requirement
            for requirement in input_set
            if not any(other < requirement for other in input_set)
        )

    def __eq__(self, other):
        return isinstance(
            other, RequirementSet) and self.alternatives == other.alternatives

    def __hash__(self):
        return hash(self.alternatives)

    def __repr__(self):
        return repr(self.alternatives)

    def pretty_print(self, indent=""):
        to_print = []
        if self == RequirementSet.impossible():
            to_print.append("Impossible")
        elif self == RequirementSet.trivial():
            to_print.append("Trivial")
        else:
            for alternative in self.alternatives:
                to_print.append(", ".join(map(str, sorted(alternative))))
        for line in sorted(to_print):
            print(indent + line)

    @classmethod
    @lru_cache()
    def trivial(cls) -> "RequirementSet":
        # empty RequirementList.satisfied is True
        return cls([RequirementList([])])

    @classmethod
    @lru_cache()
    def impossible(cls) -> "RequirementSet":
        # No alternatives makes satisfied always return False
        return cls([])

    def satisfied(self, current_resources: CurrentResources) -> bool:
        return any(
            requirement_list.satisfied(current_resources)
            for requirement_list in self.alternatives)

    def simplify(self, static_resources: CurrentResources,
                 database: ResourceDatabase) -> "RequirementSet":
        new_alternatives = [
            alternative.simplify(static_resources, database)
            for alternative in self.alternatives
        ]
        return RequirementSet(alternative for alternative in new_alternatives
                              if alternative is not None)

    def merge(self, other: "RequirementSet") -> "RequirementSet":
        return RequirementSet(
            RequirementList(a.union(b))
            for a in self.alternatives
            for b in other.alternatives)


SatisfiableRequirements = FrozenSet[RequirementList]
