from __future__ import annotations

import copy

import pytest

from randovania.graph.graph_requirement import GraphRequirementList


@pytest.fixture
def mock_resources(blank_resource_db):
    """Create some mock resources for testing."""
    return {
        "item_a": blank_resource_db.get_item("Ammo"),
        "item_b": blank_resource_db.get_item("Health"),
        "item_c": blank_resource_db.item[0] if blank_resource_db.item else None,
    }


def test_create_empty():
    """Test creating an empty requirement list."""
    req = GraphRequirementList()
    assert req.all_resources() == set()


def test_add_simple_resource(mock_resources):
    """Test adding a simple resource requirement (amount = 1)."""
    req = GraphRequirementList()
    resource = mock_resources["item_a"]

    req.add_resource(resource, 1, False)

    assert req.all_resources() == {resource}
    assert req.get_requirement_for(resource) == (1, False)


def test_cant_add_resource_when_frozen(mock_resources):
    """Test adding a resource when the list is frozen."""
    req = GraphRequirementList()
    resource = mock_resources["item_a"]

    req.freeze()
    with pytest.raises(RuntimeError, match=r"Cannot modify a frozen GraphRequirementList"):
        req.add_resource(resource, 1, False)

    assert req.all_resources() == set()


def test_add_negate_resource(mock_resources):
    """Test adding a negated resource requirement."""
    req = GraphRequirementList()
    resource = mock_resources["item_a"]

    req.add_resource(resource, 1, True)

    assert req.all_resources() == {resource}
    assert req.get_requirement_for(resource) == (1, True)


def test_add_resource_with_amount(mock_resources):
    """Test adding a resource requirement with amount > 1."""
    req = GraphRequirementList()
    resource = mock_resources["item_a"]

    req.add_resource(resource, 5, False)

    assert req.all_resources() == {resource}
    assert req.get_requirement_for(resource) == (5, False)


def test_add_resource_amount_zero_ignored(mock_resources):
    """Test that adding a resource with amount 0 is ignored."""
    req = GraphRequirementList()
    resource = mock_resources["item_a"]

    req.add_resource(resource, 0, False)

    assert req.all_resources() == set()


def test_add_multiple_resources(mock_resources):
    """Test adding multiple different resources."""
    req = GraphRequirementList()

    req.add_resource(mock_resources["item_a"], 1, False)
    req.add_resource(mock_resources["item_b"], 3, False)

    assert req.all_resources() == {mock_resources["item_a"], mock_resources["item_b"]}


def test_add_resource_max_amount(mock_resources):
    """Test that adding the same resource twice takes the max amount."""
    req = GraphRequirementList()
    resource = mock_resources["item_a"]

    req.add_resource(resource, 5, False)
    req.add_resource(resource, 3, False)

    assert req.get_requirement_for(resource) == (5, False)


def test_equality_empty():
    """Test equality of empty requirement lists."""
    req1 = GraphRequirementList()
    req2 = GraphRequirementList()

    assert req1 == req2
    assert req1.equals_to(req2)


def test_equality_same_requirements(mock_resources):
    """Test equality with same requirements."""
    req1 = GraphRequirementList()
    req2 = GraphRequirementList()

    resource = mock_resources["item_a"]
    req1.add_resource(resource, 1, False)
    req2.add_resource(resource, 1, False)

    assert req1 == req2


def test_inequality_different_requirements(mock_resources):
    """Test inequality with different requirements."""
    req1 = GraphRequirementList()
    req2 = GraphRequirementList()

    req1.add_resource(mock_resources["item_a"], 1, False)
    req2.add_resource(mock_resources["item_b"], 1, False)

    assert req1 != req2


def test_hash_consistency(mock_resources):
    """Test that equal requirement lists have the same hash."""
    req1 = GraphRequirementList()
    req2 = GraphRequirementList()

    resource = mock_resources["item_a"]
    req1.add_resource(resource, 1, False)
    req2.add_resource(resource, 1, False)

    req1.freeze()
    req2.freeze()

    assert hash(req1) == hash(req2)


