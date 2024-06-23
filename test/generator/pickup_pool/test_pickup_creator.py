from __future__ import annotations

import dataclasses

import pytest
from frozendict import frozendict

from randovania.game_description.pickup.ammo_pickup import AMMO_PICKUP_CATEGORY, AmmoPickupDefinition
from randovania.game_description.pickup.pickup_category import USELESS_PICKUP_CATEGORY, PickupCategory
from randovania.game_description.pickup.pickup_entry import (
    PickupEntry,
    PickupGeneratorParams,
    PickupModel,
    ResourceLock,
)
from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.games.prime2.patcher import echoes_items
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout.base.standard_pickup_state import StandardPickupState


def test_create_pickup_for(echoes_resource_database, generic_pickup_category):
    # Setup
    item_a = echoes_resource_database.get_item("DarkVisor")
    item_b = echoes_resource_database.get_item("MorphBall")
    item_c = echoes_resource_database.get_item("Bombs")
    ammo_a = echoes_resource_database.get_item("EnergyTank")
    ammo_b = echoes_resource_database.get_item("DarkAmmo")

    less_generic_pickup_category = PickupCategory(
        name="the_category", long_name="The Category", hint_details=("a ", " wonderful item"), hinted_as_major=True
    )

    standard_pickup = StandardPickupDefinition(
        game=echoes_resource_database.game_enum,
        name="The Item",
        pickup_category=less_generic_pickup_category,
        broad_category=generic_pickup_category,
        model_name="SuperModel",
        offworld_models=frozendict({}),
        progression=("DarkVisor", "MorphBall", "Bombs"),
        ammo=("EnergyTank", "DarkAmmo"),
        must_be_starting=False,
        original_locations=(),
        probability_offset=5.0,
        preferred_location_category=LocationCategory.MAJOR,
    )
    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_pickups=0,
        included_ammo=(10, 20),
    )

    extra_resources = (
        (ammo_a, 10),
        (ammo_b, 20),
    )

    # Run
    result = pickup_creator.create_standard_pickup(standard_pickup, state, echoes_resource_database, None, False)

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
        pickup_category=less_generic_pickup_category,
        broad_category=generic_pickup_category,
        respects_lock=False,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=5.0,
        ),
    )


@pytest.mark.parametrize(
    "ammo_quantity",
    [
        0,
        10,
        15,
    ],
)
def test_create_missile_launcher(
    ammo_quantity: int, echoes_pickup_database, echoes_resource_database, default_generator_params
):
    # Setup
    missile = echoes_resource_database.get_item("Missile")
    missile_launcher = echoes_resource_database.get_item("MissileLauncher")
    temporary = echoes_resource_database.get_item("Temporary1")

    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_pickups=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = pickup_creator.create_standard_pickup(
        echoes_pickup_database.standard_pickups["Missile Launcher"],
        state,
        echoes_resource_database,
        echoes_pickup_database.ammo_pickups["Missile Expansion"],
        ammo_requires_main_item=True,
    )
    result = dataclasses.replace(result, offworld_models=frozendict({}))

    # Assert
    assert result == PickupEntry(
        name="Missile Launcher",
        progression=((missile_launcher, 1),),
        extra_resources=(
            (missile, ammo_quantity),
            (echoes_resource_database.get_item(echoes_items.PERCENTAGE), 1),
        ),
        model=PickupModel(echoes_resource_database.game_enum, "MissileLauncher"),
        pickup_category=echoes_pickup_database.pickup_categories["missile"],
        broad_category=echoes_pickup_database.pickup_categories["missile_related"],
        generator_params=default_generator_params,
        resource_lock=ResourceLock(
            locked_by=missile_launcher,
            temporary_item=temporary,
            item_to_lock=missile,
        ),
        unlocks_resource=True,
    )


