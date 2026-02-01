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


def test_create_empty(blank_resource_db):
    """Test creating an empty requirement list."""
    req = GraphRequirementList(blank_resource_db)
    assert req.all_resources() == set()


@pytest.mark.parametrize(
    ("amount", "negate", "expected_str"),
    [
        (1, False, "Missile"),
        (1, True, "No Missile"),
        (5, False, "Missile ≥ 5"),
    ],
)
def test_add_resource(mock_resources, blank_resource_db, amount, negate, expected_str):
    """Test adding resource requirements with different amounts and negation."""
    req = GraphRequirementList(blank_resource_db)
    resource = mock_resources["item_a"]

    req.add_resource(resource, amount, negate)

    assert req.all_resources() == {resource}
    assert req.get_requirement_for(resource) == (amount, negate)
    assert str(req) == expected_str


def test_cant_add_resource_when_frozen(mock_resources, blank_resource_db):
    """Test adding a resource when the list is frozen."""
    req = GraphRequirementList(blank_resource_db)
    resource = mock_resources["item_a"]

    req.freeze()
    with pytest.raises(RuntimeError, match=r"Cannot modify a frozen GraphRequirementList"):
        req.add_resource(resource, 1, False)

    assert req.all_resources() == set()


def test_add_resource_amount_zero_ignored(mock_resources, blank_resource_db):
    """Test that adding a resource with amount 0 is ignored."""
    req = GraphRequirementList(blank_resource_db)
    resource = mock_resources["item_a"]

    req.add_resource(resource, 0, False)

    assert req.all_resources() == set()


def test_add_multiple_resources(mock_resources, blank_resource_db):
    """Test adding multiple different resources."""
    req = GraphRequirementList(blank_resource_db)

    req.add_resource(mock_resources["item_a"], 1, False)
    req.add_resource(mock_resources["item_b"], 3, False)

    assert req.all_resources() == {mock_resources["item_a"], mock_resources["item_b"]}


def test_add_resource_max_amount(mock_resources, blank_resource_db):
    """Test that adding the same resource twice takes the max amount."""
    req = GraphRequirementList(blank_resource_db)
    resource = mock_resources["item_a"]

    req.add_resource(resource, 5, False)
    req.add_resource(resource, 3, False)

    assert req.get_requirement_for(resource) == (5, False)


@pytest.mark.parametrize(
    ("add_to_req1", "add_to_req2", "should_equal"),
    [
        ([], [], True),  # Both empty
        ([("item_a", 1, False)], [("item_a", 1, False)], True),  # Same requirements
        ([("item_a", 1, False)], [("item_b", 1, False)], False),  # Different requirements
    ],
)
def test_equality(mock_resources, blank_resource_db, add_to_req1, add_to_req2, should_equal):
    """Test equality/inequality of requirement lists."""
    req1 = GraphRequirementList(blank_resource_db)
    req2 = GraphRequirementList(blank_resource_db)

    for item_key, amount, negate in add_to_req1:
        req1.add_resource(mock_resources[item_key], amount, negate)
    for item_key, amount, negate in add_to_req2:
        req2.add_resource(mock_resources[item_key], amount, negate)

    if should_equal:
        assert req1 == req2
        assert req1.equals_to(req2)
    else:
        assert req1 != req2


def test_hash_consistency(mock_resources, blank_resource_db):
    """Test that equal requirement lists have the same hash."""
    req1 = GraphRequirementList(blank_resource_db)
    req2 = GraphRequirementList(blank_resource_db)

    resource = mock_resources["item_a"]
    req1.add_resource(resource, 1, False)
    req2.add_resource(resource, 1, False)

    req1.freeze()
    req2.freeze()

    assert hash(req1) == hash(req2)


def test_copy_simple(mock_resources, blank_resource_db):
    """Test copying a requirement list."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)
    req1.add_resource(mock_resources["item_b"], 3, False)

    req2 = copy.copy(req1)

    assert req1.equals_to(req2)
    assert req1 == req2


def test_copy_independence(mock_resources, blank_resource_db):
    """Test that copied requirement lists are independent."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = copy.copy(req1)
    req2.add_resource(mock_resources["item_b"], 1, False)

    assert req2.all_resources() == {mock_resources["item_a"], mock_resources["item_b"]}
    assert req1.all_resources() == {mock_resources["item_a"]}