def test_copy_simple(mock_resources):
    """Test copying a requirement list."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)
    req1.add_resource(mock_resources["item_b"], 3, False)

    req2 = copy.copy(req1)

    assert req1.equals_to(req2)
    assert req1 == req2


def test_copy_independence(mock_resources):
    """Test that copied requirement lists are independent."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = copy.copy(req1)
    req2.add_resource(mock_resources["item_b"], 1, False)

    assert req2.all_resources() == {mock_resources["item_a"], mock_resources["item_b"]}
    assert req1.all_resources() == {mock_resources["item_a"]}


def test_get_requirement_for_missing(mock_resources):
    """Test get_requirement_for with resource not in list."""
    req = GraphRequirementList()

    assert req.get_requirement_for(mock_resources["item_a"]) == (0, False)


def test_satisfied_empty(blank_resource_db):
    """Test that empty requirement list is always satisfied."""
    req = GraphRequirementList()
    resources = blank_resource_db.create_resource_collection()

    assert req.satisfied(resources, 100.0)


@pytest.mark.parametrize(("has_resource", "expected"), [(True, True), (False, False)])
def test_satisfied_simple(mock_resources, blank_resource_db, has_resource, expected):
    """Test satisfaction when resource is present or missing."""
    req = GraphRequirementList()
    resource = mock_resources["item_a"]
    req.add_resource(resource, 1, False)

    resources = blank_resource_db.create_resource_collection()
    if has_resource:
        resources.add_resource_gain([(resource, 1)])

    assert req.satisfied(resources, 100.0) == expected


@pytest.mark.parametrize(("resource_amount", "expected"), [(10, True), (3, False)])
def test_satisfied_amount(mock_resources, blank_resource_db, resource_amount, expected):
    """Test satisfaction with sufficient or insufficient amount."""
    req = GraphRequirementList()
    resource = mock_resources["item_a"]
    req.add_resource(resource, 5, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(resource, resource_amount)])

    assert req.satisfied(resources, 100.0) == expected


@pytest.mark.parametrize(("has_resource", "expected"), [(False, True), (True, False)])
def test_satisfied_negate(mock_resources, blank_resource_db, has_resource, expected):
    """Test satisfaction with negated resource (resource absent or present)."""
    req = GraphRequirementList()
    resource = mock_resources["item_a"]
    req.add_resource(resource, 1, True)

    resources = blank_resource_db.create_resource_collection()
    if has_resource:
        resources.add_resource_gain([(resource, 1)])

    assert req.satisfied(resources, 100.0) == expected


@pytest.mark.parametrize(("has_item_b", "expected"), [(True, True), (False, False)])
def test_satisfied_multiple(mock_resources, blank_resource_db, has_item_b, expected):
    """Test satisfaction with multiple requirements all met or one missing."""
    req = GraphRequirementList()
    req.add_resource(mock_resources["item_a"], 1, False)
    req.add_resource(mock_resources["item_b"], 3, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(mock_resources["item_a"], 1)])
    if has_item_b:
        resources.add_resource_gain([(mock_resources["item_b"], 5)])

    assert req.satisfied(resources, 100.0) == expected


def test_and_with_empty(mock_resources):
    """Test and_with with empty requirement."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList()

    copied = req1.copy_then_and_with(req2)
    assert req1.and_with(req2)

    assert req1.all_resources() == {mock_resources["item_a"]}
    assert copied == req1


def test_and_with_combine(mock_resources):
    """Test and_with combines requirements."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_b"], 1, False)

    copied = req1.copy_then_and_with(req2)
    assert req1.all_resources() == {mock_resources["item_a"]}

    assert req1.and_with(req2)

    assert req1.all_resources() == {mock_resources["item_a"], mock_resources["item_b"]}
    assert copied == req1


