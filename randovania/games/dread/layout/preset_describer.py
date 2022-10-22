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


def _format_environmental_damage(configuration: DreadConfiguration):
    def format_dmg(value: int | None):
        if value is None:
            return "Unmodified"
        elif value == 0:
            return "Removed"
        else:
            return f"Constant {value} dmg/s"
        pass

    return [
        {f"{name}: {format_dmg(dmg)}": True}
        for name, dmg in [("Heat", configuration.constant_heat_damage),
                          ("Cold", configuration.constant_cold_damage),
                          ("Lava", configuration.constant_lava_damage)]
    ]


class DreadPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, DreadConfiguration)

        major_items = configuration.major_items_configuration
        template_strings = super().format_params(configuration)

        extra_message_tree = {
            "Logic Settings": [
                {
                    "Highly Dangerous Logic":
                        configuration.allow_highly_dangerous_logic,
                }
            ],
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
            ],
            "Environmental Damage": _format_environmental_damage(configuration),
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
