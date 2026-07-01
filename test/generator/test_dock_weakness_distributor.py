from __future__ import annotations

import dataclasses
from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.game_description.game_description import GameDescription
from randovania.generator import dock_weakness_distributor
from randovania.generator.generator import generate_and_validate_description
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.dock_weakness_distributor_configuration import (
    DockWeaknessDistributorConfiguration,
    DockWeaknessDistributorMode,
)
from randovania.layout.generator_parameters import GeneratorParameters


@pytest.fixture
def _force_blank_two_way(blank_game_description):
    dock_type = blank_game_description.dock_type_database.find_type("door")
    rando_settings = dock_type.get_weakness_distributor()
    dock_type
    object.__setattr__(
        rando_settings,
        "force_change_two_way",
        True,
    )
    yield
    object.__setattr__(
        rando_settings,
        "force_change_two_way",
        False,
    )


def _replace_mode(
    game: GameDescription,
    configuration: DockWeaknessDistributorConfiguration,
    mode: DockWeaknessDistributorMode,
) -> DockWeaknessDistributorConfiguration:
    dock_type = game.dock_type_database.find_type("door")
    return configuration.replace_state(
        dock_type,
        dataclasses.replace(
            configuration.types_state[dock_type],
            mode=mode,
        ),
    )


def test_distribute_pre_fill_weaknesses_swap(blank_game_description, empty_patches):
    rng = Random(5000)

    distributor_config = _replace_mode(
        blank_game_description,
        empty_patches.configuration.dock_weakness_distributor,
        DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS,
    )

    patches = dataclasses.replace(
        empty_patches,
        configuration=dataclasses.replace(
            empty_patches.configuration,
            dock_weakness_distributor=distributor_config,
        ),
    )

    result = dock_weakness_distributor.distribute_pre_fill_weaknesses(
        blank_game_description,
        distributor_config,
        patches,
        rng,
    )
    docks = {(n.identifier.area, n.name): w.name for n, w in result.all_dock_weaknesses(blank_game_description)}

    assert docks == {
        ("Back-Only Lock Room", "Door to Starting Area"): "Explosive Door",
        ("Blue Key Room", "Door to Starting Area (Entrance)"): "Normal Door",
        ("Blue Key Room", "Door to Starting Area (Exit)"): "Back-Only Door",
        ("Boss Arena", "Door to Starting Area"): "Normal Door",
        ("Explosive Depot", "Door to Hint Room"): "Normal Door",
        ("Explosive Depot", "Door to Starting Area"): "Normal Door",
        ("Heated Room", "Door to Starting Area"): "Normal Door",
        ("Ledge Room", "Door to Starting Area"): "Normal Door",
        ("Hint Room", "Door to Explosive Depot"): "Normal Door",
        ("Starting Area", "Door to Back-Only Lock Room"): "Normal Door",
        ("Starting Area", "Door to Blue Key Room (Entrance)"): "Normal Door",
        ("Starting Area", "Door to Blue Key Room (Exit)"): "Normal Door",
        ("Starting Area", "Door to Boss Arena"): "Locked Door",
        ("Starting Area", "Door to Explosive Depot"): "Normal Door",
        ("Starting Area", "Door to Heated Room"): "Normal Door",
        ("Starting Area", "Door to Ledge Room"): "Normal Door",
    }
    assert list(result.all_weaknesses_to_shuffle(blank_game_description)) == []


@pytest.mark.usefixtures("_force_blank_two_way")
def test_distribute_pre_fill_weaknesses_swap_force_two_way(blank_game_description, empty_patches):
    rng = Random(10000)

    distributor_config = _replace_mode(
        blank_game_description,
        empty_patches.configuration.dock_weakness_distributor,
        DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS,
    )
    patches = dataclasses.replace(
        empty_patches,
        configuration=dataclasses.replace(
            empty_patches.configuration,
            dock_weakness_distributor=distributor_config,
        ),
    )

    result = dock_weakness_distributor.distribute_pre_fill_weaknesses(
        blank_game_description,
        distributor_config,
        patches,
        rng,
    )
    docks = {(n.identifier.area, n.name): w.name for n, w in result.all_dock_weaknesses(blank_game_description)}

    assert docks == {
        ("Back-Only Lock Room", "Door to Starting Area"): "Back-Only Door",
        ("Blue Key Room", "Door to Starting Area (Entrance)"): "Back-Only Door",
        ("Blue Key Room", "Door to Starting Area (Exit)"): "Back-Only Door",
        ("Boss Arena", "Door to Starting Area"): "Back-Only Door",
        ("Explosive Depot", "Door to Hint Room"): "Back-Only Door",
        ("Explosive Depot", "Door to Starting Area"): "Back-Only Door",
        ("Heated Room", "Door to Starting Area"): "Back-Only Door",
        ("Ledge Room", "Door to Starting Area"): "Back-Only Door",
        ("Hint Room", "Door to Explosive Depot"): "Back-Only Door",
        ("Starting Area", "Door to Back-Only Lock Room"): "Back-Only Door",
        ("Starting Area", "Door to Blue Key Room (Entrance)"): "Back-Only Door",
        ("Starting Area", "Door to Blue Key Room (Exit)"): "Back-Only Door",
        ("Starting Area", "Door to Boss Arena"): "Back-Only Door",
        ("Starting Area", "Door to Explosive Depot"): "Back-Only Door",
        ("Starting Area", "Door to Heated Room"): "Back-Only Door",
        ("Starting Area", "Door to Ledge Room"): "Back-Only Door",
    }
    assert list(result.all_weaknesses_to_shuffle(blank_game_description)) == []


