import dataclasses
from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.game_description import default_database
from randovania.generator import dock_weakness_distributor
from randovania.generator.generator import generate_and_validate_description
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.layout.generator_parameters import GeneratorParameters


@pytest.fixture()
def force_blank_two_way(blank_game_description):
    object.__setattr__(
        blank_game_description.dock_weakness_database.dock_rando_config,
        "force_change_two_way",
        True,
    )
    yield
    object.__setattr__(
        blank_game_description.dock_weakness_database.dock_rando_config,
        "force_change_two_way",
        False,
    )


def test_distribute_pre_fill_weaknesses_swap(empty_patches):
    rng = Random(5000)
    patches = dataclasses.replace(
        empty_patches,
        configuration=dataclasses.replace(
            empty_patches.configuration,
            dock_rando=dataclasses.replace(
                empty_patches.configuration.dock_rando,
                mode=DockRandoMode.WEAKNESSES,
            )
        )
    )

    result = dock_weakness_distributor.distribute_pre_fill_weaknesses(
        patches, rng,
    )
    docks = dict(((n.identifier.area_name, n.name), w.name)
                 for n, w in result.all_dock_weaknesses())

    assert docks == {
        ('Back-Only Lock Room', 'Door to Starting Area'): 'Explosive Door',
        ('Blue Key Room', 'Door to Starting Area (Entrance)'): 'Normal Door',
        ('Blue Key Room', 'Door to Starting Area (Exit)'): 'Back-Only Door',
        ('Boss Arena', 'Door to Starting Area'): 'Normal Door',
        ('Explosive Depot', 'Door to Hint Room'): 'Normal Door',
        ('Explosive Depot', 'Door to Starting Area'): 'Normal Door',
        ('Hint Room', 'Door to Explosive Depot'): 'Normal Door',
        ('Starting Area', 'Door to Back-Only Lock Room'): 'Normal Door',
        ('Starting Area', 'Door to Blue Key Room (Entrance)'): 'Normal Door',
        ('Starting Area', 'Door to Blue Key Room (Exit)'): 'Normal Door',
        ('Starting Area', 'Door to Boss Arena'): 'Locked Door',
        ('Starting Area', 'Door to Explosive Depot'): 'Normal Door',
    }
    assert list(result.all_weaknesses_to_shuffle()) == []


def test_distribute_pre_fill_weaknesses_swap_force_two_way(empty_patches, force_blank_two_way,
                                                           monkeypatch):
    rng = Random(10000)
    patches = dataclasses.replace(
        empty_patches,
        configuration=dataclasses.replace(
            empty_patches.configuration,
            dock_rando=dataclasses.replace(
                empty_patches.configuration.dock_rando,
                mode=DockRandoMode.WEAKNESSES,
            )
        )
    )

    result = dock_weakness_distributor.distribute_pre_fill_weaknesses(
        patches, rng,
    )
    docks = dict(((n.identifier.area_name, n.name), w.name)
                 for n, w in result.all_dock_weaknesses())

    assert docks == {
        ('Back-Only Lock Room', 'Door to Starting Area'): 'Back-Only Door',
        ('Blue Key Room', 'Door to Starting Area (Entrance)'): 'Back-Only Door',
        ('Blue Key Room', 'Door to Starting Area (Exit)'): 'Back-Only Door',
        ('Boss Arena', 'Door to Starting Area'): 'Back-Only Door',
        ('Explosive Depot', 'Door to Hint Room'): 'Back-Only Door',
        ('Explosive Depot', 'Door to Starting Area'): 'Back-Only Door',
        ('Hint Room', 'Door to Explosive Depot'): 'Back-Only Door',
        ('Starting Area', 'Door to Back-Only Lock Room'): 'Back-Only Door',
        ('Starting Area', 'Door to Blue Key Room (Entrance)'): 'Back-Only Door',
        ('Starting Area', 'Door to Blue Key Room (Exit)'): 'Back-Only Door',
        ('Starting Area', 'Door to Boss Arena'): 'Back-Only Door',
        ('Starting Area', 'Door to Explosive Depot'): 'Back-Only Door',
    }
    assert list(result.all_weaknesses_to_shuffle()) == []


def test_distribute_pre_fill_docks(empty_patches, monkeypatch):
    rng = Random(5000)
    patches = dataclasses.replace(
        empty_patches,
        configuration=dataclasses.replace(
            empty_patches.configuration,
            dock_rando=dataclasses.replace(
                empty_patches.configuration.dock_rando,
                mode=DockRandoMode.DOCKS,
            )
        )
    )

    result = dock_weakness_distributor.distribute_pre_fill_weaknesses(
        patches, rng,
    )
    docks = dict(((n.identifier.area_name, n.name), w.name)
                 for n, w in result.all_dock_weaknesses())
    to_shuffle = [
        (n.identifier.area_name, n.name)
        for n in result.all_weaknesses_to_shuffle()
    ]

    assert docks == {
        ('Back-Only Lock Room', 'Door to Starting Area'): 'Normal Door',
        ('Blue Key Room', 'Door to Starting Area (Entrance)'): 'Normal Door',
        ('Blue Key Room', 'Door to Starting Area (Exit)'): 'Normal Door',
        ('Boss Arena', 'Door to Starting Area'): 'Normal Door',
        ('Explosive Depot', 'Door to Hint Room'): 'Normal Door',
        ('Explosive Depot', 'Door to Starting Area'): 'Normal Door',
        ('Hint Room', 'Door to Explosive Depot'): 'Normal Door',
        ('Starting Area', 'Door to Back-Only Lock Room'): 'Normal Door',
        ('Starting Area', 'Door to Blue Key Room (Entrance)'): 'Normal Door',
        ('Starting Area', 'Door to Blue Key Room (Exit)'): 'Normal Door',
        ('Starting Area', 'Door to Boss Arena'): 'Normal Door',
        ('Starting Area', 'Door to Explosive Depot'): 'Normal Door',
    }
    assert to_shuffle == [
        ('Starting Area', 'Door to Boss Arena'),
        ('Starting Area', 'Door to Explosive Depot'),
        ('Starting Area', 'Door to Back-Only Lock Room'),
        ('Starting Area', 'Door to Blue Key Room (Exit)'),
        ('Starting Area', 'Door to Blue Key Room (Entrance)'),
        ('Boss Arena', 'Door to Starting Area'),
        ('Explosive Depot', 'Door to Starting Area'),
        ('Explosive Depot', 'Door to Hint Room'),
        ('Back-Only Lock Room', 'Door to Starting Area'),
        ('Blue Key Room', 'Door to Starting Area (Exit)'),
        ('Blue Key Room', 'Door to Starting Area (Entrance)'),
        ('Hint Room', 'Door to Explosive Depot'),
    ]


async def test_dock_weakness_distribute(default_blank_preset):
    options = MagicMock()
    _editor = PresetEditor(default_blank_preset.fork(), options)
    with _editor as editor:
        editor.dock_rando_configuration = dataclasses.replace(
            editor.dock_rando_configuration,
            mode=DockRandoMode.DOCKS
        )
        preset = editor.create_custom_preset_with()

    gen_params = GeneratorParameters(5000, False, [preset])
    description = await generate_and_validate_description(gen_params, None, False)

    assert list(description.all_patches[0].all_dock_weaknesses())