def test_get_requirement_for_missing(mock_resources, blank_resource_db):
    """Test get_requirement_for with resource not in list."""
    req = GraphRequirementList(blank_resource_db)

    assert req.get_requirement_for(mock_resources["item_a"]) == (0, False)


def test_satisfied_empty(blank_resource_db):
    """Test that empty requirement list is always satisfied."""
    req = GraphRequirementList(blank_resource_db)
    resources = blank_resource_db.create_resource_collection()

    assert req.satisfied(resources, 100.0)


@pytest.mark.parametrize(("has_resource", "expected"), [(True, True), (False, False)])
def test_satisfied_simple(mock_resources, blank_resource_db, has_resource, expected):
    """Test satisfaction when resource is present or missing."""
    req = GraphRequirementList(blank_resource_db)
    resource = mock_resources["item_a"]
    req.add_resource(resource, 1, False)

    resources = blank_resource_db.create_resource_collection()
    if has_resource:
        resources.add_resource_gain([(resource, 1)])

    assert req.satisfied(resources, 100.0) == expected


@pytest.mark.parametrize(("resource_amount", "expected"), [(10, True), (3, False)])
def test_satisfied_amount(mock_resources, blank_resource_db, resource_amount, expected):
    """Test satisfaction with sufficient or insufficient amount."""
    req = GraphRequirementList(blank_resource_db)
    resource = mock_resources["item_a"]
    req.add_resource(resource, 5, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(resource, resource_amount)])

    assert req.satisfied(resources, 100.0) == expected


@pytest.mark.parametrize(("has_resource", "expected"), [(False, True), (True, False)])
def test_satisfied_negate(mock_resources, blank_resource_db, has_resource, expected):
    """Test satisfaction with negated resource (resource absent or present)."""
    req = GraphRequirementList(blank_resource_db)
    resource = mock_resources["item_a"]
    req.add_resource(resource, 1, True)

    resources = blank_resource_db.create_resource_collection()
    if has_resource:
        resources.add_resource_gain([(resource, 1)])

    assert req.satisfied(resources, 100.0) == expected


@pytest.mark.parametrize(("has_item_b", "expected"), [(True, True), (False, False)])
def test_satisfied_multiple(mock_resources, blank_resource_db, has_item_b, expected):
    """Test satisfaction with multiple requirements all met or one missing."""
    req = GraphRequirementList(blank_resource_db)
    req.add_resource(mock_resources["item_a"], 1, False)
    req.add_resource(mock_resources["item_b"], 3, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(mock_resources["item_a"], 1)])
    if has_item_b:
        resources.add_resource_gain([(mock_resources["item_b"], 5)])

    assert req.satisfied(resources, 100.0) == expected


def test_and_with_empty(mock_resources, blank_resource_db):
    """Test and_with with empty requirement."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList(blank_resource_db)

    copied = req1.copy_then_and_with(req2)
    assert req1.and_with(req2)

    assert req1.all_resources() == {mock_resources["item_a"]}
    assert copied == req1


def test_and_with_combine(mock_resources, blank_resource_db):
    """Test and_with combines requirements."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_b"], 1, False)

    copied = req1.copy_then_and_with(req2)
    assert req1.all_resources() == {mock_resources["item_a"]}

    assert req1.and_with(req2)

    assert req1.all_resources() == {mock_resources["item_a"], mock_resources["item_b"]}
    assert copied == req1


def test_and_with_max_amounts(mock_resources, blank_resource_db):
    """Test and_with takes max of amounts."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 5, False)

    req2 = GraphRequirementList(blank_resource_db)
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

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 1, False)
    req1.add_resource(ammo, 5, False)
    req1.add_resource(key, 1, True)
    req1.add_resource(damage, 100, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(jump, 1, False)
    req2.add_resource(ammo, 2, False)
    req2.add_resource(damage, 100, False)

    assert str(req1) == "Weapon and No Blue Key and Missile ≥ 5 and Normal Damage ≥ 100"
    assert str(req2) == "Jump and Missile ≥ 2 and Normal Damage ≥ 100"

    copied = req1.copy_then_and_with(req2)

    assert str(req1) == "Weapon and No Blue Key and Missile ≥ 5 and Normal Damage ≥ 100"
    assert str(req2) == "Jump and Missile ≥ 2 and Normal Damage ≥ 100"
    assert str(copied) == "Jump and Weapon and No Blue Key and Missile ≥ 5 and Normal Damage ≥ 200"

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


def test_copy_then_and_with_independence(blank_resource_db):
    """Test that copy_then_and_with creates truly independent copies."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")
    jump = blank_resource_db.get_item("Jump")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 5, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(ammo, 3, False)

    # Create a copy using copy_then_and_with
    copied = req1.copy_then_and_with(req2)

    # Verify initial state
    assert copied.get_requirement_for(weapon, False) == (5, False)
    assert copied.get_requirement_for(ammo, False) == (3, False)

    # Now modify req1 by adding more resources
    req1.add_resource(jump, 2, False)

    # The copied version should NOT be affected
    assert copied.get_requirement_for(jump, False) == (0, False)
    assert copied.get_requirement_for(weapon, False) == (5, False)

    # And modifying req2 shouldn't affect the copy either
    req2.add_resource(weapon, 10, False)  # This changes ammo count in req2

    # Verify copied is still independent
    assert copied.get_requirement_for(ammo, False) == (3, False)
    assert copied.get_requirement_for(weapon, False) == (5, False)


