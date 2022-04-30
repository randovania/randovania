from randovania.game_description import default_database
from randovania.game_description.item.major_item import MajorItem
from randovania.games.prime2.layout.beam_configuration import BeamConfiguration, BeamAmmoConfiguration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree, has_shuffled_item, message_for_required_mains, handle_progressive_expected_counts,
)


def create_beam_configuration_description(beams: BeamConfiguration) -> list[dict[str, bool]]:
    beam_names = ["Power", "Dark", "Light", "Annihilator"]
    default_config = BeamConfiguration(
        power=BeamAmmoConfiguration(0, -1, -1, 0, 0, 5, 0),
        dark=BeamAmmoConfiguration(1, 45, -1, 1, 5, 5, 30),
        light=BeamAmmoConfiguration(2, 46, -1, 1, 5, 5, 30),
        annihilator=BeamAmmoConfiguration(3, 46, 45, 1, 5, 5, 30),
    )
    id_to_name = {
        -1: "Nothing",
        43: "Power Bomb",
        44: "Missile",
        45: "Dark Ammo",
        46: "Light Ammo",
    }

    result = []

    def format_ammo_cost(b: BeamAmmoConfiguration) -> list[str]:
        if b.ammo_a == b.ammo_b == -1:
            return [""]

        return [
            f"{b.uncharged_cost} (Uncharged)",
            f"{b.charged_cost} (Charged)",
            f"{b.combo_ammo_cost} (Combo)",
        ]

    def format_different_ammo_cost(actual: BeamAmmoConfiguration, default: BeamAmmoConfiguration):
        a1 = format_ammo_cost(actual)
        d1 = format_ammo_cost(default)

        return "/".join(
            a
            for a, d in zip(a1, d1)
            if a != d
        )

    def format_ammo_name(b: BeamAmmoConfiguration) -> str:
        if b.ammo_a == b.ammo_b == -1:
            return "no ammo"

        names = [id_to_name[b.ammo_a], id_to_name[b.ammo_b]]
        if "Nothing" in names:
            names.remove("Nothing")

        if all(" Ammo" in n for n in names) and len(names) > 1:
            names[0] = names[0].replace(" Ammo", "")

        return " and ".join(names)

    def format_missile_cost(b: BeamAmmoConfiguration) -> str:
        return "{missiles} missiles for combo".format(
            missiles=b.combo_missile_cost,
        )

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
            description = "{beam} Beam uses {different}".format(
                beam=name,
                different=", ".join(different)
            )
            result.append({description: True})

    return result


class EchoesPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, EchoesConfiguration)
        major_items = configuration.major_items_configuration
        item_database = default_database.item_database_for_game(configuration.game)

        template_strings = super().format_params(configuration)
        unified_ammo = configuration.ammo_configuration.items_state[item_database.ammo["Beam Ammo Expansion"]]

        # Difficulty
        if (configuration.varia_suit_damage, configuration.dark_suit_damage) != (6, 1.2):
            template_strings["Difficulty"].append("Dark Aether: {:.2f} dmg/s Varia, {:.2f} dmg/s Dark".format(
                configuration.varia_suit_damage, configuration.dark_suit_damage
            ))

        if configuration.energy_per_tank != 100:
            template_strings["Difficulty"].append(f"Energy Tank: {configuration.energy_per_tank} energy")

        if configuration.safe_zone.heal_per_second != 1:
            template_strings["Difficulty"].append(f"Safe Zone: {configuration.safe_zone.heal_per_second:.2f} energy/s")

        extra_message_tree = {
            "Item Pool": [
                {
                    "Progressive Suit": has_shuffled_item(major_items, "Progressive Suit"),
                    "Progressive Grapple": has_shuffled_item(major_items, "Progressive Grapple"),
                    "Split beam ammo": unified_ammo.pickup_count == 0,
                }
            ],
            "Difficulty": [
                {"1-HP Mode": configuration.dangerous_energy_tank},
            ],
            "Gameplay": [
                {f"Translator Gates: {configuration.translator_configuration.description()}": True},
                {f"Elevators: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
            ],
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_configuration,
                    {
                        "Missiles needs Launcher": "Missile Expansion",
                        "Power Bomb needs Main": "Power Bomb Expansion",
                    }
                ),
                {"Warp to start": configuration.warp_to_start,
                 "Menu Mod": configuration.menu_mod,
                 "Final bosses removed": configuration.elevators.skip_final_bosses},
                *create_beam_configuration_description(configuration.beam_configuration),
            ]
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        # Sky Temple Keys
        if configuration.sky_temple_keys == LayoutSkyTempleKeyMode.ALL_BOSSES:
            template_strings["Item Pool"].append("Sky Temple Keys at all bosses")
        elif configuration.sky_temple_keys == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
            template_strings["Item Pool"].append("Sky Temple Keys at all guardians")
        else:
            template_strings["Item Pool"].append(f"{configuration.sky_temple_keys.num_keys} Sky Temple Keys")

        return template_strings

    def expected_shuffled_item_count(self, configuration: BaseConfiguration) -> dict[MajorItem, int]:
        count = super().expected_shuffled_item_count(configuration)
        majors = configuration.major_items_configuration

        from randovania.games.prime2.item_database import progressive_items
        for (progressive_item_name, non_progressive_items) in progressive_items.tuples():
            handle_progressive_expected_counts(count, majors, progressive_item_name, non_progressive_items)

        return count
