from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import pytest

from randovania.graph.graph_requirement import GraphRequirementList, GraphRequirementSet

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase


@pytest.fixture
def mock_resources(blank_resource_db: ResourceDatabase):
    """Create some mock resources for testing."""
    return {
        "item_a": blank_resource_db.get_item("Ammo"),
        "item_b": blank_resource_db.get_item("Health"),
        "item_c": blank_resource_db.item[0] if blank_resource_db.item else None,
    }


def test_set_special_cases(blank_resource_db: ResourceDatabase):
    """Test empty, trivial, and impossible requirement sets."""
    resources = blank_resource_db.create_resource_collection()

    # Empty set: no alternatives, never satisfied
    empty = GraphRequirementSet()
    assert empty.num_alternatives() == 0
    assert not empty.satisfied(resources, 100.0)
    assert empty.is_impossible()
    assert str(empty) == "Impossible"

    # Trivial set: always satisfied
    trivial = GraphRequirementSet.trivial()
    assert trivial.satisfied(resources, 100.0)
    assert trivial.is_trivial()
    assert str(trivial) == "Trivial"

    # Impossible set: never satisfied
    impossible = GraphRequirementSet.impossible()
    assert not impossible.satisfied(resources, 100.0)
    assert impossible.is_impossible()
    assert str(impossible) == "Impossible"


def test_set_alternatives_and_satisfaction(mock_resources, blank_resource_db: ResourceDatabase):
    """Test adding alternatives and satisfaction with different resource configurations."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_b"], 1, False)

    req_set = GraphRequirementSet()
    req_set.add_alternative(req1)
    req_set.add_alternative(req2)

    assert req_set.num_alternatives() == 2

    # Not satisfied when no resources available
    resources = blank_resource_db.create_resource_collection()
    assert not req_set.satisfied(resources, 100.0)

    # Satisfied when at least one alternative is met
    resources.add_resource_gain([(mock_resources["item_a"], 1)])
    assert req_set.satisfied(resources, 100.0)


def test_set_optimize_alternatives(mock_resources, blank_resource_db: ResourceDatabase):
    """Test optimize_alternatives removes redundant alternatives."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_a"], 1, False)
    req2.add_resource(mock_resources["item_b"], 1, False)

    req3 = GraphRequirementList(blank_resource_db)
    req3.add_resource(mock_resources["item_a"], 5, False)

    # Test with simple redundancy
    req_set = GraphRequirementSet()
    req_set.add_alternative(copy.copy(req1))
    req_set.add_alternative(copy.copy(req2))
    req_set.optimize_alternatives()
    assert req_set.num_alternatives() == 1
    assert req_set.get_alternative(0) == req1

    # Test with quantity redundancy - req1 (amount=1) is less restrictive than req3 (amount=5)
    req_set2 = GraphRequirementSet()
    req_set2.add_alternative(copy.copy(req1))
    req_set2.add_alternative(copy.copy(req2))
    req_set2.add_alternative(copy.copy(req3))
    req_set2.optimize_alternatives()
    assert req_set2.num_alternatives() == 1
    assert req_set2.get_alternative(0) == req1


