from randovania.game_description import default_database
from randovania.game_description.item.major_item import MajorItem
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree, has_shuffled_item, message_for_required_mains, handle_progressive_expected_counts,
)


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