def test_and_with_max_amounts(mock_resources):
    """Test and_with takes max of amounts."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 5, False)

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_a"], 3, False)

    copied = req1.copy_then_and_with(req2)
    assert req1.all_resources() == {mock_resources["item_a"]}
    assert req1.and_with(req2)

    assert req1.get_requirement_for(mock_resources["item_a"]) == (5, False)
    assert copied == req1


def test_and_with_complex_resources(blank_resource_db):
    weapon = blank_resource_db.get_item("Weapon")
    jump = blank_resource_db.get_item("Jump")
    key = blank_resource_db.get_item("BlueKey")
    ammo = blank_resource_db.get_item("Ammo")
    damage = blank_resource_db.get_damage("Damage")

    req1 = GraphRequirementList()
    req1.add_resource(weapon, 1, False)
    req1.add_resource(ammo, 5, False)
    req1.add_resource(key, 1, True)
    req1.add_resource(damage, 100, False)

    req2 = GraphRequirementList()
    req2.add_resource(jump, 1, False)
    req2.add_resource(ammo, 2, False)
    req2.add_resource(damage, 100, False)

    copied = req1.copy_then_and_with(req2)
    assert req1.and_with(req2)

    assert req1 == copied
    requirements = {resource: req1.get_requirement_for(resource) for resource in req1.all_resources()}
    assert requirements == {
        weapon: (1, False),
        jump: (1, False),
        key: (1, True),
        ammo: (5, False),
        damage: (200, False),
    }


def test_str_empty():
    """Test string representation of empty requirement."""
    req = GraphRequirementList()
    assert str(req) == "Trivial"


def test_str_simple(mock_resources):
    """Test string representation with simple requirement."""
    req = GraphRequirementList()
    req.add_resource(mock_resources["item_a"], 1, False)

    assert str(req) == "Missile"


def test_str_multiple(mock_resources):
    """Test string representation with multiple requirements."""
    req = GraphRequirementList()
    req.add_resource(mock_resources["item_a"], 1, False)
    req.add_resource(mock_resources["item_b"], 5, False)

    assert str(req) == "Missile and Health ≥ 5"


def test_complex_requirements_combination(blank_resource_db):
    """Test complex combination of different requirement types."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")
    key = blank_resource_db.get_item("BlueKey")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList()
    req.add_resource(weapon, 1, False)
    req.add_resource(ammo, 5, False)
    req.add_resource(key, 1, True)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain(
        [
            (weapon, 1),
            (ammo, 10),
        ]
    )

    assert not req.satisfied(resources, 50.0)
    assert req.satisfied(resources, 150.0)

    resources.add_resource_gain(
        [
            (key, 1),
        ]
    )
    assert not req.satisfied(resources, 150.0)


def test_copy_then_remove_entries_for_set_resources(blank_resource_db):
    weapon = blank_resource_db.get_item("Weapon")
    key = blank_resource_db.get_item("BlueKey")
    ammo = blank_resource_db.get_item("Ammo")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList()
    req.add_resource(weapon, 1, False)
    req.add_resource(key, 1, False)
    req.add_resource(ammo, 2, False)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain(
        [
            (weapon, 1),
            (ammo, 1),
        ]
    )

    result1 = req.copy_then_remove_entries_for_set_resources(resources)
    assert str(result1) == "Blue Key and Missile ≥ 2 and Normal Damage ≥ 100"

    resources.add_resource_gain(
        [
            (ammo, 1),
        ]
    )
    result2 = req.copy_then_remove_entries_for_set_resources(resources)
    assert str(result2) == "Blue Key and Normal Damage ≥ 100"

    resources.set_resource(key, 0)
    assert req.copy_then_remove_entries_for_set_resources(resources) is None

    resources.set_resource(key, 1)
    result3 = req.copy_then_remove_entries_for_set_resources(resources)
    assert str(result3) == "Normal Damage ≥ 100"