def test_set_copy_then_and_with_set_trivial(mock_resources, blank_resource_db: ResourceDatabase):
    """Test copy_then_and_with_set with trivial sets (equivalent to test_trivial_merge)."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)

    req_set = GraphRequirementSet()
    req_set.add_alternative(req1)

    trivial = GraphRequirementSet.trivial()
    impossible = GraphRequirementSet.impossible()

    # trivial AND trivial = trivial
    result1 = trivial.copy_then_and_with_set(trivial)
    assert result1.is_trivial()

    # trivial AND req_set = req_set
    result2 = trivial.copy_then_and_with_set(req_set)
    assert result2.num_alternatives() == 1

    # req_set AND trivial = req_set
    result3 = req_set.copy_then_and_with_set(trivial)
    assert result3.num_alternatives() == 1

    # trivial AND impossible = impossible
    result4 = trivial.copy_then_and_with_set(impossible)
    assert result4.is_impossible()

    # impossible AND req_set = impossible
    result5 = impossible.copy_then_and_with_set(req_set)
    assert result5.is_impossible()

    # req_set AND impossible = impossible
    result6 = req_set.copy_then_and_with_set(impossible)
    assert result6.is_impossible()

    # req_set AND req_set = req_set
    result7 = req_set.copy_then_and_with_set(req_set)
    assert result7.num_alternatives() == 1


def test_set_copy_then_and_with_set_expand(mock_resources, blank_resource_db: ResourceDatabase):
    """Test copy_then_and_with_set expands alternatives correctly."""
    req_a = GraphRequirementList(blank_resource_db)
    req_a.add_resource(mock_resources["item_a"], 1, False)

    req_b = GraphRequirementList(blank_resource_db)
    req_b.add_resource(mock_resources["item_b"], 1, False)

    set_a = GraphRequirementSet()
    set_a.add_alternative(req_a)

    set_b = GraphRequirementSet()
    set_b.add_alternative(req_b)

    # (A) AND (B) = (A and B)
    result = set_a.copy_then_and_with_set(set_b)
    assert result.num_alternatives() == 1
    alt = result.get_alternative(0)
    assert mock_resources["item_a"] in alt.all_resources()
    assert mock_resources["item_b"] in alt.all_resources()


def test_set_copy_then_and_with_set_cartesian(mock_resources, blank_resource_db: ResourceDatabase):
    """Test copy_then_and_with_set performs cartesian product of alternatives."""
    req_a = GraphRequirementList(blank_resource_db)
    req_a.add_resource(mock_resources["item_a"], 1, False)

    req_b = GraphRequirementList(blank_resource_db)
    req_b.add_resource(mock_resources["item_b"], 1, False)

    weapon = blank_resource_db.get_item("Weapon")
    jump = blank_resource_db.get_item("Jump")

    req_c = GraphRequirementList(blank_resource_db)
    req_c.add_resource(weapon, 1, False)

    req_d = GraphRequirementList(blank_resource_db)
    req_d.add_resource(jump, 1, False)

    set_ab = GraphRequirementSet()
    set_ab.add_alternative(req_a)
    set_ab.add_alternative(req_b)

    set_cd = GraphRequirementSet()
    set_cd.add_alternative(req_c)
    set_cd.add_alternative(req_d)

    # (A or B) AND (C or D) = (A and C) or (A and D) or (B and C) or (B and D)
    result = set_ab.copy_then_and_with_set(set_cd)
    assert result.num_alternatives() == 4


def test_set_copy_then_remove_entries_for_set_resources(mock_resources, blank_resource_db: ResourceDatabase):
    """Test copy_then_remove_entries_for_set_resources on GraphRequirementSet."""
    weapon = blank_resource_db.get_item("Weapon")
    key = blank_resource_db.get_item("BlueKey")
    ammo = blank_resource_db.get_item("Ammo")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 1, False)
    req1.add_resource(ammo, 2, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(key, 1, False)

    req_set = GraphRequirementSet()
    req_set.add_alternative(req1)
    req_set.add_alternative(req2)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(weapon, 1)])

    result = req_set.copy_then_remove_entries_for_set_resources(resources)
    assert result.num_alternatives() == 2


def test_set_equality(mock_resources, blank_resource_db: ResourceDatabase):
    """Test equality and inequality of GraphRequirementSets."""
    # Empty sets are equal
    empty1 = GraphRequirementSet()
    empty2 = GraphRequirementSet()
    assert empty1 == empty2
    assert empty1.equals_to(empty2)

    # Sets with same alternatives are equal
    req = GraphRequirementList(blank_resource_db)
    req.add_resource(mock_resources["item_a"], 1, False)

    set1 = GraphRequirementSet()
    set1.add_alternative(copy.copy(req))

    set2 = GraphRequirementSet()
    set2.add_alternative(copy.copy(req))
    assert set1 == set2

    # Sets with different alternatives are not equal
    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_b"], 1, False)

    set3 = GraphRequirementSet()
    set3.add_alternative(req2)
    assert set1 != set3


def test_set_copy(mock_resources, blank_resource_db: ResourceDatabase):
    """Test copying a GraphRequirementSet."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)

    req_set1 = GraphRequirementSet()
    req_set1.add_alternative(req1)

    req_set2 = copy.copy(req_set1)

    assert req_set1.equals_to(req_set2)
    assert req_set1 == req_set2


