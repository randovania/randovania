import dataclasses
import logging
from functools import lru_cache
from math import ceil
from typing import Optional, Iterable, FrozenSet, Iterator, Tuple, List, Type, Union

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, CurrentResources
from randovania.game_description.resources.resource_type import ResourceType

MAX_DAMAGE = 9999999


class Requirement:
    def damage(self, current_resources: CurrentResources, database: ResourceDatabase) -> int:
        raise NotImplementedError()

    def satisfied(self, current_resources: CurrentResources, current_energy: int, database: ResourceDatabase) -> bool:
        raise NotImplementedError()

    def patch_requirements(self, static_resources: CurrentResources, damage_multiplier: float,
                           database: ResourceDatabase) -> "Requirement":
        """
        Creates a new Requirement that does not contain reference to resources in static_resources.
        For those that contains a reference, they're replaced with Trivial when satisfied and Impossible otherwise.
        :param static_resources:
        :param damage_multiplier: All damage requirements have their value multiplied by this.
        :param database:
        """
        raise NotImplementedError()

    def simplify(self) -> "Requirement":
        """
        Creates a new Requirement without some redundant complexities, like:
        - RequirementAnd/RequirementOr of exactly one item
        - RequirementAnd/RequirementOr of others of the same type.
        - RequirementAnd with impossible among the items
        - RequirementOr with trivial among the items
        :return:
        """
        raise NotImplementedError()

    def as_set(self, database: ResourceDatabase) -> "RequirementSet":
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

    def iterate_resource_requirements(self, database: ResourceDatabase):
        raise NotImplementedError()


class RequirementArrayBase(Requirement):
    items: Tuple[Requirement, ...]
    comment: Optional[str]
    _cached_hash = None

    def __init__(self, items: Iterable[Requirement], comment: Optional[str] = None):
        self.items = tuple(items)
        self.comment = comment

    def damage(self, current_resources: CurrentResources, database: ResourceDatabase) -> int:
        raise NotImplementedError()

    def satisfied(self, current_resources: CurrentResources, current_energy: int, database: ResourceDatabase) -> bool:
        raise NotImplementedError()

    def patch_requirements(self, static_resources: CurrentResources, damage_multiplier: float,
                           database: ResourceDatabase) -> Requirement:
        return type(self)(
            item.patch_requirements(static_resources, damage_multiplier, database) for item in self.items
        )

    def simplify(self) -> "Requirement":
        raise NotImplementedError()

    def as_set(self, database: ResourceDatabase) -> "RequirementSet":
        raise NotImplementedError()

    @property
    def sorted(self) -> Tuple[Requirement]:
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
            return "({})".format(self.combinator().join(sorted(visual_items)))
        else:
            return self._str_no_items()

    @classmethod
    def combinator(cls):
        raise NotImplementedError()

    @classmethod
    def _str_no_items(cls):
        raise NotImplementedError()


class RequirementAnd(RequirementArrayBase):
    def damage(self, current_resources: CurrentResources, database: ResourceDatabase) -> int:
        result = 0
        for item in self.items:
            if item.satisfied(current_resources, MAX_DAMAGE, database):
                result += item.damage(current_resources, database)
            else:
                return MAX_DAMAGE
        return result

    def satisfied(self, current_resources: CurrentResources, current_energy: int, database: ResourceDatabase) -> bool:
        return all(
            item.satisfied(current_resources, current_energy, database)
            for item in self.items
        )

    def simplify(self) -> Requirement:
        new_items = _expand_items(self.items, RequirementAnd, Requirement.trivial())
        if Requirement.impossible() in new_items:
            return Requirement.impossible()

        if len(new_items) == 1:
            return new_items[0]

        return RequirementAnd(new_items, comment=self.comment)

    def as_set(self, database: ResourceDatabase) -> "RequirementSet":
        result = RequirementSet.trivial()
        for item in self.items:
            result = result.union(item.as_set(database))
        return result

    @classmethod
    def combinator(cls):
        return " and "

    @classmethod
    def _str_no_items(cls):
        return "Trivial"