def test_copy_then_and_with_vector_mutation(blank_resource_db):
    """Test that copy_then_and_with doesn't share mutable vector state."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 5, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(ammo, 3, False)

    # Store the original values via the public API
    req1_weapon_before = req1.get_requirement_for(weapon, False)

    # Create a copy using copy_then_and_with
    copied = req1.copy_then_and_with(req2)

    # Verify req1's values are unchanged via public API
    req1_weapon_after = req1.get_requirement_for(weapon, False)
    assert req1_weapon_before == req1_weapon_after

    # Verify the copied has both resources
    assert copied.get_requirement_for(weapon, False) == (5, False)
    assert copied.get_requirement_for(ammo, False) == (3, False)


def test_and_with_multiple_times(blank_resource_db):
    """Test that and_with can be called multiple times without corruption."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")
    jump = blank_resource_db.get_item("Jump")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 2, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(ammo, 3, False)

    req3 = GraphRequirementList(blank_resource_db)
    req3.add_resource(jump, 1, False)

    # Call and_with multiple times
    assert req1.and_with(req2)
    assert req1.get_requirement_for(weapon, False) == (2, False)
    assert req1.get_requirement_for(ammo, False) == (3, False)

    assert req1.and_with(req3)
    assert req1.get_requirement_for(weapon, False) == (2, False)
    assert req1.get_requirement_for(ammo, False) == (3, False)
    assert req1.get_requirement_for(jump, False) == (1, False)

    # Now test with amounts > 1
    req4 = GraphRequirementList(blank_resource_db)
    req4.add_resource(weapon, 5, False)  # Should update to max(2, 5) = 5

    assert req1.and_with(req4)
    assert req1.get_requirement_for(weapon, False) == (5, False)
    assert req1.get_requirement_for(ammo, False) == (3, False)
    assert req1.get_requirement_for(jump, False) == (1, False)