def test_copy_then_remove_entries_for_set_resources_with_same_resource_in_set_and_other(blank_resource_db):
    ammo = blank_resource_db.get_item("Ammo")
    req = GraphRequirementList()
    req.add_resource(ammo, 1, False)
    req.add_resource(ammo, 2, False)
    assert str(req) == "Missile ≥ 2"

    resources = blank_resource_db.create_resource_collection()
    result1 = req.copy_then_remove_entries_for_set_resources(resources)
    assert result1 == req

    resources.add_resource_gain([(ammo, 1)])
    result2 = req.copy_then_remove_entries_for_set_resources(resources)
    assert result2 == req

    resources.add_resource_gain([(ammo, 1)])
    result3 = req.copy_then_remove_entries_for_set_resources(resources)
    assert str(result3) == "Trivial"


def test_is_requirement_superset_empty():
    """Test that empty requirement is a superset of empty requirement."""
    req1 = GraphRequirementList()
    req2 = GraphRequirementList()

    assert req1.is_requirement_superset(req2)


def test_is_requirement_superset_simple_set_resource(mock_resources):
    """Test superset with simple set resources (amount = 1)."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)
    req1.add_resource(mock_resources["item_b"], 1, False)

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_a"], 1, False)

    # req1 requires more than req2, so it's a superset
    assert req1.is_requirement_superset(req2)
    # req2 does not require everything req1 requires
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_identical(mock_resources):
    """Test that identical requirements are supersets of each other."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)
    req1.add_resource(mock_resources["item_b"], 1, False)

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_a"], 1, False)
    req2.add_resource(mock_resources["item_b"], 1, False)

    assert req1.is_requirement_superset(req2)
    assert req2.is_requirement_superset(req1)