class RequirementOr(RequirementArrayBase):
    def damage(self, current_resources: CurrentResources, database: ResourceDatabase) -> int:
        try:
            return min(
                item.damage(current_resources, database)
                for item in self.items
                if item.satisfied(current_resources, MAX_DAMAGE, database)
            )
        except ValueError:
            return MAX_DAMAGE

    def satisfied(self, current_resources: CurrentResources, current_energy: int, database: ResourceDatabase) -> bool:
        return any(
            item.satisfied(current_resources, current_energy, database)
            for item in self.items
        )

    def simplify(self) -> Requirement:
        new_items = _expand_items(self.items, RequirementOr, Requirement.impossible())
        if Requirement.trivial() in new_items:
            return Requirement.trivial()

        num_and_requirements = 0
        common_requirements = None
        for item in new_items:
            if isinstance(item, RequirementAnd):
                num_and_requirements += 1
                if common_requirements is None:
                    common_requirements = item.items
                else:
                    common_requirements = [
                        common
                        for common in common_requirements
                        if common in item.items
                    ]

        # Only extract the common requirements if there's more than 1 requirement
        if num_and_requirements >= 2 and common_requirements:
            simplified_items = []
            common_new_or = []

            for item in new_items:
                if isinstance(item, RequirementAnd):
                    assert set(common_requirements) <= set(item.items)
                    simplified_condition = [it for it in item.items if it not in common_requirements]
                    if simplified_condition:
                        common_new_or.append(RequirementAnd(simplified_condition) if len(simplified_condition) > 1
                                             else simplified_condition[0])
                else:
                    simplified_items.append(item)

            common_requirements.append(RequirementOr(common_new_or))
            simplified_items.append(RequirementAnd(common_requirements))
            final_items = simplified_items

        else:
            final_items = new_items

        if len(final_items) == 1:
            return final_items[0]

        return RequirementOr(final_items, comment=self.comment)

    def as_set(self, database: ResourceDatabase) -> "RequirementSet":
        alternatives = set()
        for item in self.items:
            alternatives |= item.as_set(database).alternatives
        return RequirementSet(alternatives)

    @classmethod
    def combinator(cls):
        return " or "

    @classmethod
    def _str_no_items(cls):
        return "Impossible"


def _expand_items(items: Tuple[Requirement, ...],
                  cls: Type[Union[RequirementAnd, RequirementOr]],
                  exclude: Requirement) -> List[Requirement]:
    expanded = []

    def _add(_item):
        if _item not in expanded and _item != exclude:
            expanded.append(_item)

    for item in items:
        simplified = item.simplify()
        if isinstance(simplified, cls):
            for new_item in simplified.items:
                _add(new_item)
        else:
            _add(simplified)
    return expanded


@dataclasses.dataclass(frozen=True)
class ResourceRequirement(Requirement):
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

    def damage(self, current_resources: CurrentResources, database: ResourceDatabase) -> int:
        if self.resource.resource_type == ResourceType.DAMAGE:
            return ceil(database.get_damage_reduction(self.resource, current_resources) * self.amount)
        else:
            return 0

    def satisfied(self, current_resources: CurrentResources, current_energy: int, database: ResourceDatabase) -> bool:
        """Checks if a given resources dict satisfies this requirement"""

        if self.is_damage:
            assert not self.negate, "Damage requirements shouldn't have the negate flag"

            return current_energy > self.damage(current_resources, database)

        has_amount = current_resources.get(self.resource, 0) >= self.amount
        if self.negate:
            return not has_amount
        else:
            return has_amount

    def simplify(self) -> Requirement:
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
                           database: ResourceDatabase) -> Requirement:
        if static_resources.get(self.resource) is not None:
            if self.satisfied(static_resources, 0, database):
                return Requirement.trivial()
            else:
                return Requirement.impossible()
        else:
            if self.is_damage:
                return self.multiply_amount(damage_multiplier)
            else:
                return self

    def as_set(self, database: ResourceDatabase) -> "RequirementSet":
        return RequirementSet([
            RequirementList([
                self
            ])
        ])

    def iterate_resource_requirements(self, database: ResourceDatabase):
        yield self


