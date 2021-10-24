import dataclasses

from randovania.gui.lib import preset_describer
from randovania.layout.prime2.echoes_configuration import LayoutSkyTempleKeyMode


def test_echoes_format_params(default_layout_configuration):
    # Setup
    layout_configuration = dataclasses.replace(
        default_layout_configuration,
        sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
    )

    # Run
    result = preset_describer._echoes_format_params(layout_configuration)

    # Assert
    assert result == {
        'Difficulty': [
            'Damage Strictness: Medium',
        ],
        'Game Changes': [
            'Missiles needs Launcher, Power Bomb needs Main',
            'Warp to start, Menu Mod',
        ],
        'Gameplay': [
            'Starting Location: Temple Grounds - Landing Site',
            'Translator Gates: Vanilla (Colors)',
        ],
        'Item Placement': [
            'All tricks disabled',
            'Dangerous Actions: Randomly',
        ],
        'Item Pool': [
            'Size: 118 of 119',
            'Progressive Suit, Split beam ammo',
            'Sky Temple Keys at all bosses',
        ],
        'Starting Items': [
            'Vanilla',
        ]
    }
