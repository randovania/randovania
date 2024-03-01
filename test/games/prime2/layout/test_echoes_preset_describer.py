from __future__ import annotations

import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout import preset_describer
from randovania.games.prime2.layout.beam_configuration import BeamAmmoConfiguration, BeamConfiguration
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.standard_pickup_state import StandardPickupState


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
        {"Power Beam uses 6 missiles for combo": True},
        {"Dark Beam uses Missile": True},
        {"Light Beam uses 10 (Combo) Light Ammo, 6 missiles for combo": True},
        {"Annihilator Beam uses 10 (Combo) Light and Dark Ammo": True},
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
        "Difficulty": [],
        "Game Changes": [
            "Missiles needs Launcher, Power Bomb needs Main",
            "Warp to start, Menu Mod",
        ],
        "Gameplay": [
            "Starts at Temple Grounds - Landing Site",
            "Translator Gates: Vanilla (Colors)",
        ],
        "Logic Settings": [
            "All tricks disabled",
        ],
        "Item Pool": [
            "Size: 118 of 119",
            "Vanilla starting items",
            "Progressive Suit",
            "Split beam ammo",
            "Sky Temple Keys at all bosses",
        ],
    }


def test_echoes_format_params2(default_echoes_configuration):
    std_pick = default_echoes_configuration.standard_pickup_configuration
    # Setup
    layout_configuration = dataclasses.replace(
        default_echoes_configuration,
        available_locations=dataclasses.replace(
            default_echoes_configuration.available_locations,
            randomization_mode=RandomizationMode.MAJOR_MINOR_SPLIT,
        ),
        standard_pickup_configuration=dataclasses.replace(
            std_pick.replace_states(
                {
                    std_pick.get_pickup_with_name("Scan Visor"): StandardPickupState(),
                    std_pick.get_pickup_with_name("Dark Suit"): StandardPickupState(num_shuffled_pickups=1),
                    std_pick.get_pickup_with_name("Light Suit"): StandardPickupState(num_shuffled_pickups=1),
                    std_pick.get_pickup_with_name("Progressive Suit"): StandardPickupState(),
                }
            ),
            minimum_random_starting_pickups=1,
            maximum_random_starting_pickups=2,
        ),
        sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
        energy_per_tank=50,
        varia_suit_damage=21.2,
        safe_zone=dataclasses.replace(
            default_echoes_configuration.safe_zone,
            heal_per_second=2.5,
        ),
    )

    # Run
    result = RandovaniaGame.METROID_PRIME_ECHOES.data.layout.preset_describer.format_params(layout_configuration)

    # Assert
    assert result == {
        "Difficulty": [
            "Dark Aether deals 21.20 dmg/s to Varia, 1.20 dmg/s to Dark Suit",
            "50 energy per Energy Tank",
            "Safe Zones restore 2.50 energy/s",
        ],
        "Game Changes": [
            "Missiles needs Launcher, Power Bomb needs Main",
            "Warp to start, Menu Mod",
        ],
        "Gameplay": [
            "Starts at Temple Grounds - Landing Site",
            "Translator Gates: Vanilla (Colors)",
        ],
        "Logic Settings": [
            "All tricks disabled",
        ],
        "Item Pool": [
            "Major/minor split",
            "Major: 57/58",
            "Minor: 61/61",
            "1 to 2 random starting items",
            "Excludes Scan Visor",
            "Split beam ammo",
            "Sky Temple Keys at all bosses",
        ],
    }