def test_damage_resource_copy_independence(blank_resource_db):
    """Test that damage resources are properly copied and independent."""
    damage = blank_resource_db.get_damage("Damage")
    weapon = blank_resource_db.get_item("Weapon")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(damage, 50, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(weapon, 1, False)
    req2.add_resource(damage, 30, False)

    # Use copy_then_and_with
    copied = req1.copy_then_and_with(req2)

    # Verify damage is combined (50 + 30 = 80 for damage resources)
    assert copied.get_requirement_for(damage, True) == (80, False)

    # Now modify req1's damage
    req1.add_resource(damage, 20, False)  # This adds 20 more, so req1 now has 70 total

    # copied should still have 80, not be affected
    assert copied.get_requirement_for(damage, True) == (80, False)
    assert req1.get_requirement_for(damage, True) == (70, False)


def test_and_with_mutation_independence(blank_resource_db):
    """Test that and_with doesn't mutate through shared Pair references."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 5, False)
    req1.add_resource(ammo, 3, False)

    # Store the original values
    original_weapon_amount = req1.get_requirement_for(weapon, False)[0]
    original_ammo_amount = req1.get_requirement_for(ammo, False)[0]

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(weapon, 10, False)  # This should update to max(5, 10) = 10

    # Use copy_then_and_with
    copied = req1.copy_then_and_with(req2)

    # Verify copied has the max
    assert copied.get_requirement_for(weapon, False) == (10, False)
    assert copied.get_requirement_for(ammo, False) == (3, False)

    # Verify req1 is UNCHANGED - this is the key test
    assert req1.get_requirement_for(weapon, False) == (original_weapon_amount, False)
    assert req1.get_requirement_for(ammo, False) == (original_ammo_amount, False)


def test_copy_then_and_with_does_not_mutate_original_vectors(blank_resource_db):
    """Test that copy_then_and_with creates independent copies."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 5, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(ammo, 3, False)

    # Store the original values
    req1_weapon_original = req1.get_requirement_for(weapon, False)

    # Create a copy using copy_then_and_with
    copied = req1.copy_then_and_with(req2)

    # Verify req1's values weren't mutated during the copy
    req1_weapon_after = req1.get_requirement_for(weapon, False)
    assert req1_weapon_original == req1_weapon_after

    # Verify the copied has the correct values
    assert copied.get_requirement_for(weapon, False) == (5, False)
    assert copied.get_requirement_for(ammo, False) == (3, False)

    # Verify req1 still has only weapon, not ammo
    assert req1.get_requirement_for(ammo, False) == (0, False)


@pytest.mark.parametrize(
    ("resources_to_add", "expected_str"),
    [
        ([], "Trivial"),
        ([("item_a", 1, False)], "Missile"),
        ([("item_a", 1, False), ("item_b", 5, False)], "Missile and Health ≥ 5"),
    ],
)
def test_str_representation(mock_resources, blank_resource_db, resources_to_add, expected_str):
    """Test string representation with various requirements."""
    req = GraphRequirementList(blank_resource_db)
    for item_key, amount, negate in resources_to_add:
        req.add_resource(mock_resources[item_key], amount, negate)

    assert str(req) == expected_str


def test_complex_requirements_combination(blank_resource_db):
    """Test complex combination of different requirement types."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")
    key = blank_resource_db.get_item("BlueKey")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList(blank_resource_db)
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

    req = GraphRequirementList(blank_resource_db)
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
    req = GraphRequirementList(blank_resource_db)
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


def test_is_requirement_superset_empty(blank_resource_db):
    """Test that empty requirement is a superset of empty requirement."""
    req1 = GraphRequirementList(blank_resource_db)
    req2 = GraphRequirementList(blank_resource_db)

    assert req1.is_requirement_superset(req2)


def test_is_requirement_superset_simple_set_resource(mock_resources, blank_resource_db):
    """Test superset with simple set resources (amount = 1)."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)
    req1.add_resource(mock_resources["item_b"], 1, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_a"], 1, False)

    # req1 requires more than req2, so it's a superset
    assert req1.is_requirement_superset(req2)
    # req2 does not require everything req1 requires
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_identical(mock_resources, blank_resource_db):
    """Test that identical requirements are supersets of each other."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)
    req1.add_resource(mock_resources["item_b"], 1, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_a"], 1, False)
    req2.add_resource(mock_resources["item_b"], 1, False)

    assert req1.is_requirement_superset(req2)
    assert req2.is_requirement_superset(req1)


def test_is_requirement_superset_negate_resource(mock_resources, blank_resource_db):
    """Test superset with negated resources."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, True)
    req1.add_resource(mock_resources["item_b"], 1, True)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_a"], 1, True)

    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_mixed_set_and_negate(mock_resources, blank_resource_db):
    """Test superset with mix of set and negated resources - catches bug where negate checked against set_bitmask."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)  # set resource
    req1.add_resource(mock_resources["item_b"], 1, True)  # negated resource

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_b"], 1, True)  # only negated resource

    # req1 requires item_a AND NOT item_b
    # req2 requires only NOT item_b
    # So req1 is more restrictive (superset of req2)
    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_negate_not_in_superset(mock_resources, blank_resource_db):
    """Test that superset fails when subset has negated resource not in superset's negate_bitmask."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)  # set resource, NOT negated

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_a"], 1, True)  # negated resource

    # req1 requires item_a to be present
    # req2 requires item_a to be absent
    # These are incompatible, neither is a superset
    assert not req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


@pytest.mark.parametrize(
    ("req1_amount", "req2_amount", "req1_is_superset", "req2_is_superset"),
    [
        (5, 3, True, False),  # req1 requires more
        (5, 5, True, True),  # Equal amounts
    ],
)
def test_is_requirement_superset_other_resources(
    mock_resources, blank_resource_db, req1_amount, req2_amount, req1_is_superset, req2_is_superset
):
    """Test superset with resources requiring various amounts."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], req1_amount, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_a"], req2_amount, False)

    assert req1.is_requirement_superset(req2) == req1_is_superset
    assert req2.is_requirement_superset(req1) == req2_is_superset


@pytest.mark.parametrize(
    ("req1_amount", "req2_amount", "req1_is_superset", "req2_is_superset"),
    [
        (150, 100, True, False),  # req1 requires more damage
        (100, 100, True, True),  # Equal damage amounts
    ],
)
def test_is_requirement_superset_damage_resources(
    blank_resource_db, req1_amount, req2_amount, req1_is_superset, req2_is_superset
):
    """Test superset with damage resources at various amounts."""
    damage = blank_resource_db.get_damage("Damage")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(damage, req1_amount, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(damage, req2_amount, False)

    assert req1.is_requirement_superset(req2) == req1_is_superset
    assert req2.is_requirement_superset(req1) == req2_is_superset


def test_is_requirement_superset_mixed_requirements(blank_resource_db):
    """Test superset with mixed requirement types."""
    weapon = blank_resource_db.get_item("Weapon")
    ammo = blank_resource_db.get_item("Ammo")
    key = blank_resource_db.get_item("BlueKey")
    damage = blank_resource_db.get_damage("Damage")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 1, False)
    req1.add_resource(ammo, 10, False)
    req1.add_resource(key, 1, True)
    req1.add_resource(damage, 200, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(weapon, 1, False)
    req2.add_resource(ammo, 5, False)
    req2.add_resource(key, 1, True)
    req2.add_resource(damage, 100, False)

    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_subset_missing_set_resource(mock_resources, blank_resource_db):
    """Test superset fails when subset has set resource not in superset."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_b"], 1, False)

    assert not req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_subset_missing_negate_resource(mock_resources, blank_resource_db):
    """Test superset fails when subset has negated resource not in superset."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, True)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_b"], 1, True)

    assert not req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_is_requirement_superset_empty_subset(mock_resources, blank_resource_db):
    """Test that non-empty requirement is superset of empty."""
    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)

    req2 = GraphRequirementList(blank_resource_db)

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

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 1, False)
    req1.add_resource(jump, 1, False)
    req1.add_resource(ammo, 15, False)
    req1.add_resource(health, 8, False)
    req1.add_resource(key, 1, True)
    req1.add_resource(damage, 300, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(weapon, 1, False)
    req2.add_resource(ammo, 10, False)
    req2.add_resource(health, 5, False)
    req2.add_resource(key, 1, True)
    req2.add_resource(damage, 200, False)

    assert req1.is_requirement_superset(req2)
    assert not req2.is_requirement_superset(req1)


def test_and_set_with_negate(blank_resource_db):
    weapon = blank_resource_db.get_item("Weapon")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(weapon, 1, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(weapon, 1, True)

    req3 = GraphRequirementList(blank_resource_db)
    req3.add_resource(weapon, 1, False)
    with pytest.raises(ValueError, match=r"Cannot add resource requirement that conflicts with existing requirements"):
        req3.add_resource(weapon, 1, True)

    result = req1.copy_then_and_with(req2)
    assert result is None

    assert not req1.and_with(req2)


def test_isolate_damage_requirements_empty(blank_resource_db):
    """Test isolate_damage_requirements with empty requirement list."""
    req = GraphRequirementList(blank_resource_db)
    resources = blank_resource_db.create_resource_collection()

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Trivial"


def test_isolate_damage_requirements_only_damage(blank_resource_db):
    """Test isolate_damage_requirements with only damage requirements."""
    damage = blank_resource_db.get_damage("Damage")
    req = GraphRequirementList(blank_resource_db)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Normal Damage ≥ 100"


def test_isolate_damage_requirements_multiple_damage(blank_resource_db):
    """Test isolate_damage_requirements with multiple damage types."""
    damage = blank_resource_db.get_damage("Damage")
    calltrops = blank_resource_db.get_damage("Caltrops")
    req = GraphRequirementList(blank_resource_db)
    req.add_resource(damage, 50, False)
    req.add_resource(calltrops, 100, False)

    resources = blank_resource_db.create_resource_collection()

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Caltrops Damage ≥ 100 and Normal Damage ≥ 50"


@pytest.mark.parametrize(
    ("resource_type", "resource_name", "req_amount", "negate", "provided_amount", "expected_result"),
    [
        ("item", "Weapon", 1, False, 1, "Normal Damage ≥ 100"),  # Satisfied set resource
        ("item", "Weapon", 1, False, 0, None),  # Unsatisfied set resource
        ("item", "Weapon", 1, True, 0, "Normal Damage ≥ 100"),  # Satisfied negate resource (absent)
        ("item", "Weapon", 1, True, 1, None),  # Unsatisfied negate resource (present)
        ("item", "Ammo", 5, False, 10, "Normal Damage ≥ 100"),  # Satisfied other resource (sufficient)
        ("item", "Ammo", 10, False, 5, None),  # Unsatisfied other resource (insufficient)
    ],
)
def test_isolate_damage_requirements_with_non_damage_resources(
    blank_resource_db, resource_type, resource_name, req_amount, negate, provided_amount, expected_result
):
    """Test isolate_damage_requirements with various non-damage resource satisfaction states."""
    resource = blank_resource_db.get_item(resource_name)
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList(blank_resource_db)
    req.add_resource(resource, req_amount, negate)
    req.add_resource(damage, 100, False)

    resources = blank_resource_db.create_resource_collection()
    if provided_amount > 0:
        resources.add_resource_gain([(resource, provided_amount)])

    isolated = req.isolate_damage_requirements(resources)

    if expected_result is None:
        assert isolated is None
    else:
        assert str(isolated) == expected_result


def test_isolate_damage_requirements_complex_all_satisfied(blank_resource_db):
    """Test isolate_damage_requirements with complex requirements, all non-damage satisfied."""
    weapon = blank_resource_db.get_item("Weapon")
    key = blank_resource_db.get_item("BlueKey")
    ammo = blank_resource_db.get_item("Ammo")
    damage = blank_resource_db.get_damage("Damage")

    req = GraphRequirementList(blank_resource_db)
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

    req = GraphRequirementList(blank_resource_db)
    req.add_resource(weapon, 1, False)
    req.add_resource(ammo, 5, False)

    resources = blank_resource_db.create_resource_collection()
    resources.add_resource_gain([(weapon, 1), (ammo, 10)])

    isolated = req.isolate_damage_requirements(resources)

    assert str(isolated) == "Trivial"


def test_isolate_damage_requirements_no_damage_requirements_unsatisfied(blank_resource_db):
    """Test isolate_damage_requirements with no damage requirements returns None when unsatisfied."""
    weapon = blank_resource_db.get_item("Weapon")

    req = GraphRequirementList(blank_resource_db)
    req.add_resource(weapon, 1, False)

    resources = blank_resource_db.create_resource_collection()

    isolated = req.isolate_damage_requirements(resources)

    assert isolated is None


def test_isolate_damage_requirements_with_reduction(blank_resource_db):
    """Test isolate_damage_requirements with complex requirements, all non-damage satisfied."""
    double_jump = blank_resource_db.get_item("DoubleJump")
    damage = blank_resource_db.get_damage("Caltrops")

    req = GraphRequirementList(blank_resource_db)
    req.add_resource(damage, 150, False)

    resources = blank_resource_db.create_resource_collection()
    isolated1 = req.isolate_damage_requirements(resources)
    assert str(isolated1) == "Caltrops Damage ≥ 150"

    resources.add_resource_gain([(double_jump, 1)])
    isolated2 = req.isolate_damage_requirements(resources)
    assert str(isolated2) == "Trivial"


def test_hash(mock_resources, blank_resource_db):
    """Test that the hash function is consistent and unique for different requirements."""
    damage = blank_resource_db.get_damage("Damage")

    req1 = GraphRequirementList(blank_resource_db)
    req1.add_resource(mock_resources["item_a"], 1, False)
    req1.add_resource(mock_resources["item_b"], 3, False)
    req1.add_resource(damage, 100, False)

    req2 = GraphRequirementList(blank_resource_db)
    req2.add_resource(mock_resources["item_a"], 1, False)
    req2.add_resource(mock_resources["item_b"], 3, False)
    req2.add_resource(damage, 100, False)

    req3 = GraphRequirementList(blank_resource_db)
    req3.add_resource(mock_resources["item_a"], 2, False)
    req3.add_resource(mock_resources["item_b"], 3, False)
    req3.add_resource(damage, 100, False)

    req4 = copy.copy(req1)
    req4.add_resource(damage, 100, False)

    req1.freeze()
    req2.freeze()
    req3.freeze()
    req4.freeze()

    assert hash(req1) == hash(req2)
    assert hash(req1) != hash(req3)
    assert hash(req1) != hash(req4)
