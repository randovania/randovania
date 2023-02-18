from randovania.generator.item_pool import pickup_creator


def test_assign_extra_pickups(empty_patches):
    # Setup
    sample_pickup = pickup_creator.create_visual_etm()

    # Run
    new_patches = empty_patches.assign_extra_starting_pickups([
        sample_pickup,
    ])

    # Assert
    assert new_patches.starting_equipment == [sample_pickup]
