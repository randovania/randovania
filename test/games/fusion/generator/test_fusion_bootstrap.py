from __future__ import annotations

import dataclasses
from random import Random

import pytest

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.fusion.generator import FusionBootstrap
from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig
from randovania.generator.pickup_pool import pool_creator
from randovania.layout.base.dock_weakness_distributor_configuration import DockWeaknessDistributorMode


@pytest.mark.parametrize(
    ("artifacts", "expected"),
    [
        (FusionArtifactConfig(5, 5), [24, 66, 100, 107, 110]),
        (FusionArtifactConfig(11, 11), [24, 66, 90, 96, 100, 104, 106, 107, 109, 110, 124]),
        (FusionArtifactConfig(0, 0), []),
    ],
)
def test_assign_pool_results_predetermined(fusion_game_description, fusion_configuration, artifacts, expected):
    fusion_configuration = dataclasses.replace(fusion_configuration, artifacts=artifacts)
    patches = GamePatches.create_from_game(fusion_game_description, 0, fusion_configuration)
    pool_results = pool_creator.calculate_pool_results(fusion_configuration, patches.game)

    # Run
    result = FusionBootstrap().assign_pool_results(
        Random(8000),
        fusion_configuration,
        patches,
        pool_results,
    )

    # Assert
    shuffled_metroids = [pickup for pickup in pool_results.to_place if pickup.gui_category.name == "InfantMetroid"]

    assert result.starting_equipment == pool_results.starting
    assert {index for index, entry in result.pickup_assignment.items() if "Infant Metroid" in entry.pickup.name} == {
        PickupIndex(i) for i in expected
    }
    assert shuffled_metroids == []


@pytest.mark.parametrize(
    ("dmg_type", "dmg_configured", "dmg_multiplier", "config_value"),
    [
        ("LavaDamage", 40, [2.0, 2.0 / 0.9, 0.0], "lava_damage"),
        ("LavaDamage", 10, [0.5, 0.5 / 0.9, 0.0], "lava_damage"),
        ("HeatDamage", 60, [10.0, 0.0], "heat_damage"),
        ("AcidDamage", 6, [0.1], "acid_damage"),
        ("ColdDamage", 45, [3.0, 0.0], "cold_damage"),
    ],
)
def test_patch_resource_database(
    fusion_game_description, fusion_configuration, dmg_type, dmg_configured, dmg_multiplier, config_value
):
    # replace the environmental damage with the dmg value for the test and run bootstrap
    fusion_configuration = dataclasses.replace(fusion_configuration, **{config_value: dmg_configured})
    result = FusionBootstrap().patch_resource_database(fusion_game_description.resource_database, fusion_configuration)
    # loop through all reductions and assert that the new multiplier is what we expect
    for i, reduction in enumerate(result.damage_reductions[result.get_damage(dmg_type)]):
        assert reduction.damage_multiplier == dmg_multiplier[i]


@pytest.mark.parametrize("door_state", ["vanilla", "individual-all", "type-all", "individual-no-open", "type-no-open"])
@pytest.mark.parametrize("geron_state", [False, True])
def test_enabled_misc_resources(fusion_game_description, fusion_configuration, door_state, geron_state) -> None:
    expected_resources = {"BomblessPBs", "GeneratorHack"}

    door_db = fusion_game_description.dock_type_database
    door_type = door_db.find_type("Door")
    open_hatch_door = door_db.get_by_weakness("Door", "Open Hatch")

    weakness_mode = DockWeaknessDistributorMode.ORIGINAL
    if door_state in ["individual-all", "individual-no-open"]:
        weakness_mode = DockWeaknessDistributorMode.INDIVIDUAL_DOCK
    elif door_state in ["type-all", "type-no-open"]:
        weakness_mode = DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS

    all_door_weaknesses = set(door_db.weaknesses[door_type].values())
    if door_state in ["individual-no-open", "type-no-open"]:
        all_door_weaknesses.remove(open_hatch_door)

    if door_state != "vanilla":
        types_state = fusion_configuration.dock_weakness_distributor.types_state
        types_state[door_type] = dataclasses.replace(types_state[door_type], mode=weakness_mode)
        types_state[door_type] = dataclasses.replace(types_state[door_type], can_change_from=all_door_weaknesses)
        types_state[door_type] = dataclasses.replace(types_state[door_type], can_change_to=all_door_weaknesses)
        fusion_configuration = dataclasses.replace(
            fusion_configuration,
            dock_weakness_distributor=dataclasses.replace(
                fusion_configuration.dock_weakness_distributor, types_state=types_state
            ),
        )
        if door_state in ["individual-all", "type-all"]:
            expected_resources.add("DoorLockRando")
            expected_resources.add("OpenHatchLockRando")
        elif door_state in ["individual-no-open", "type-no-open"]:
            expected_resources.add("DoorLockRando")
    elif door_state == "vanilla":
        # keep as is
        pass
    else:
        raise Exception("unhandled state for door_state")

    if geron_state:
        fusion_configuration = dataclasses.replace(fusion_configuration, adjusted_geron_weaknesses=True)
        expected_resources.add("NerfGerons")
    else:
        fusion_configuration = dataclasses.replace(fusion_configuration, adjusted_geron_weaknesses=False)

    enabled_resources = FusionBootstrap()._get_enabled_misc_resources(
        fusion_configuration, fusion_game_description.get_resource_database_view()
    )

    assert enabled_resources == expected_resources