def test_is_requirement_superset_negate_resource(mock_resources):
    """Test superset with negated resources."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, True)
    req1.add_resource(mock_resources["item_b"], 1, True)

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_a"], 1, True)

    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_mixed_set_and_negate(mock_resources):
    """Test superset with mix of set and negated resources - catches bug where negate checked against set_bitmask."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)  # set resource
    req1.add_resource(mock_resources["item_b"], 1, True)  # negated resource

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_b"], 1, True)  # only negated resource

    # req1 requires item_a AND NOT item_b
    # req2 requires only NOT item_b
    # So req1 is more restrictive (superset of req2)
    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_negate_not_in_superset(mock_resources):
    """Test that superset fails when subset has negated resource not in superset's negate_bitmask."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)  # set resource, NOT negated

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_a"], 1, True)  # negated resource

    # req1 requires item_a to be present
    # req2 requires item_a to be absent
    # These are incompatible, neither is a superset
    assert not req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_other_resources(mock_resources):
    """Test superset with resources requiring amount > 1."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 5, False)

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_a"], 3, False)

    # req1 requires more of the same resource
    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_other_resources_equal(mock_resources):
    """Test superset when other_resources have equal amounts."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 5, False)

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_a"], 5, False)

    assert req1.is_requirement_superset(req2)
    assert req2.is_requirement_superset(req1)


def test_is_requirement_superset_damage_resources(blank_resource_db):
    """Test superset with damage resources."""
    damage = blank_resource_db.get_damage("Damage")

    req1 = GraphRequirementList()
    req1.add_resource(damage, 150, False)

    req2 = GraphRequirementList()
    req2.add_resource(damage, 100, False)

    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_damage_resources_equal(blank_resource_db):
    """Test superset with equal damage amounts."""
    damage = blank_resource_db.get_damage("Damage")

    req1 = GraphRequirementList()
    req1.add_resource(damage, 100, False)

    req2 = GraphRequirementList()
    req2.add_resource(damage, 100, False)

    assert req1.is_requirement_superset(req2)
    assert req2.is_requirement_superset(req1)


def test_is_requirement_superset_mixed_requirements(blank_resource_db):
    """Test superset with mixed requirement types."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")
    key = blank_resource_db.get_item("BlueKey")
    damage = blank_resource_db.get_damage("Damage")

    req1 = GraphRequirementList()
    req1.add_resource(weapon, 1, False)
    req1.add_resource(ammo, 10, False)
    req1.add_resource(key, 1, True)
    req1.add_resource(damage, 200, False)

    req2 = GraphRequirementList()
    req2.add_resource(weapon, 1, False)
    req2.add_resource(ammo, 5, False)
    req2.add_resource(key, 1, True)
    req2.add_resource(damage, 100, False)

    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_subset_missing_set_resource(mock_resources):
    """Test superset fails when subset has set resource not in superset."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_b"], 1, False)

    assert not req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_subset_missing_negate_resource(mock_resources):
    """Test superset fails when subset has negated resource not in superset."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, True)

    req2 = GraphRequirementList()
    req2.add_resource(mock_resources["item_b"], 1, True)

    assert not req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_empty_subset(mock_resources):
    """Test that non-empty requirement is superset of empty."""
    req1 = GraphRequirementList()
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList()

    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_complex_combination(blank_resource_db):
    """Test superset with complex combination of all requirement types."""
    weapon = blank_resource_db.get_item("Weapon")
    jump = blank_resource_db.get_item("Jump")
    ammo = blank_resource_db.get_item("Ammo")
    health = blank_resource_db.get_item("Health")
    key = blank_resource_db.get_item("BlueKey")
    damage = blank_resource_db.get_damage("Damage")

    req1 = GraphRequirementList()
    req1.add_resource(weapon, 1, False)
    req1.add_resource(jump, 1, False)
    req1.add_resource(ammo, 15, False)
    req1.add_resource(health, 8, False)
    req1.add_resource(key, 1, True)
    req1.add_resource(damage, 300, False)

    req2 = GraphRequirementList()
    req2.add_resource(weapon, 1, False)
    req2.add_resource(ammo, 10, False)
    req2.add_resource(health, 5, False)
    req2.add_resource(key, 1, True)
    req2.add_resource(damage, 200, False)

    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_and_set_with_negate(blank_resource_db):
    weapon = blank_resource_db.get_item("Weapon")

    req1 = GraphRequirementList()
    req1.add_resource(weapon, 1, False)

    req2 = GraphRequirementList()
    req2.add_resource(weapon, 1, True)

    req3 = GraphRequirementList()
    req3.add_resource(weapon, 1, False)
    with pytest.raises(ValueError, match=r"Cannot add resource requirement that conflicts with existing requirements"):
        req3.add_resource(weapon, 1, True)

    result = req1.copy_then_and_with(req2)
    assert result is None

    assert not req1.and_with(req2)


def test_isolate_damage_requirements_empty(blank_resource_db):
    """Test isolate_damage_requirements with empty requirement list."""
    req = GraphRequirementList()
    resources = blank_resource_db.create_resource_collection()

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Trivial"


def test_isolate_damage_requirements_only_damage(blank_resource_db):
    """Test isolate_damage_requirements with only damage requirements."""
    damage = blank_resource_db.get_damage("Damage")
    req = GraphRequirementList()
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Normal Damage ≥ 100"


def test_isolate_damage_requirements_multiple_damage(blank_resource_db):
    """Test isolate_damage_requirements with multiple damage types."""
    damage = blank_resource_db.get_damage("Damage")
    calltrops = blank_resource_db.get_damage("Caltrops")
    req = GraphRequirementList()
    req.add_resource(damage, 50, False)
    req.add_resource(calltrops, 100, False)

    resources = blank_resource_db.create_resource_collection()

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Caltrops Damage ≥ 100 and Normal Damage ≥ 50"


def test_isolate_damage_requirements_with_satisfied_set_resource(blank_resource_db):
    """Test isolate_damage_requirements with satisfied set resource."""
    weapon = blank_resource_db.get_item("Weapon")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList()
    req.add_resource(weapon, 1, False)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(weapon, 1)])

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Normal Damage ≥ 100"


