from functools import lru_cache
from typing import NamedTuple, Optional, Iterable, FrozenSet

from randovania.resolver.resources import ResourceInfo, CurrentResources, DamageResourceInfo, ResourceType, \
    ResourceDatabase


def _calculate_reduction(resource: DamageResourceInfo,
                         current_resources: CurrentResources,
                         database: ResourceDatabase) -> float:

    multiplier = 1

    for reduction in resource.reductions:
        if current_resources.get(database.get_by_type_and_index(ResourceType.ITEM, reduction.inventory_index), 0) > 0:
            multiplier *= reduction.damage_multiplier

    return multiplier


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

    def satisfied(self, current_resources: CurrentResources, database: ResourceDatabase) -> bool:
        """Checks if a given resources dict satisfies this requirement"""

        if isinstance(self.resource, DamageResourceInfo):
            assert not self.negate, "Damage requirements shouldn't have the negate flag"
            # TODO: actually implement the damage resources

            current_energy = current_resources.get(database.energy_tank, 0) * 100
            damage = _calculate_reduction(self.resource, current_resources, database) * self.amount

            return current_energy >= damage

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
        return str(self) < str(other)


class RequirementList(frozenset):
    def __deepcopy__(self, memodict):
        return self

    def amount_unsatisfied(self, current_resources: CurrentResources, database: ResourceDatabase) -> bool:
        return sum(not requirement.satisfied(current_resources, database)
                   for requirement in self.values())

    def satisfied(self, current_resources: CurrentResources, database: ResourceDatabase) -> bool:
        """
        A list is considered satisfied if all IndividualRequirement that belongs to it are satisfied.
        In particular, an empty RequirementList is considered satisfied.
        :param database:
        :param current_resources:
        :return:
        """
        return all(requirement.satisfied(current_resources, database)
                   for requirement in self.values())

    def simplify(self,
                 static_resources: CurrentResources,
                 database: ResourceDatabase) -> Optional["RequirementList"]:
        """
        Creates a new RequirementList that does not contain reference to resources in static_resources
        :param static_resources:
        :param database:
        :return: None if this RequirementList is impossible to satisfy, otherwise the simplified RequirementList.
        """
        items = []
        for item in self:  # type: IndividualRequirement
            # The impossible resource is always impossible.
            if item.resource == database.impossible_resource():
                return None

            if item.resource in static_resources:
                # If the resource is a static resource, we either remove it from the list or
                # consider this list impossible
                if not item.satisfied(static_resources, database):
                    return None

            elif item.resource != database.trivial_resource():
                # An empty RequirementList is considered satisfied, so we don't have to add the trivial resource
                items.append(item)

        return RequirementList(items)

    def replace(self, individual: IndividualRequirement, replacement: "RequirementList") -> "RequirementList":
        items = []
        for item in self:  # type: IndividualRequirement
            if item == individual:
                items.extend(replacement)
            else:
                items.append(item)
        return RequirementList(items)

    def values(self) -> FrozenSet[IndividualRequirement]:
        return self


class RequirementSet:
    """
    Represents multiple alternatives of satisfying a requirement.
    For example, going from A to B may be possible by having Grapple+Space Jump or Screw Attack.
    """
    alternatives: FrozenSet[RequirementList]

    def __init__(self, alternatives: Iterable[RequirementList]):
        """
        Constructs a RequirementSet from given iterator of RequirementList.
        Redundant alternatives (Bombs or Bombs + Space Jump) are automatically removed.
        :param alternatives:
        """
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

    def satisfied(self, current_resources: CurrentResources, database: ResourceDatabase) -> bool:
        """
        Checks if at least one alternative is satisfied with the given resources.
        In particular, an empty RequirementSet is *never* considered satisfied.
        :param database:
        :param current_resources:
        :return:
        """
        return any(
            requirement_list.satisfied(current_resources, database)
            for requirement_list in self.alternatives)

    def simplify(self, static_resources: CurrentResources,
                 database: ResourceDatabase) -> "RequirementSet":
        """"""
        new_alternatives = [
            alternative.simplify(static_resources, database)
            for alternative in self.alternatives
        ]
        return RequirementSet(alternative
                              for alternative in new_alternatives

                              # RequirementList.simplify may return None
                              if alternative is not None)

    def replace(self, individual: IndividualRequirement, replacements: "RequirementSet") -> "RequirementSet":
        result = []

        for alternative in self.alternatives:
            if replacements.alternatives:
                for other in replacements.alternatives:
                    result.append(alternative.replace(individual, other))
            elif individual not in alternative:
                result.append(alternative)

        return RequirementSet(result)

    def union(self, other: "RequirementSet") -> "RequirementSet":
        """Create a new RequirementSet that is only satisfied when both are satisfied"""
        return RequirementSet(
            RequirementList(a.union(b))
            for a in self.alternatives
            for b in other.alternatives)

    def expand_alternatives(self, other: "RequirementSet") -> "RequirementSet":
        """Create a new RequirementSet that is satisfied when either are satisfied."""
        return RequirementSet(self.alternatives | other.alternatives)


SatisfiableRequirements = FrozenSet[RequirementList]
