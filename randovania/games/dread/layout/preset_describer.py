from randovania.game_description.item.major_item import MajorItem
from randovania.games.dread.layout.dread_configuration import DreadConfiguration, DreadArtifactConfig
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree, message_for_required_mains, handle_progressive_expected_counts, has_shuffled_item,
)


def describe_artifacts(artifacts: DreadArtifactConfig) -> list[dict[str, bool]]:
    has_artifacts = artifacts.required_artifacts > 0
    if has_artifacts:
        return [
            {
                f"{artifacts.required_artifacts} Metroid DNA": True,
            },
            {
                "Prefers E.M.M.I.": artifacts.prefer_emmi,
                "Prefers major bosses": artifacts.prefer_major_bosses,
            }
        ]
    else:
        return [
            {
                "Reach Itorash": True,
            }
        ]


class DreadPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, DreadConfiguration)

        major_items = configuration.major_items_configuration
        template_strings = super().format_params(configuration)

        
        if configuration.linear_dps > 0 and configuration.linear_damage_runs:
            template_strings["Difficulty"].append(f"Damage Rooms: {configuration.linear_dps} damage per second")
        elif configuration.linear_dps <= 0 and configuration.linear_damage_runs:
            template_strings["Difficulty"].append(f"Damage Rooms: Off")

        extra_message_tree = {
            "Difficulty": [
                {
                    "Immediate Energy Part": configuration.immediate_energy_parts,
                },
                {
                    f"Energy Tank: {configuration.energy_per_tank} energy": configuration.energy_per_tank != 100
                },
            ],
            "Item Pool": [
                {
                    "Progressive Beam": has_shuffled_item(major_items, "Progressive Beam"),
                    "Progressive Charge Beam": has_shuffled_item(major_items, "Progressive Charge Beam"),
                    "Progressive Missile": has_shuffled_item(major_items, "Progressive Missile"),
                    "Progressive Bomb": has_shuffled_item(major_items, "Progressive Bomb"),
                    "Progressive Suit": has_shuffled_item(major_items, "Progressive Suit"),
                    "Progressive Spin": has_shuffled_item(major_items, "Progressive Spin")
                }
            ],
            "Gameplay": [
                {f"Elevators/Shuttles: {configuration.elevators.description()}": not configuration.elevators.is_vanilla}
            ],
            "Goal": describe_artifacts(configuration.artifacts),
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_configuration,
                    {
                        "Power Bomb needs Main": "Power Bomb Expansion",
                    }
                ),
                {
                    "Open Hanubia Shortcut": configuration.hanubia_shortcut_no_grapple,
                    "Easier Path to Itorash in Hanubia": configuration.hanubia_easier_path_to_itorash
                },
                {
                    "X Starts Released": configuration.x_starts_released,
                },
                {
                    "Linear Damage Run Scaling": configuration.linear_damage_runs
                }
            ]
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def expected_shuffled_item_count(self, configuration: BaseConfiguration) -> dict[MajorItem, int]:
        count = super().expected_shuffled_item_count(configuration)
        majors = configuration.major_items_configuration

        from randovania.games.dread.item_database import progressive_items
        for (progressive_item_name, non_progressive_items) in progressive_items.tuples():
            handle_progressive_expected_counts(count, majors, progressive_item_name, non_progressive_items)

        return count
