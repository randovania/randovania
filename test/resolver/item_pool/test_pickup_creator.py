import pytest

import randovania.generator.item_pool.ammo
import randovania.generator.item_pool.pickup_creator
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.pickup_entry import ConditionalResources, ResourceConversion, PickupEntry
from randovania.layout.major_item_state import MajorItemState


@pytest.mark.parametrize("percentage", [False, True])
@pytest.mark.parametrize("has_convert", [False, True])
def test_create_pickup_for(percentage: bool, has_convert: bool, echoes_resource_database):
    # Setup
    item_a = echoes_resource_database.get_item(10)
    item_b = echoes_resource_database.get_item(15)
    item_c = echoes_resource_database.get_item(18)
    ammo_a = echoes_resource_database.get_item(40)
    ammo_b = echoes_resource_database.get_item(42)
    temporary_a = echoes_resource_database.get_item(71)
    temporary_b = echoes_resource_database.get_item(72)

    major_item = MajorItem(
        name="The Item",
        item_category=ItemCategory.MORPH_BALL,
        broad_category=ItemCategory.MORPH_BALL_RELATED,
        model_index=1337,
        progression=(10, 15, 18),
        ammo_index=(40, 42),
        converts_indices=(71, 72) if has_convert else (),
        required=False,
        original_index=None,
        probability_offset=5,
    )
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(10, 20),
    )

    def _create_resources(item):
        if percentage:
            return (
                (item, 1),
                (ammo_a, 10),
                (ammo_b, 20),
                (echoes_resource_database.item_percentage, 1),
            )
        else:
            return (
                (item, 1),
                (ammo_a, 10),
                (ammo_b, 20),
            )

    # Run
    result = randovania.generator.item_pool.pickup_creator.create_major_item(major_item, state, percentage,
                                                                             echoes_resource_database,
                                                                             None, False)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model_index=1337,
        resources=(
            ConditionalResources(
                name="Dark Visor",
                item=None,
                resources=_create_resources(item_a),
            ),
            ConditionalResources(
                name="Morph Ball",
                item=item_a,
                resources=_create_resources(item_b),
            ),
            ConditionalResources(
                name="Morph Ball Bomb",
                item=item_b,
                resources=_create_resources(item_c),
            ),
        ),
        convert_resources=(
            ResourceConversion(source=temporary_a, target=ammo_a),
            ResourceConversion(source=temporary_b, target=ammo_b),
        ) if has_convert else (),
        item_category=ItemCategory.MORPH_BALL,
        broad_category=ItemCategory.MORPH_BALL_RELATED,
        probability_offset=5,
    )


@pytest.mark.parametrize(["ammo_quantity"], [
    (0,),
    (10,),
    (15,),
])
def test_create_missile_launcher(ammo_quantity: int, echoes_item_database, echoes_resource_database):
    # Setup
    missile = echoes_resource_database.get_item(44)
    missile_launcher = echoes_resource_database.get_item(73)
    temporary = echoes_resource_database.get_item(71)

    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = randovania.generator.item_pool.pickup_creator.create_major_item(
        echoes_item_database.major_items["Missile Launcher"],
        state,
        True,
        echoes_resource_database,
        echoes_item_database.ammo["Missile Expansion"],
        True
    )

    # Assert
    assert result == PickupEntry(
        name="Missile Launcher",
        resources=(
            ConditionalResources(
                "Missile Launcher", None,
                resources=(
                    (missile_launcher, 1),
                    (missile, ammo_quantity),
                    (echoes_resource_database.item_percentage, 1),
                )
            ),
        ),
        convert_resources=(
            ResourceConversion(source=temporary, target=missile),
        ),
        model_index=24,
        item_category=ItemCategory.MISSILE,
        broad_category=ItemCategory.MISSILE_RELATED,
    )


@pytest.mark.parametrize("ammo_quantity", [0, 10, 15])
@pytest.mark.parametrize("ammo_requires_major_item", [False, True])
def test_create_seeker_launcher(ammo_quantity: int,
                                ammo_requires_major_item: bool,
                                echoes_item_database,
                                echoes_resource_database,
                                ):
    # Setup
    missile = echoes_resource_database.get_item(44)
    missile_launcher = echoes_resource_database.get_item(73)
    seeker_launcher = echoes_resource_database.get_item(26)
    temporary = echoes_resource_database.get_item(71)

    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = randovania.generator.item_pool.pickup_creator.create_major_item(
        echoes_item_database.major_items["Seeker Launcher"],
        state,
        True,
        echoes_resource_database,
        echoes_item_database.ammo["Missile Expansion"],
        ammo_requires_major_item
    )

    # Assert
    locked_conditional = (
        ConditionalResources(
            "Seeker Launcher", None,
            resources=(
                (seeker_launcher, 1),
                (temporary, ammo_quantity),
                (echoes_resource_database.item_percentage, 1),
            )
        ),
        ConditionalResources(
            "Seeker Launcher", missile_launcher,
            resources=(
                (seeker_launcher, 1),
                (missile, ammo_quantity),
                (echoes_resource_database.item_percentage, 1),
            )
        ),
    )
    normal_resources = (
        ConditionalResources(
            "Seeker Launcher", None,
            resources=(
                (seeker_launcher, 1),
                (missile, ammo_quantity),
                (echoes_resource_database.item_percentage, 1),
            )
        ),
    )

    assert result == PickupEntry(
        name="Seeker Launcher",
        resources=locked_conditional if ammo_requires_major_item else normal_resources,
        model_index=25,
        item_category=ItemCategory.MISSILE,
        broad_category=ItemCategory.MISSILE_RELATED,
    )


@pytest.mark.parametrize("requires_major_item", [False, True])
def test_create_ammo_expansion(requires_major_item: bool, echoes_resource_database):
    # Setup
    primary_a = echoes_resource_database.get_item(73)
    ammo_a = echoes_resource_database.get_item(40)
    ammo_b = echoes_resource_database.get_item(42)
    temporary_a = echoes_resource_database.get_item(71)
    temporary_b = echoes_resource_database.get_item(72)

    ammo = Ammo(
        name="The Item",
        maximum=100,
        items=(40, 42),
        broad_category=ItemCategory.ETM,
        unlocked_by=73,
        temporaries=(71, 72),
        models=(10, 20),
    )
    ammo_count = [75, 150]

    item_resources = (
        (ammo_a, ammo_count[0]),
        (ammo_b, ammo_count[1]),
        (echoes_resource_database.item_percentage, 1),
    )
    temporary_resources = (
        (temporary_a, ammo_count[0]),
        (temporary_b, ammo_count[1]),
        (echoes_resource_database.item_percentage, 1),
    )

    # Run
    result = randovania.generator.item_pool.pickup_creator.create_ammo_expansion(
        ammo, ammo_count, requires_major_item, echoes_resource_database)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model_index=10,
        resources=(
            ConditionalResources("Temporary Missile", None, temporary_resources),
            ConditionalResources("The Item", primary_a, item_resources),
        ) if requires_major_item else (
            ConditionalResources(None, None, item_resources),
        ),
        item_category=ItemCategory.EXPANSION,
        broad_category=ItemCategory.ETM,
        probability_offset=0,
    )
