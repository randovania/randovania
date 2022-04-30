from randovania.games.prime2.layout import preset_describer
from randovania.games.prime2.layout.beam_configuration import BeamConfiguration, BeamAmmoConfiguration


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