@pytest.mark.parametrize("ammo_quantity", [0, 10, 15])
@pytest.mark.parametrize("ammo_requires_main_item", [False, True])
def test_create_seeker_launcher(
    ammo_quantity: int,
    ammo_requires_main_item: bool,
    echoes_pickup_database,
    echoes_resource_database,
    default_generator_params,
):
    # Setup
    missile = echoes_resource_database.get_item("Missile")
    missile_launcher = echoes_resource_database.get_item("MissileLauncher")
    seeker_launcher = echoes_resource_database.get_item("Seekers")
    temporary = echoes_resource_database.get_item("Temporary1")

    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_pickups=0,
        included_ammo=(ammo_quantity,),
    )

    # Run
    result = pickup_creator.create_standard_pickup(
        echoes_pickup_database.standard_pickups["Seeker Launcher"],
        state,
        echoes_resource_database,
        echoes_pickup_database.ammo_pickups["Missile Expansion"],
        ammo_requires_main_item,
    )
    result = dataclasses.replace(result, offworld_models=frozendict({}))

    # Assert

    assert result == PickupEntry(
        name="Seeker Launcher",
        progression=((seeker_launcher, 1),),
        extra_resources=(
            (missile, ammo_quantity),
            (echoes_resource_database.get_item(echoes_items.PERCENTAGE), 1),
        ),
        model=PickupModel(echoes_resource_database.game_enum, "SeekerLauncher"),
        pickup_category=echoes_pickup_database.pickup_categories["missile"],
        broad_category=echoes_pickup_database.pickup_categories["missile_related"],
        respects_lock=ammo_requires_main_item,
        resource_lock=ResourceLock(
            locked_by=missile_launcher,
            temporary_item=temporary,
            item_to_lock=missile,
        ),
        generator_params=default_generator_params,
    )


@pytest.mark.parametrize("requires_main_item", [False, True])
def test_create_ammo_expansion(requires_main_item: bool, echoes_pickup_database, echoes_resource_database):
    # Setup
    primary_a = echoes_resource_database.get_item("MissileLauncher")
    ammo_a = echoes_resource_database.get_item("Missile")
    temporary_a = echoes_resource_database.get_item("Temporary1")

    ammo = AmmoPickupDefinition(
        game=echoes_resource_database.game_enum,
        name="The Item",
        items=("Missile",),
        broad_category=USELESS_PICKUP_CATEGORY,
        unlocked_by="MissileLauncher",
        temporary="Temporary1",
        model_name="AmmoModel",
        offworld_models=frozendict({}),
        preferred_location_category=LocationCategory.MINOR,
    )
    ammo_count = (11, 150)

    # Run
    result = pickup_creator.create_ammo_pickup(ammo, ammo_count, requires_main_item, echoes_resource_database)

    # Assert
    assert result == PickupEntry(
        name="The Item",
        model=PickupModel(echoes_resource_database.game_enum, "AmmoModel"),
        progression=(),
        extra_resources=((ammo_a, ammo_count[0]),),
        pickup_category=AMMO_PICKUP_CATEGORY,
        broad_category=USELESS_PICKUP_CATEGORY,
        respects_lock=requires_main_item,
        resource_lock=ResourceLock(
            locked_by=primary_a,
            temporary_item=temporary_a,
            item_to_lock=ammo_a,
        ),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MINOR,
            probability_offset=0.0,
            probability_multiplier=2.0,
        ),
    )


@pytest.mark.parametrize("include_before", [False, True])
def test_missile_expansion_before_launcher(include_before, echoes_pickup_database, echoes_resource_database):
    # Setup
    ammo = echoes_pickup_database.ammo_pickups["Missile Expansion"]
    standard_pickup = echoes_pickup_database.standard_pickups["Missile Launcher"]

    missile = echoes_resource_database.get_item(ammo.items[0])
    missile_launcher = echoes_resource_database.get_item(standard_pickup.progression[0])
    temporary = echoes_resource_database.get_item(ammo.temporary)
    percent = echoes_resource_database.get_item(echoes_items.PERCENTAGE)

    # Run
    expansion = pickup_creator.create_ammo_pickup(ammo, [5], True, echoes_resource_database)
    launcher = pickup_creator.create_standard_pickup(
        standard_pickup, StandardPickupState(included_ammo=(5,)), echoes_resource_database, ammo, True
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
