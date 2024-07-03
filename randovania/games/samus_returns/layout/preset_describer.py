from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.layout.hint_configuration import ItemHintMode
from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig, MSRConfiguration
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
    has_shuffled_item,
    message_for_required_mains,
)

if TYPE_CHECKING:
    from randovania.games.game import ProgressiveItemTuples
    from randovania.layout.base.base_configuration import BaseConfiguration


def describe_artifacts(artifacts: MSRArtifactConfig) -> list[dict[str, bool]]:
    has_artifacts = artifacts.required_artifacts > 0
    if has_artifacts and artifacts.prefer_anywhere:
        return [
            {
                f"{artifacts.required_artifacts} Metroid DNA": True,
            },
            {
                "Place at any item location": artifacts.prefer_anywhere,
            },
        ]
    elif has_artifacts:
        return [
            {
                f"{artifacts.required_artifacts} Metroid DNA": True,
            },
            {
                "Prefers Standard Metroids": artifacts.prefer_metroids,
                "Prefers Stronger Metroids": artifacts.prefer_stronger_metroids,
                "Prefers Bosses": artifacts.prefer_bosses,
            },
        ]
    else:
        return [
            {
                "Defeat Proteus Ridley": True,
            }
        ]


def format_environmental_damage(configuration: MSRConfiguration) -> list:
    def format_dmg(value: int | None) -> str:
        if value is None:
            return "Unmodified"
        elif value == 0:
            return "Removed"
        else:
            return f"Constant {value} dmg/s"

    return [
        {f"{name}: {format_dmg(dmg)}": True}
        for name, dmg in [
            ("Heat", configuration.constant_heat_damage),
            ("Lava", configuration.constant_lava_damage),
        ]
    ]


_MSR_HINT_TEXT = {
    ItemHintMode.DISABLED: None,
    ItemHintMode.HIDE_AREA: "Area only",
    ItemHintMode.PRECISE: "Area and room",
}


class MSRPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, MSRConfiguration)

        standard_pickups = configuration.standard_pickup_configuration
        template_strings = super().format_params(configuration)

        dna_hint = _MSR_HINT_TEXT[configuration.hints.artifacts]
        baby_hint = _MSR_HINT_TEXT[configuration.hints.baby_metroid]

        extra_message_tree = {
            "Logic Settings": [
                {
                    "Highly Dangerous Logic": configuration.allow_highly_dangerous_logic,
                }
            ],
            "Difficulty": [
                {f"{configuration.energy_per_tank} energy per Energy Tank": configuration.energy_per_tank != 100},
                {
                    f"Energy Reserve Tank restores {configuration.life_tank_size} Energy": configuration.life_tank_size
                    != 299
                },
                {
                    f"Aeion Reserve Tank restores {configuration.aeion_tank_size} Aeion": configuration.aeion_tank_size
                    != 500
                },
                {
                    f"Missile Reserve Tank restores {configuration.missile_tank_size} Missiles, \
                            {configuration.super_missile_tank_size} Super Missiles": configuration.missile_tank_size
                    != 30
                    or configuration.super_missile_tank_size != 10
                },
            ],
            "Item Pool": [
                {
                    "Energy Reserve Tank": has_shuffled_item(standard_pickups, "Energy Reserve Tank"),
                    "Aeion Reserve Tank": has_shuffled_item(standard_pickups, "Aeion Reserve Tank"),
                    "Missile Reserve Tank": has_shuffled_item(standard_pickups, "Missile Reserve Tank"),
                },
            ],
            "Gameplay": [
                {
                    f"Elevators: {configuration.teleporters.description('elevators')}": (
                        not configuration.teleporters.is_vanilla
                    )
                },
            ],
            "Goal": describe_artifacts(configuration.artifacts),
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Missile needs Launcher": "Missile Tank",
                        "Super Missile needs Launcher": "Super Missile Tank",
                        "Power Bomb needs Launcher": "Power Bomb Tank",
                    },
                ),
                {
                    "Charge Beam Door Buff": configuration.charge_door_buff,
                    "Beam Door Buff": configuration.beam_door_buff,
                    "Beam Burst Buff": configuration.beam_burst_buff,
                    "Missile Door Buff": configuration.nerf_super_missiles,
                },
                {
                    "Open Area 3 Factory Interior East Shortcut": configuration.area3_interior_shortcut_no_grapple,
                    "Remove Area Exit Grapple Blocks": configuration.elevator_grapple_blocks,
                },
                {
                    "Change Surface Cavern Cavity Crumble Blocks": configuration.surface_crumbles,
                    "Change Area 1 Transport to Surface and Area 2 Crumble Blocks": configuration.area1_crumbles,
                },
                {
                    "Enable Reverse Area 8": configuration.reverse_area8,
                },
            ],
            "Hints": [
                {f"Baby Metroid Hint: {baby_hint}": baby_hint is not None},
                {f"DNA Hints: {dna_hint}": dna_hint is not None},
            ],
            "Environmental Damage": format_environmental_damage(configuration),
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def progressive_items(self) -> ProgressiveItemTuples:
        from randovania.games.samus_returns.pickup_database import progressive_items

        return progressive_items.tuples()
