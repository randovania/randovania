from functools import lru_cache
from math import ceil
from typing import NamedTuple, Optional, Iterable, FrozenSet, Iterator, Tuple

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


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

    def damage(self, current_resources: CurrentResources) -> int:
        if self.resource.resource_type == ResourceType.DAMAGE:
            return ceil(self.resource.damage_reduction(current_resources) * self.amount)
        else:
            return 0

    def satisfied(self, current_resources: CurrentResources, current_energy: int) -> bool:
        """Checks if a given resources dict satisfies this requirement"""

        if self.resource.resource_type == ResourceType.DAMAGE:
            assert not self.negate, "Damage requirements shouldn't have the negate flag"

            return current_energy > self.damage(current_resources)

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

    @property
    def pretty_text(self):
        if self.amount == 1:
            return "{}{}".format("No " if self.negate else "", self.resource)
        else:
            return str(self)

    @property
    def _as_comparison_tuple(self):
        return self.resource.resource_type, self.resource.index, self.amount, self.negate

    def __lt__(self, other: "IndividualRequirement") -> bool:
        return self._as_comparison_tuple < other._as_comparison_tuple


class RequirementList:
    difficulty_level: int
    items: FrozenSet[IndividualRequirement]
    _cached_hash: Optional[int] = None

    def __deepcopy__(self, memodict):
        return self

    def __init__(self, difficulty_level: int, items: Iterable[IndividualRequirement]):
        self.difficulty_level = difficulty_level
        self.items = frozenset(items)

    @classmethod
    def with_single_resource(cls, resource: ResourceInfo) -> "RequirementList":
        return cls(0, [IndividualRequirement(resource, 1, False)])

    @classmethod
    def without_misc_resources(cls,
                               items: Iterable[IndividualRequirement],
                               database: ResourceDatabase, ) -> Optional["RequirementList"]:

        difficulty = 0

        to_add = []
        for individual in items:
            if individual.resource == database.impossible_resource():
                raise Exception("Impossible resource found in a RequirementList")

            elif individual.resource == database.trivial_resource():
                raise Exception("Trivial resource found in a RequirementList")

            if individual.resource == database.difficulty_resource:
                assert not individual.negate, "We shouldn't have a negate requirement for difficulty"
                difficulty = individual.amount

            to_add.append(individual)

        return cls(difficulty, to_add)

    def __eq__(self, other):
        return isinstance(
            other, RequirementList) and self.items == other.items

    def __lt__(self, other: "RequirementList"):
        return self.items < other.items

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.items)
        return self._cached_hash

    def __repr__(self):
        return repr(self.items)

    def __str__(self) -> str:
        if self.items:
            return ", ".join(map(str, sorted(self.items)))
        else:
            return "Trivial"

    def amount_unsatisfied(self, current_resources: CurrentResources, current_energy: int) -> bool:
        return sum(not requirement.satisfied(current_resources, current_energy)
                   for requirement in self.values())

    def damage(self, current_resources: CurrentResources) -> int:
        return sum(requirement.damage(current_resources) for requirement in self.values())

    def satisfied(self, current_resources: CurrentResources, current_energy: int) -> bool:
        """
        A list is considered satisfied if each IndividualRequirement that belongs to it is satisfied.
        In particular, an empty RequirementList is considered satisfied.
        :param current_resources:
        :param current_energy:
        :return:
        """

        energy = current_energy
        for requirement in self.values():
            if requirement.satisfied(current_resources, current_energy):
                if requirement.resource.resource_type == ResourceType.DAMAGE:
                    energy -= requirement.damage(current_resources)
            else:
                return False
        return True

    def simplify(self, static_resources: CurrentResources) -> Optional["RequirementList"]:
        """
        Creates a new RequirementList that does not contain reference to resources in static_resources
        :param static_resources:
        :return: None if this RequirementList is impossible to satisfy, otherwise the simplified RequirementList.
        """
        items = []
        for item in self.values():
            if static_resources.get(item.resource) is not None:
                # If the resource is a static resource, we either remove it from the list or
                # consider this list impossible
                if not item.satisfied(static_resources, 0):
                    return None
            else:
                # An empty RequirementList is considered satisfied, so we don't have to add the trivial resource
                items.append(item)

        return RequirementList(self.difficulty_level, items)

    def get(self, resource: ResourceInfo) -> Optional[IndividualRequirement]:
        """
        Gets an IndividualRequirement that uses the given resource
        :param resource:
        :return:
        """
        for item in self.values():
            if item.resource == resource:
                return item
        return None

    @property
    def dangerous_resources(self) -> Iterator[SimpleResourceInfo]:
        """
        Return an iterator of all SimpleResourceInfo in this list that have the negate flag
        :return:
        """
        for individual in self.values():
            if individual.negate:
                yield individual.resource

    def replace(self, individual: IndividualRequirement, replacement: "RequirementList") -> "RequirementList":
        items = []
        for item in self.values():
            if item == individual:
                items.extend(replacement)
            else:
                items.append(item)
        return RequirementList(self.difficulty_level, items)

    def values(self) -> FrozenSet[IndividualRequirement]:
        return self.items

    def union(self, other: "RequirementList") -> "RequirementList":
        return RequirementList(max(self.difficulty_level, other.difficulty_level),
                               self.items | other.items)

    @property
    def sorted(self) -> Tuple[IndividualRequirement]:
        return tuple(sorted(self.items))