def test_isolate_damage_requirements_with_unsatisfied_set_resource(blank_resource_db):
    """Test isolate_damage_requirements returns None with unsatisfied set resource."""
    weapon = blank_resource_db.get_item("Weapon")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList()
    req.add_resource(weapon, 1, False)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()

    isolated = req.isolate_damage_requirements(resources)

    assert isolated is None


def test_isolate_damage_requirements_with_satisfied_negate_resource(blank_resource_db):
    """Test isolate_damage_requirements with satisfied negate resource (resource absent)."""
    weapon = blank_resource_db.get_item("Weapon")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList()
    req.add_resource(weapon, 1, True)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()
    # weapon is not present, so negation is satisfied

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Normal Damage ≥ 100"


def test_isolate_damage_requirements_with_unsatisfied_negate_resource(blank_resource_db):
    """Test isolate_damage_requirements returns None with unsatisfied negate resource (resource present)."""
    weapon = blank_resource_db.get_item("Weapon")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList()
    req.add_resource(weapon, 1, True)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(weapon, 1)])

    isolated = req.isolate_damage_requirements(resources)

    assert isolated is None


def test_isolate_damage_requirements_with_satisfied_other_resource(blank_resource_db):
    """Test isolate_damage_requirements with satisfied other resource (amount)."""
    ammo = blank_resource_db.get_item("Ammo")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList()
    req.add_resource(ammo, 5, False)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(ammo, 10)])

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Normal Damage ≥ 100"


def test_isolate_damage_requirements_with_unsatisfied_other_resource(blank_resource_db):
    """Test isolate_damage_requirements returns None with unsatisfied other resource."""
    ammo = blank_resource_db.get_item("Ammo")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList()
    req.add_resource(ammo, 10, False)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(ammo, 5)])

    isolated = req.isolate_damage_requirements(resources)

    assert isolated is None


def test_isolate_damage_requirements_complex_all_satisfied(blank_resource_db):
    """Test isolate_damage_requirements with complex requirements, all non-damage satisfied."""
    weapon = blank_resource_db.get_item("Weapon")
    key = blank_resource_db.get_item("BlueKey")
    ammo = blank_resource_db.get_item("Ammo")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList()
    req.add_resource(weapon, 1, False)
    req.add_resource(key, 1, True)
    req.add_resource(ammo, 5, False)
    req.add_resource(damage, 150, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(weapon, 1), (ammo, 10)])

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Normal Damage ≥ 150"


def test_isolate_damage_requirements_no_damage_requirements(blank_resource_db):
    """Test isolate_damage_requirements with no damage requirements returns Trivial when satisfied."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")

    req = GraphRequirementList()
    req.add_resource(weapon, 1, False)
    req.add_resource(ammo, 5, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(weapon, 1), (ammo, 10)])

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Trivial"


def test_isolate_damage_requirements_no_damage_requirements_unsatisfied(blank_resource_db):
    """Test isolate_damage_requirements with no damage requirements returns None when unsatisfied."""
    weapon = blank_resource_db.get_item("Weapon")

    req = GraphRequirementList()
    req.add_resource(weapon, 1, False)

    resources = blank_resource_db.create_resource_collection()

    isolated = req.isolate_damage_requirements(resources)

    assert isolated is None


def test_isolate_damage_requirements_with_reduction(blank_resource_db):
    """Test isolate_damage_requirements with complex requirements, all non-damage satisfied."""
    double_jump = blank_resource_db.get_item("DoubleJump")
    damage = blank_resource_db.get_damage("Caltrops")

    req = GraphRequirementList()
    req.add_resource(damage, 150, False)

    resources = blank_resource_db.create_resource_collection()
    isolated1 = req.isolate_damage_requirements(resources)
    assert str(isolated1) == "Caltrops Damage ≥ 150"

    resources.add_resource_gain([(double_jump, 1)])
    isolated2 = req.isolate_damage_requirements(resources)
    assert str(isolated2) == "Trivial"
