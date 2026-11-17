from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, NamedTuple

from hypothesis import given, settings
from hypothesis import strategies as st

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.graph.graph_requirement import create_requirement_list, create_requirement_set

if TYPE_CHECKING:
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.graph.graph_requirement import GraphRequirementSet

_DB = default_database.resource_database_for(RandovaniaGame.BLANK)
_ITEMS = [_DB.get_item(name) for name in ("Weapon", "Ammo", "Health")]
_DAMAGE = _DB.get_damage("Damage")
_MAX_COUNT = 3


def _counts(item: ItemResourceInfo) -> range:
    return range(min(item.max_capacity, _MAX_COUNT) + 1)


class _Inventory(NamedTuple):
    label: str
    resources: ResourceCollection


def _create_inventory(counts: tuple[int, ...]) -> _Inventory:
    resources = _DB.create_resource_collection()
    resources.add_resource_gain(zip(_ITEMS, counts))
    return _Inventory(", ".join(f"{item}={count}" for item, count in zip(_ITEMS, counts)), resources)


_ALL_INVENTORIES = [_create_inventory(counts) for counts in itertools.product(*map(_counts, _ITEMS))]

_REQUIREMENTS = [
    *(ResourceRequirement.create(item, amount, False) for item in _ITEMS for amount in _counts(item)[1:]),
    *(ResourceRequirement.create(item, 1, True) for item in _ITEMS),
    *(ResourceRequirement.create(_DAMAGE, amount, False) for amount in (10, 50)),
]

# Strategies describe how hypothesis generates inputs. A requirement set is a list of alternatives
# (any one suffices), and each alternative a list of requirements that must all hold. Plain lists
# print readably in a failure, and each example builds a fresh set from them. An item appears at
# most once per alternative, since a requirement and its negation together raise a ValueError.
_alternative = st.lists(st.sampled_from(_REQUIREMENTS), max_size=3, unique_by=lambda requirement: requirement.resource)
_alternatives = st.lists(_alternative, min_size=1, max_size=4)


def _satisfied_inventories(requirement: GraphRequirementSet, health: int) -> list[str]:
    return [inventory.label for inventory in _ALL_INVENTORIES if requirement.satisfied(inventory.resources, health)]


@settings(max_examples=1000)
@given(alternatives=_alternatives, health=st.integers(min_value=1, max_value=100))
def test_optimize_alternatives_keeps_satisfied_inventories(
    alternatives: list[list[ResourceRequirement]], health: int
) -> None:
    """Removing redundant alternatives never changes which inventories satisfy the set."""
    requirement = create_requirement_set([create_requirement_list(_DB, entries) for entries in alternatives])
    before_optimize = str(requirement)
    expected = _satisfied_inventories(requirement, health)

    requirement.optimize_alternatives()

    assert _satisfied_inventories(requirement, health) == expected, f"{before_optimize} became {requirement}"
