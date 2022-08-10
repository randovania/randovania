import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout import preset_describer
from randovania.games.prime2.layout.beam_configuration import BeamConfiguration, BeamAmmoConfiguration
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode


def test_create_beam_configuration_description_vanilla():
    default_config = BeamConfiguration(
        power=BeamAmmoConfiguration(0, -1, -1, 0, 0, 5, 0),
        dark=BeamAmmoConfiguration(1, 45, -1, 1, 5, 5, 30),
        light=BeamAmmoConfiguration(2, 46, -1, 1, 5, 5, 30),
        annihilator=BeamAmmoConfiguration(3, 46, 45, 1, 5, 5, 30),
    )

    # Run
    result = preset_describer.create_beam_configuration_description(default_config)

    # Assert
    assert result == []


def test_create_beam_configuration_description_custom():
    default_config = BeamConfiguration(
        power=BeamAmmoConfiguration(0, -1, -1, 0, 0, 6, 0),
        dark=BeamAmmoConfiguration(1, 44, -1, 1, 5, 5, 30),
        light=BeamAmmoConfiguration(2, 46, -1, 1, 5, 6, 10),
        annihilator=BeamAmmoConfiguration(3, 46, 45, 1, 5, 5, 10),
    )

    # Run
    result = preset_describer.create_beam_configuration_description(default_config)

    # Assert
    assert result == [
        {'Power Beam uses 6 missiles for combo': True},
        {'Dark Beam uses Missile': True},
        {'Light Beam uses 10 (Combo) Light Ammo, 6 missiles for combo': True},
        {'Annihilator Beam uses 10 (Combo) Light and Dark Ammo': True},
    ]


def test_echoes_format_params(default_echoes_configuration):
    # Setup
    layout_configuration = dataclasses.replace(
        default_echoes_configuration,
        sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
    )

    # Run
    result = RandovaniaGame.METROID_PRIME_ECHOES.data.layout.preset_describer.format_params(layout_configuration)

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
        'Logic Settings': [
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
