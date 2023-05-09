import dataclasses
from random import Random
from unittest.mock import MagicMock

from randovania.generator import dock_weakness_distributor
from randovania.generator.generator import generate_and_validate_description
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.layout.generator_parameters import GeneratorParameters


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