def test_set_freeze(mock_resources, blank_resource_db: ResourceDatabase):
    """Test freezing a GraphRequirementSet."""
    req = GraphRequirementList(blank_resource_db)
    req.add_resource(mock_resources["item_a"], 1, False)

    req_set = GraphRequirementSet()
    req_set.add_alternative(req)

    assert not req_set.is_frozen()
    req_set.freeze()
    assert req_set.is_frozen()

    with pytest.raises(RuntimeError, match=r"Cannot modify a frozen GraphRequirementSet"):
        req_set.add_alternative(req)


def test_set_string_representation(mock_resources, blank_resource_db: ResourceDatabase):
    """Test string representation of GraphRequirementSets."""
    # Empty/impossible set
    assert str(GraphRequirementSet()) == "Impossible"
    assert str(GraphRequirementSet.impossible()) == "Impossible"

    # Trivial set
    assert str(GraphRequirementSet.trivial()) == "Trivial"

    # Single alternative
    req = GraphRequirementList(blank_resource_db)
    req.add_resource(mock_resources["item_a"], 1, False)
    single = GraphRequirementSet()
    single.add_alternative(req)
    assert str(single) == "Missile"

    # Multiple alternatives
    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_b"], 1, False)
    multiple = GraphRequirementSet()
    multiple.add_alternative(copy.copy(req))
    multiple.add_alternative(req2)
    result = str(multiple)
    assert "Missile" in result
    assert "Health" in result
    assert " or " in result


def test_set_trivial_and_impossible_checks(blank_resource_db: ResourceDatabase):
    """Test is_trivial and is_impossible methods."""
    # Trivial set
    trivial = GraphRequirementSet.trivial()
    assert trivial.is_trivial()
    assert not trivial.is_impossible()

    # Impossible set
    impossible = GraphRequirementSet.impossible()
    assert impossible.is_impossible()
    assert not impossible.is_trivial()

    # Empty set is impossible
    empty = GraphRequirementSet()
    assert empty.is_impossible()
    assert not empty.is_trivial()

    # Set with empty alternative is trivial
    with_empty = GraphRequirementSet()
    with_empty.add_alternative(GraphRequirementList(blank_resource_db))
    assert with_empty.is_trivial()


def test_set_isolate_damage_requirements(blank_resource_db: ResourceDatabase):
    """Test isolate_damage_requirements with various scenarios."""
    damage = blank_resource_db.get_damage("Damage")
    weapon = blank_resource_db.get_item("Weapon")

    # Empty set returns impossible
    empty = GraphRequirementSet()
    resources = blank_resource_db.create_resource_collection()
    assert empty.isolate_damage_requirements(resources).is_impossible()

    # With satisfied non-damage requirements, isolates damage
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 1, False)
    req1.add_resource(damage, 100, False)

    req_set = GraphRequirementSet()
    req_set.add_alternative(req1)

    resources.add_resource_gain([(weapon, 1)])
    isolated = req_set.isolate_damage_requirements(resources)
    assert isolated.num_alternatives() == 1
    assert str(isolated.get_alternative(0)) == "Normal Damage ≥ 100"

    # With unsatisfied non-damage requirements, returns impossible
    resources2 = blank_resource_db.create_resource_collection()
    assert req_set.isolate_damage_requirements(resources2).is_impossible()


def test_set_constructor_with_alternatives(mock_resources, blank_resource_db: ResourceDatabase):
    """Test constructing GraphRequirementSet and verifying alternatives."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)
    req1.add_resource(mock_resources["item_b"], 5, False)

    weapon = blank_resource_db.get_item("Weapon")
    jump = blank_resource_db.get_item("Jump")

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(weapon, 1, False)
    req2.add_resource(jump, 1, False)

    key = blank_resource_db.get_item("BlueKey")

    req3 = GraphRequirementList(blank_resource_db)
    req3.add_resource(key, 1, False)

    req_set = GraphRequirementSet()
    req_set.add_alternative(req1)
    req_set.add_alternative(req2)
    req_set.add_alternative(req3)

    assert req_set.num_alternatives() == 3
    alternatives = req_set.alternatives
    assert len(alternatives) == 3
