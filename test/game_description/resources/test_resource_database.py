import pytest


@pytest.mark.parametrize(
    ("quantity", "expected_mulitplier"),
    [
        (0, 1.0),
        (1, 0.5),
        (2, 0.0),
        (3, 0.0),
    ],
)
def test_get_damage_reduction(blank_resource_db, quantity, expected_mulitplier) -> None:
    """Test that get_damage_reduction properly handles quantity."""
    jump = blank_resource_db.get_item("Jump")
    damage = blank_resource_db.get_damage("Caltrops")
    resources = blank_resource_db.create_resource_collection()

    # Add the quantity of Jumps to our resources
    resources.add_resource_gain([(jump, quantity)])

    # Get the multiplier for the given amount of Jump upgrades
    multiplier = blank_resource_db.get_damage_reduction(damage, resources)

    assert multiplier == expected_mulitplier