class RequirementTemplate(Requirement):
    template_name: str

    def __init__(self, template_name: str):
        self.template_name = template_name

    def template_requirement(self, database: ResourceDatabase) -> Requirement:
        return database.requirement_template[self.template_name]

    def damage(self, current_resources: CurrentResources, database: ResourceDatabase) -> int:
        return self.template_requirement(database).damage(current_resources, database)

    def satisfied(self, current_resources: CurrentResources, current_energy: int, database: ResourceDatabase) -> bool:
        return self.template_requirement(database).satisfied(current_resources, current_energy, database)

    def patch_requirements(self, static_resources: CurrentResources, damage_multiplier: float,
                           database: ResourceDatabase) -> Requirement:
        return self.template_requirement(database).patch_requirements(static_resources, damage_multiplier, database)

    def simplify(self) -> Requirement:
        return self

    def as_set(self, database: ResourceDatabase) -> "RequirementSet":
        return self.template_requirement(database).as_set(database)

    def __eq__(self, other):
        return isinstance(other, RequirementTemplate) and self.template_name == other.template_name

    def __hash__(self) -> int:
        return hash(self.template_name)

    def __str__(self) -> str:
        return self.template_name

    def iterate_resource_requirements(self, database: ResourceDatabase):
        yield from self.template_requirement(database).iterate_resource_requirements(database)


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

    @property
    def as_stable_sort_tuple(self):
        return len(self.items), sorted(self.items)

    def __hash__(self) -> int:
        if self._cached_hash is None:
            self._cached_hash = hash(self.items)
        return self._cached_hash

    def __repr__(self):
        return repr(self.items)

    def __str__(self) -> str:
        if self.items:
            return ", ".join(sorted(map(str, self.items)))
        else:
            return "Trivial"

    def damage(self, current_resources: CurrentResources, database: ResourceDatabase):
        return sum(requirement.damage(current_resources, database) for requirement in self.values())

    def satisfied(self, current_resources: CurrentResources, current_energy: int, database: ResourceDatabase) -> bool:
        """
        A list is considered satisfied if each IndividualRequirement that belongs to it is satisfied.
        In particular, an empty RequirementList is considered satisfied.
        :param current_resources:
        :param current_energy:
        :param database:
        :return:
        """

        energy = current_energy
        for requirement in self.values():
            if requirement.satisfied(current_resources, current_energy, database):
                if requirement.resource.resource_type == ResourceType.DAMAGE:
                    energy -= requirement.damage(current_resources, database)
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
    def dangerous_resources(self) -> Iterator[ResourceInfo]:
        """
        Return an iterator of all SimpleResourceInfo in this list that have the negate flag
        :return:
        """
        for individual in self.values():
            if individual.negate:
                yield individual.resource

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
            if not any(other.items < requirement.items for other in input_set)
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

    def pretty_print(self, indent="", print_function=logging.info):
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

    def satisfied(self, current_resources: CurrentResources, current_energy: int, database: ResourceDatabase) -> bool:
        """
        Checks if at least one alternative is satisfied with the given resources.
        In particular, an empty RequirementSet is *never* considered satisfied.
        :param current_resources:
        :param current_energy:
        :param database:
        :return:
        """
        return any(
            requirement_list.satisfied(current_resources, current_energy, database)
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
    def dangerous_resources(self) -> Iterator[ResourceInfo]:
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

    def patch_requirements(self, resources: CurrentResources, database: ResourceDatabase) -> "RequirementSet":
        return RequirementOr(
            RequirementAnd(
                individual.patch_requirements(resources, 1, database)
                for individual in alternative.items
            )
            for alternative in self.alternatives
        ).as_set(database)


SatisfiableRequirements = FrozenSet[RequirementList]
