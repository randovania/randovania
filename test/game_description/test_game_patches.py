from __future__ import annotations

from randovania.generator.pickup_pool import pickup_creator


def test_assign_extra_pickups(empty_patches):
    # Setup
    sample_pickup = pickup_creator.create_visual_nothing(empty_patches.game.game, "Visual Nothing")

    # Run
    new_patches = empty_patches.assign_extra_starting_pickups(
        [
            sample_pickup,
        ]
    )

    # Assert
    assert new_patches.starting_equipment == [sample_pickup]
