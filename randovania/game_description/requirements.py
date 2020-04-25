from functools import lru_cache
from math import ceil
from typing import NamedTuple, Optional, Iterable, FrozenSet, Iterator, Tuple

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo

MAX_DAMAGE = 9999999


class Requirement:
    def damage(self, current_resources: CurrentResources, current_energy: int) -> int:
        raise NotImplementedError()

    def satisfied(self, current_resources: CurrentResources, current_energy: int) -> bool:
        raise NotImplementedError()

    def patch_requirements(self, static_resources: CurrentResources, damage_multiplier: float,
                           ) -> "Requirement":
        """
        Creates a new Requirement that does not contain reference to resources in static_resources.
        For those that contains a reference, they're replaced with Trivial when satisfied and Impossible otherwise.
        :param static_resources:
        :param damage_multiplier: All damage requirements have their value multiplied by this.
        """
        raise NotImplementedError()

    @property
    def as_set(self) -> "RequirementSet":
        raise NotImplementedError()

    @classmethod
    @lru_cache()
    def trivial(cls) -> "Requirement":
        # empty RequirementAnd.satisfied is True
        return RequirementAnd([])

    @classmethod
    @lru_cache()
    def impossible(cls) -> "Requirement":
        # empty RequirementOr.satisfied is False
        return RequirementOr([])

    def __lt__(self, other: "Requirement"):
        return str(self) < str(other)


class RequirementAnd(Requirement):
    items: Tuple[Requirement, ...]
    _cached_hash = None

    def __init__(self, items: Iterable[Requirement]):
        self.items = tuple(items)

    @classmethod
    def simplified(cls, items: Iterable[Requirement]) -> "RequirementAnd":
        expanded = []
        for item in items:
            if isinstance(item, RequirementAnd):
                expanded.extend(item.items)
            else:
                expanded.append(item)

        new_items = []
        for item in expanded:
            if item == Requirement.impossible():
                return item
            elif item != Requirement.trivial():
                new_items.append(item)

        return cls(new_items)

    def damage(self, current_resources: CurrentResources, current_energy: int) -> int:
        return sum(
            item.damage(current_resources, current_energy)
            for item in self.items
        )

    def satisfied(self, current_resources: CurrentResources, current_energy: int) -> bool:
        return all(
            item.satisfied(current_resources, current_energy)
            for item in self.items
        )

    def patch_requirements(self, static_resources: CurrentResources, damage_multiplier: float,
                           ) -> Requirement:
        return RequirementAnd.simplified(
            item.patch_requirements(static_resources, damage_multiplier) for item in self.items
        )

    @property
    def as_set(self) -> "RequirementSet":
        result = RequirementSet.trivial()
        for item in self.items:
            result = result.union(item.as_set)
        return result

    @property
    def sorted(self) -> Tuple[Requirement]:
        return tuple(sorted(self.items))

    def __eq__(self, other):
        return isinstance(other, RequirementAnd) and self.items == other.items

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.items)
        return self._cached_hash

    def __repr__(self):
        return repr(self.items)

    def __str__(self) -> str:
        if self.items:
            visual_items = [str(item) for item in self.items]
            if len(self.items) > 1:
                return "({})".format(" and ".join(sorted(visual_items)))
            else:
                return visual_items[0]
        else:
            return "Trivial"


class RequirementOr(Requirement):
    items: Tuple[Requirement, ...]
    _cached_hash = None

    def __init__(self, items: Iterable[Requirement]):
        self.items = tuple(items)

    @classmethod
    def simplified(cls, items: Iterable[Requirement]) -> "RequirementOr":
        expanded = []
        for item in items:
            if isinstance(item, RequirementOr):
                expanded.extend(item.items)
            else:
                expanded.append(item)

        new_items = []
        for item in expanded:
            if item == Requirement.trivial():
                return item
            elif item != Requirement.impossible():
                new_items.append(item)

        return cls(new_items)

    def damage(self, current_resources: CurrentResources, current_energy: int) -> int:
        try:
            return min(
                item.damage(current_resources, current_energy)
                for item in self.items
                if item.satisfied(current_resources, current_energy)
            )
        except ValueError:
            return MAX_DAMAGE

    def satisfied(self, current_resources: CurrentResources, current_energy: int) -> bool:
        return any(
            item.satisfied(current_resources, current_energy)
            for item in self.items
        )

    def patch_requirements(self, static_resources: CurrentResources, damage_multiplier: float,
                           ) -> Requirement:
        return RequirementOr.simplified(
            item.patch_requirements(static_resources, damage_multiplier) for item in self.items
        )

    @property
    def as_set(self) -> "RequirementSet":
        alternatives = set()
        for item in self.items:
            alternatives |= item.as_set.alternatives
        return RequirementSet(alternatives)

    @property
    def sorted(self) -> Tuple[Requirement]:
        return tuple(sorted(self.items))

    def __eq__(self, other):
        return isinstance(other, RequirementOr) and self.items == other.items

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.items)
        return self._cached_hash

    def __repr__(self):
        return repr(self.items)

    def __str__(self) -> str:
        if self.items:
            visual_items = [str(item) for item in self.items]
            if len(self.items) > 1:
                return "({})".format(" or ".join(sorted(visual_items)))
            else:
                return visual_items[0]
        else:
            return "Impossible"


