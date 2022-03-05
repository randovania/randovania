from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration, LayoutCutsceneMode
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree, message_for_required_mains,
)

_PRIME1_CUTSCENE_MODE_DESCRIPTION = {
    LayoutCutsceneMode.MAJOR: "Major cutscene removal",
    LayoutCutsceneMode.MINOR: "Minor cutscene removal",
    LayoutCutsceneMode.COMPETITIVE: "Competitive cutscene removal",
    LayoutCutsceneMode.ORIGINAL: None,
}


class PrimePresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, PrimeConfiguration)
        template_strings = super().format_params(configuration)
        cutscene_removal = _PRIME1_CUTSCENE_MODE_DESCRIPTION[configuration.qol_cutscenes]

        extra_message_tree = {
            "Difficulty": [
                {"Heat Damage: {:.2f} dmg/s".format(configuration.heat_damage): configuration.heat_damage != 10.0},
                {f"Energy Tank: {configuration.energy_per_tank} energy": configuration.energy_per_tank != 100},
            ],
            "Gameplay": [
                {f"Elevators: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
                {
                    "Underwater movement without Gravity allowed":
                        configuration.allow_underwater_movement_without_gravity,
                },
            ],
            "Quality of Life": [
                {
                    "Fixes to game breaking bugs": configuration.qol_game_breaking,
                    "Pickup scans": configuration.qol_pickup_scans,
                }
            ],
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_configuration,
                    {
                        "Missiles needs Launcher": "Missile Expansion",
                        "Power Bomb needs Main": "Power Bomb Expansion",
                    }
                ),
                {
                    "Varia-only heat protection": configuration.heat_protection_only_varia,
                    "Progressive suit damage reduction": configuration.progressive_damage_reduction,
                },
                {
                    "Warp to start": configuration.warp_to_start,
                    "Final bosses removed": configuration.elevators.skip_final_bosses,
                    "Unlocked Vault door": configuration.main_plaza_door,
                    "Phazon Elite without Dynamo": configuration.phazon_elite_without_dynamo,
                },
                {
                    "Small Samus": configuration.small_samus,
                },
                {
                    "Shuffle Item Position": configuration.shuffle_item_pos,
                    "Items Every Room": configuration.items_every_room,
                },
                {
                    "Spring Ball": configuration.spring_ball,
                },
                {
                    "Deterministic I. Drone RNG": configuration.deterministic_idrone,
                },
                {
                    cutscene_removal: cutscene_removal is not None,
                }
            ],
        }

        fill_template_strings_from_tree(template_strings, extra_message_tree)

        backwards = [
            message
            for flag, message in [
                (configuration.backwards_frigate, "Frigate"),
                (configuration.backwards_labs, "Labs"),
                (configuration.backwards_upper_mines, "Upper Mines"),
                (configuration.backwards_lower_mines, "Lower Mines"),
            ]
            if flag
        ]
        if backwards:
            template_strings["Game Changes"].append("Allowed backwards: {}".format(", ".join(backwards)))

        # Artifacts
        template_strings["Item Pool"].append(f"{configuration.artifact_target.num_artifacts} Artifacts, "
                                             f"{configuration.artifact_minimum_progression} min actions")

        return template_strings
