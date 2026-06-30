from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description import default_database
from randovania.games.prime2.layout.beam_configuration import BeamAmmoConfiguration, BeamConfiguration
from randovania.games.prime2.layout.echoes_configuration import (
    EchoesConfiguration,
    LayoutSkyTempleKeyMode,
)
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
    message_for_required_mains,
)

if TYPE_CHECKING:
    from randovania.game.gui import ProgressiveItemTuples
    from randovania.games.prime2_opr.layout.prime2_opr_configuration import EchoesOPRConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


def create_beam_configuration_description(
    beams: BeamConfiguration,
) -> list[dict[str, bool]]:
    beam_names = ["Power", "Dark", "Light", "Annihilator"]
    default_config = BeamConfiguration(
        power=BeamAmmoConfiguration(None, None, 0, 0, 5, 0),
        dark=BeamAmmoConfiguration(45, None, 1, 5, 5, 30),
        light=BeamAmmoConfiguration(46, None, 1, 5, 5, 30),
        annihilator=BeamAmmoConfiguration(46, 45, 1, 5, 5, 30),
    )
    id_to_name = {
        None: "Nothing",
        43: "Power Bomb",
        44: "Missile",
        45: "Dark Ammo",
        46: "Light Ammo",
    }

    result = []

    def format_ammo_cost(b: BeamAmmoConfiguration) -> list[str]:
        if b.ammo_a is b.ammo_b is None:
            return [""]

        return [
            f"{b.uncharged_cost} (Uncharged)",
            f"{b.charged_cost} (Charged)",
            f"{b.combo_ammo_cost} (Combo)",
        ]

    def format_different_ammo_cost(actual: BeamAmmoConfiguration, default: BeamAmmoConfiguration) -> str:
        a1 = format_ammo_cost(actual)
        d1 = format_ammo_cost(default)

        return "/".join(a for a, d in zip(a1, d1) if a != d)

    def format_ammo_name(b: BeamAmmoConfiguration) -> str:
        if b.ammo_a is b.ammo_b is None:
            return "no ammo"

        names = [id_to_name[b.ammo_a], id_to_name[b.ammo_b]]
        if "Nothing" in names:
            names.remove("Nothing")

        if all(" Ammo" in n for n in names) and len(names) > 1:
            names[0] = names[0].replace(" Ammo", "")

        return " and ".join(names)

    def format_missile_cost(b: BeamAmmoConfiguration) -> str:
        return f"{b.combo_missile_cost} missiles for combo"

    for name, default_beam, actual_beam in zip(beam_names, default_config.all_beams, beams.all_beams):
        different = []

        ammo_cost = format_different_ammo_cost(actual_beam, default_beam)
        ammo_name = format_ammo_name(actual_beam)
        if ammo_name != format_ammo_name(default_beam) or ammo_cost:
            if ammo_name != "no ammo" and ammo_cost:
                different.append(f"{ammo_cost} {ammo_name}")
            else:
                different.append(ammo_name)

        missile_cost = format_missile_cost(actual_beam)
        if missile_cost != format_missile_cost(default_beam):
            different.append(missile_cost)

        if different:
            description = "{beam} Beam uses {different}".format(beam=name, different=", ".join(different))
            result.append({description: True})

    return result


def shared_preset_description(
    template_strings: dict[str, list[str]], configuration: EchoesConfiguration | EchoesOPRConfiguration
) -> dict[str, list[str]]:
    """Shared logic between Echoes and EchoesOPR"""
    pickup_database = default_database.pickup_database_for_game(configuration.game)

    unified_ammo = configuration.ammo_pickup_configuration.pickups_state[
        pickup_database.ammo_pickups["Beam Ammo Expansion"]
    ]

    # Difficulty
    if (configuration.varia_suit_damage, configuration.dark_suit_damage) != (
        6,
        1.2,
    ):
        template_strings["Difficulty"].append(
            f"Dark Aether deals {configuration.varia_suit_damage:.2f} dmg/s to Varia, "
            f"{configuration.dark_suit_damage:.2f} dmg/s to Dark Suit"
        )

    if configuration.energy_per_tank != 100:
        template_strings["Difficulty"].append(f"{configuration.energy_per_tank} energy per Energy Tank")

    if configuration.safe_zone.heal_per_second != 1:
        template_strings["Difficulty"].append(
            f"Safe Zones restore {configuration.safe_zone.heal_per_second:.2f} energy/s"
        )

    extra_message_tree = {
        "Pickup Pool": [
            {
                "Split beam ammo": unified_ammo.pickup_count == 0,
            }
        ],
        "Difficulty": [
            {"1-HP Mode": configuration.dangerous_energy_tank},
        ],
        "Gameplay": [
            {f"Translator Gates: {configuration.translator_configuration.description()}": True},
            {
                f"Elevators: {configuration.teleporters.description('elevators')}": (
                    not configuration.teleporters.is_vanilla
                )
            },
        ],
        "Game Changes": [
            {
                "Final bosses removed": configuration.teleporters.skip_final_bosses,
                "Unlocked Save Station doors": configuration.blue_save_doors,
                "Inverted Aether": configuration.inverted_mode,
            },
            *create_beam_configuration_description(configuration.beam_configuration),
        ],
    }
    fill_template_strings_from_tree(template_strings, extra_message_tree)

    # Sky Temple Keys
    if configuration.sky_temple_keys == LayoutSkyTempleKeyMode.ALL_BOSSES:
        template_strings["Pickup Pool"].append("Sky Temple Keys at all bosses")
    elif configuration.sky_temple_keys == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        template_strings["Pickup Pool"].append("Sky Temple Keys at all guardians")
    else:
        template_strings["Pickup Pool"].append(f"{configuration.sky_temple_keys.num_keys} Sky Temple Keys")

    return template_strings


class EchoesPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, EchoesConfiguration)

        template_strings = super().format_params(configuration)
        template_strings = shared_preset_description(template_strings, configuration)

        extra_message_tree = {
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Missiles needs Launcher": "Missile Expansion",
                        "Power Bomb needs Main": "Power Bomb Expansion",
                    },
                    mains_are_default_required=False,
                ),
                {
                    "Warp to start": configuration.warp_to_start,
                    "Menu Mod": configuration.menu_mod,
                },
                {"New Patcher": configuration.use_new_patcher.is_enabled()},
            ],
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def progressive_items(self) -> ProgressiveItemTuples:
        from randovania.games.prime2.layout import progressive_items

        return progressive_items.tuples()