def test_distribute_pre_fill_docks(blank_game_description, empty_patches, monkeypatch):
    rng = Random(5000)

    distributor_config = _replace_mode(
        blank_game_description,
        empty_patches.configuration.dock_weakness_distributor,
        DockWeaknessDistributorMode.INDIVIDUAL_DOCK,
    )
    patches = dataclasses.replace(
        empty_patches,
        configuration=dataclasses.replace(
            empty_patches.configuration,
            dock_weakness_distributor=distributor_config,
        ),
    )

    result = dock_weakness_distributor.distribute_pre_fill_weaknesses(
        blank_game_description,
        distributor_config,
        patches,
        rng,
    )
    docks = {(n.identifier.area, n.name): w.name for n, w in result.all_dock_weaknesses(blank_game_description)}
    to_shuffle = [(n.identifier.area, n.name) for n in result.all_weaknesses_to_shuffle(blank_game_description)]

    assert docks == {
        ("Back-Only Lock Room", "Door to Starting Area"): "Normal Door",
        ("Blue Key Room", "Door to Starting Area (Entrance)"): "Normal Door",
        ("Blue Key Room", "Door to Starting Area (Exit)"): "Normal Door",
        ("Boss Arena", "Door to Starting Area"): "Normal Door",
        ("Explosive Depot", "Door to Hint Room"): "Normal Door",
        ("Explosive Depot", "Door to Starting Area"): "Normal Door",
        ("Heated Room", "Door to Starting Area"): "Normal Door",
        ("Ledge Room", "Door to Starting Area"): "Normal Door",
        ("Hint Room", "Door to Explosive Depot"): "Normal Door",
        ("Starting Area", "Door to Back-Only Lock Room"): "Normal Door",
        ("Starting Area", "Door to Blue Key Room (Entrance)"): "Normal Door",
        ("Starting Area", "Door to Blue Key Room (Exit)"): "Normal Door",
        ("Starting Area", "Door to Boss Arena"): "Normal Door",
        ("Starting Area", "Door to Explosive Depot"): "Normal Door",
        ("Starting Area", "Door to Heated Room"): "Normal Door",
        ("Starting Area", "Door to Ledge Room"): "Normal Door",
    }
    assert to_shuffle == [
        ("Starting Area", "Door to Boss Arena"),
        ("Starting Area", "Door to Explosive Depot"),
        ("Starting Area", "Door to Back-Only Lock Room"),
        ("Starting Area", "Door to Blue Key Room (Exit)"),
        ("Starting Area", "Door to Blue Key Room (Entrance)"),
        ("Starting Area", "Door to Heated Room"),
        ("Starting Area", "Door to Ledge Room"),
        ("Boss Arena", "Door to Starting Area"),
        ("Explosive Depot", "Door to Starting Area"),
        ("Explosive Depot", "Door to Hint Room"),
        ("Back-Only Lock Room", "Door to Starting Area"),
        ("Blue Key Room", "Door to Starting Area (Exit)"),
        ("Blue Key Room", "Door to Starting Area (Entrance)"),
        ("Hint Room", "Door to Explosive Depot"),
        ("Heated Room", "Door to Starting Area"),
        ("Ledge Room", "Door to Starting Area"),
    ]


async def test_dock_weakness_distribute(default_blank_preset, blank_game_description):
    options = MagicMock()
    _editor = PresetEditor(default_blank_preset.fork(), options)
    with _editor as editor:
        editor.dock_weakness_distributor = _replace_mode(
            blank_game_description,
            editor.dock_weakness_distributor,
            DockWeaknessDistributorMode.INDIVIDUAL_DOCK,
        )
        preset = editor.create_custom_preset_with()

    gen_params = GeneratorParameters(6000, False, [preset])
    description = await generate_and_validate_description(gen_params, None, False)

    assert list(description.all_patches[0].all_dock_weaknesses(blank_game_description))