class ResourceRequirement(NamedTuple, Requirement):
    resource: ResourceInfo
    amount: int
    negate: bool

    @classmethod
    def with_data(cls,
                  database: ResourceDatabase,
                  resource_type: ResourceType,
                  requirement_index: int,
                  amount: int,
                  negate: bool) -> "ResourceRequirement":
        return cls(
            database.get_by_type_and_index(resource_type, requirement_index),
            amount,
            negate)

    @property
    def is_damage(self) -> bool:
        return self.resource.resource_type == ResourceType.DAMAGE

    def damage(self, current_resources: CurrentResources, current_energy: int) -> int:
        if self.resource.resource_type == ResourceType.DAMAGE:
            return ceil(self.resource.damage_reduction(current_resources) * self.amount)
        else:
            return 0

    def satisfied(self, current_resources: CurrentResources, current_energy: int) -> bool:
        """Checks if a given resources dict satisfies this requirement"""

        if self.is_damage:
            assert not self.negate, "Damage requirements shouldn't have the negate flag"

            return current_energy > self.damage(current_resources, current_energy)

        has_amount = current_resources.get(self.resource, 0) >= self.amount
        if self.negate:
            return not has_amount
        else:
            return has_amount

    def __repr__(self):
        return "{} {} {}".format(
            self.resource,
            "<" if self.negate else "≥",
            self.amount)

    @property
    def pretty_text(self):
        if self.amount == 1:
            negated_prefix = "No " if self.resource.resource_type is ResourceType.ITEM else "Before "
            non_negated_prefix = "After " if self.resource.resource_type is ResourceType.EVENT else ""
            return "{}{}".format(negated_prefix if self.negate else non_negated_prefix, self.resource)
        else:
            return str(self)

    @property
    def _as_comparison_tuple(self):
        return self.resource.resource_type, self.resource.index, self.amount, self.negate

    def __lt__(self, other: "ResourceRequirement") -> bool:
        return self._as_comparison_tuple < other._as_comparison_tuple

    def multiply_amount(self, multiplier: float) -> "ResourceRequirement":
        return ResourceRequirement(
            self.resource,
            self.amount * multiplier,
            self.negate,
        )

    def patch_requirements(self, static_resources: CurrentResources, damage_multiplier: float,
                           ) -> Requirement:
        if static_resources.get(self.resource) is not None:
            if self.satisfied(static_resources, 0):
                return Requirement.trivial()
            else:
                return Requirement.impossible()
        else:
            if self.is_damage:
                return self.multiply_amount(damage_multiplier)
            else:
                return self

    @property
    def as_set(self) -> "RequirementSet":
        return RequirementSet([
            RequirementList([
                self
            ])
        ])


class RequirementList:
    items: FrozenSet[ResourceRequirement]
    _cached_hash: Optional[int] = None

    def __deepcopy__(self, memodict):
        return self

    def __init__(self, items: Iterable[ResourceRequirement]):
        self.items = frozenset(items)

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
                    energy -= requirement.damage(current_resources, current_energy)
            else:
                return False
        return True

    def get(self, resource: ResourceInfo) -> Optional[ResourceRequirement]:
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

    @property
    def difficulty_level(self) -> int:
        for individual in self.values():
            if individual.resource.resource_type == ResourceType.DIFFICULTY:
                return individual.amount
        return 0

    def values(self) -> FrozenSet[ResourceRequirement]:
        return self.items

    def union(self, other: "RequirementList") -> "RequirementList":
        return RequirementList(self.items | other.items)


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

    def pretty_print(self, indent="", print_function=print):
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
            print_function(indent + line)

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
    def all_individual(self) -> Iterator[ResourceRequirement]:
        """
        Iterates over all individual requirements involved in this set
        :return:
        """
        for alternative in self.alternatives:
            for individual in alternative.values():
                yield individual


SatisfiableRequirements = FrozenSet[RequirementList]
