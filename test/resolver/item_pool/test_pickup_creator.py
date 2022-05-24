import pytest

from randovania.game_description.item.ammo import AMMO_ITEM_CATEGORY, Ammo
from randovania.game_description.item.item_category import USELESS_ITEM_CATEGORY, ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.pickup_entry import (
    PickupEntry,
    ResourceLock,
    PickupModel,
)
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.generator.item_pool import pickup_creator
from randovania.layout.base.major_item_state import MajorItemState


@pytest.mark.parametrize("percentage", [False, True])
def test_create_pickup_for(percentage: bool, echoes_item_database, echoes_resource_database, generic_item_category):
    # Setup
    item_a = echoes_resource_database.get_item("DarkVisor")
    item_b = echoes_resource_database.get_item("MorphBall")
    item_c = echoes_resource_database.get_item("Bombs")
    ammo_a = echoes_resource_database.get_item("EnergyTank")
    ammo_b = echoes_resource_database.get_item("DarkAmmo")

    less_generic_item_category = ItemCategory(
        name="the_category",
        long_name="The Category",
        hint_details=("a ", " wonderful item"),
        is_major=True
    )

    major_item = MajorItem(
        game=echoes_resource_database.game_enum,
        name="The Item",
        item_category=less_generic_item_category,
        broad_category=generic_item_category,
        model_name="SuperModel",
        progression=("DarkVisor", "MorphBall", "Bombs"),
        default_starting_count=0,
        default_shuffled_count=1,
        ammo_index=("EnergyTank", "DarkAmmo"),
        must_be_starting=False,
        original_index=None,
        probability_offset=5,
    )
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(10, 20),
    )

    if percentage:
        extra_resources = (
            (ammo_a, 10),
            (ammo_b, 20),
            (echoes_resource_database.item_percentage, 1),
        )
    else:
        extra_resources = (
            (ammo_a, 10),
            (ammo_b, 20),
        )

    # Run
    result = pickup_creator.create_major_item(major_item, state, percentage,
                                              echoes_resource_database,
                                              None, False)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model=PickupModel(echoes_resource_database.game_enum, "SuperModel"),
        progression=(
            (item_a, 1),
            (item_b, 1),
            (item_c, 1),
        ),
        extra_resources=extra_resources,
        item_category=less_generic_item_category,
        broad_category=generic_item_category,
        probability_offset=5,
        respects_lock=False,
    )


@pytest.mark.parametrize(["ammo_quantity"], [
    (0,),
    (10,),
    (15,),
])
def test_create_missile_launcher(ammo_quantity: int, echoes_item_database, echoes_resource_database):
    # Setup
    missile = echoes_resource_database.get_item("Missile")
    missile_launcher = echoes_resource_database.get_item("MissileLauncher")
    temporary = echoes_resource_database.get_item("Temporary1")

    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = pickup_creator.create_major_item(
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
        progression=(
            (missile_launcher, 1),
        ),
        extra_resources=(
            (missile, ammo_quantity),
            (echoes_resource_database.item_percentage, 1),
        ),
        model=PickupModel(echoes_resource_database.game_enum, "MissileLauncher"),
        item_category=echoes_item_database.item_categories["missile"],
        broad_category=echoes_item_database.item_categories["missile_related"],
        resource_lock=ResourceLock(
            locked_by=missile_launcher,
            temporary_item=temporary,
            item_to_lock=missile,
        ),
        unlocks_resource=True,
    )


