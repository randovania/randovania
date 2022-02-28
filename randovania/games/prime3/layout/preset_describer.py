from randovania.game_description.item.major_item import MajorItem
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree, has_shuffled_item,
    message_for_required_mains, handle_progressive_expected_counts,
)


class CorruptionPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, CorruptionConfiguration)
        major_items = configuration.major_items_configuration
        template_strings = super().format_params(configuration)

        extra_message_tree = {
            "Item Pool": [
                {
                    "Progressive Missile": has_shuffled_item(major_items, "Progressive Missile"),
                    "Progressive Beam": has_shuffled_item(major_items, "Progressive Beam"),
                }
            ],
            "Difficulty": [
                {f"Energy Tank: {configuration.energy_per_tank} energy": configuration.energy_per_tank != 100},
            ],
            "Gameplay": [
                {f"Teleporters: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
            ],
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_configuration,
                    {
                        "Missiles needs Launcher": "Missile Expansion",
                        "Ship Missiles needs Main": "Ship Missile Expansion",
                    }
                ),
                {"Final bosses removed": configuration.elevators.skip_final_bosses},
            ]
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def expected_shuffled_item_count(self, configuration: BaseConfiguration) -> dict[MajorItem, int]:
        count = super().expected_shuffled_item_count(configuration)
        majors = configuration.major_items_configuration

        from randovania.games.prime3.item_database import progressive_items
        for (progressive_item_name, non_progressive_items) in progressive_items.tuples():
            handle_progressive_expected_counts(count, majors, progressive_item_name, non_progressive_items)

        return count