class RequirementSet:
    """
    Represents multiple alternatives of satisfying a requirement.
    For example, going from A to B may be possible by having Grapple+Space Jump or Screw Attack.
    """
    alternatives: FrozenSet[RequirementList]
    _cached_hash: Optional[int] = None

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

    def __deepcopy__(self, memodict):
        return self

    def __eq__(self, other):
        return isinstance(
            other, RequirementSet) and self.alternatives == other.alternatives

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.alternatives)
        return self._cached_hash

    def __repr__(self):
        return repr(self.alternatives)

    def pretty_print(self, indent=""):
        to_print = []
        if self == RequirementSet.impossible():
            to_print.append("Impossible")
        elif self == RequirementSet.trivial():
            to_print.append("Trivial")
        else:
            to_print.extend(
                str(alternative)
                for alternative in self.alternatives
            )
        for line in sorted(to_print):
            print(indent + line)

    @classmethod
    @lru_cache()
    def trivial(cls) -> "RequirementSet":
        # empty RequirementList.satisfied is True
        return cls([RequirementList(0, [])])

    @classmethod
    @lru_cache()
    def impossible(cls) -> "RequirementSet":
        # No alternatives makes satisfied always return False
        return cls([])

    def minimum_damage(self, current_resources: CurrentResources, current_energy: int) -> int:
        damage = 1499
        for requirement_list in self.alternatives:
            if requirement_list.satisfied(current_resources, current_energy):
                damage = min(damage, requirement_list.damage(current_resources))
        return damage

    def satisfied(self, current_resources: CurrentResources, current_energy: int) -> bool:
        """
        Checks if at least one alternative is satisfied with the given resources.
        In particular, an empty RequirementSet is *never* considered satisfied.
        :param current_resources:
        :param current_energy:
        :return:
        """
        return any(
            requirement_list.satisfied(current_resources, current_energy)
            for requirement_list in self.alternatives)

    def minimum_satisfied_difficulty(self,
                                     current_resources: CurrentResources,
                                     current_energy: int,
                                     ) -> Optional[int]:
        """
        Gets the minimum difficulty that is currently satisfied
        :param current_resources:
        :param current_energy:
        :return:
        """
        difficulties = [
            requirement_list.difficulty_level
            for requirement_list in self.alternatives
            if requirement_list.satisfied(current_resources, current_energy)
        ]
        if difficulties:
            return min(difficulties)
        else:
            return None

    def simplify(self, static_resources: CurrentResources) -> "RequirementSet":
        """"""
        new_alternatives = [
            alternative.simplify(static_resources)
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
            elif individual not in alternative.values():
                result.append(alternative)

        return RequirementSet(result)

    def union(self, other: "RequirementSet") -> "RequirementSet":
        """Create a new RequirementSet that is only satisfied when both are satisfied"""
        return RequirementSet(
            a.union(b)
            for a in self.alternatives
            for b in other.alternatives)

    def expand_alternatives(self, other: "RequirementSet") -> "RequirementSet":
        """Create a new RequirementSet that is satisfied when either are satisfied."""
        return RequirementSet(self.alternatives | other.alternatives)

    @property
    def dangerous_resources(self) -> Iterator[SimpleResourceInfo]:
        """
        Return an iterator of all SimpleResourceInfo in all alternatives that have the negate flag
        :return:
        """
        for alternative in self.alternatives:
            yield from alternative.dangerous_resources

    @property
    def progression_resources(self) -> FrozenSet[SimpleResourceInfo]:
        return frozenset(
            individual.resource
            for individual in self.all_individual
            if isinstance(individual.resource, SimpleResourceInfo) and not individual.negate
        )

    @property
    def all_individual(self) -> Iterator[IndividualRequirement]:
        """
        Iterates over all individual requirements involved in this set
        :return:
        """
        for alternative in self.alternatives:
            for individual in alternative.values():
                yield individual


SatisfiableRequirements = FrozenSet[RequirementList]