@pytest.mark.parametrize("ammo_quantity", [0, 10, 15])
@pytest.mark.parametrize("ammo_requires_major_item", [False, True])
def test_create_seeker_launcher(ammo_quantity: int,
                                ammo_requires_major_item: bool,
                                echoes_item_database,
                                echoes_resource_database,
                                ):
    # Setup
    missile = echoes_resource_database.get_item("Missile")
    missile_launcher = echoes_resource_database.get_item("MissileLauncher")
    seeker_launcher = echoes_resource_database.get_item("Seekers")
    temporary = echoes_resource_database.get_item("Temporary1")

    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = pickup_creator.create_major_item(
        echoes_item_database.major_items["Seeker Launcher"],
        state,
        True,
        echoes_resource_database,
        echoes_item_database.ammo["Missile Expansion"],
        ammo_requires_major_item
    )

    # Assert

    assert result == PickupEntry(
        name="Seeker Launcher",
        progression=(
            (seeker_launcher, 1),
        ),
        extra_resources=(
            (missile, ammo_quantity),
            (echoes_resource_database.item_percentage, 1),
        ),
        model=PickupModel(echoes_resource_database.game_enum, "SeekerLauncher"),
        item_category=echoes_item_database.item_categories["missile"],
        broad_category=echoes_item_database.item_categories["missile_related"],
        respects_lock=ammo_requires_major_item,
        resource_lock=ResourceLock(
            locked_by=missile_launcher,
            temporary_item=temporary,
            item_to_lock=missile,
        ),
    )


@pytest.mark.parametrize("requires_major_item", [False, True])
def test_create_ammo_expansion(requires_major_item: bool, echoes_item_database, echoes_resource_database):
    # Setup
    primary_a = echoes_resource_database.get_item("MissileLauncher")
    ammo_a = echoes_resource_database.get_item("Missile")
    temporary_a = echoes_resource_database.get_item("Temporary1")

    ammo = Ammo(
        game=echoes_resource_database.game_enum,
        name="The Item",
        items=("Missile",),
        broad_category=USELESS_ITEM_CATEGORY,
        unlocked_by="MissileLauncher",
        temporary="Temporary1",
        model_name="AmmoModel",
    )
    ammo_count = (11, 150)

    # Run
    result = pickup_creator.create_ammo_expansion(
        ammo, ammo_count, requires_major_item, echoes_resource_database)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model=PickupModel(echoes_resource_database.game_enum, "AmmoModel"),
        progression=tuple(),
        extra_resources=(
            (ammo_a, ammo_count[0]),
            (echoes_resource_database.item_percentage, 1),
        ),
        item_category=AMMO_ITEM_CATEGORY,
        broad_category=USELESS_ITEM_CATEGORY,
        probability_offset=0,
        respects_lock=requires_major_item,
        resource_lock=ResourceLock(
            locked_by=primary_a,
            temporary_item=temporary_a,
            item_to_lock=ammo_a,
        ),
        probability_multiplier=2,
    )


@pytest.mark.parametrize("include_before", [False, True])
def test_missile_expansion_before_launcher(include_before, echoes_item_database, echoes_resource_database):
    # Setup
    ammo = echoes_item_database.ammo["Missile Expansion"]
    major_item = echoes_item_database.major_items["Missile Launcher"]

    missile = echoes_resource_database.get_item(ammo.items[0])
    missile_launcher = echoes_resource_database.get_item(major_item.progression[0])
    temporary = echoes_resource_database.get_item(ammo.temporary)
    percent = echoes_resource_database.item_percentage

    # Run
    expansion = pickup_creator.create_ammo_expansion(ammo, [5], True, echoes_resource_database)
    launcher = pickup_creator.create_major_item(
        major_item, MajorItemState(included_ammo=(5,)),
        True, echoes_resource_database, ammo, True
    )

    def to_dict(col: ResourceCollection):
        return dict(col.as_resource_gain())

    collection = ResourceCollection.with_database(echoes_resource_database)

    if include_before:
        # Ammo Expansion
        collection.add_resource_gain(expansion.resource_gain(collection, force_lock=True))
        assert to_dict(collection) == {percent: 1, temporary: 5}

    # Add Launcher
    collection.add_resource_gain(launcher.resource_gain(collection, force_lock=True))
    if include_before:
        assert to_dict(collection) == {percent: 2, temporary: 0, missile_launcher: 1, missile: 10}
    else:
        assert to_dict(collection) == {percent: 1, temporary: 0, missile_launcher: 1, missile: 5}

    # Ammo Expansion
    collection.add_resource_gain(expansion.resource_gain(collection, force_lock=True))
    if include_before:
        assert to_dict(collection) == {percent: 3, temporary: 0, missile_launcher: 1, missile: 15}
    else:
        assert to_dict(collection) == {percent: 2, temporary: 0, missile_launcher: 1, missile: 10}
