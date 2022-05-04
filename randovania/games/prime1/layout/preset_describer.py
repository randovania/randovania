from attr import attr

from randovania.games.prime1.layout.hint_configuration import PhazonSuitHintMode
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration, LayoutCutsceneMode, RoomRandoMode
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

_PRIME1_PHAZON_SUIT_HINT = {
    PhazonSuitHintMode.DISABLED: None,
    PhazonSuitHintMode.HIDE_AREA: "Area only",
    PhazonSuitHintMode.PRECISE: "Area and room",
}

_PRIME1_ROOM_RANDO_MODE_DESCRIPTION = {
    RoomRandoMode.NONE: None,
    RoomRandoMode.ONE_WAY: "One-way Room Rando",
    RoomRandoMode.TWO_WAY: "Two-way Room Rando",
}

class PrimePresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, PrimeConfiguration)
        template_strings = super().format_params(configuration)
        cutscene_removal = _PRIME1_CUTSCENE_MODE_DESCRIPTION[configuration.qol_cutscenes]
        phazon_hint = _PRIME1_PHAZON_SUIT_HINT[configuration.hints.phazon_suit]

        room_rando = _PRIME1_ROOM_RANDO_MODE_DESCRIPTION[configuration.room_rando]

        def describe_probability(probability, attribute):
            if probability == 0:
                return None
            
            return "%.1f%% chance of %s" % (probability/10, attribute)
        
        superheated_probability = describe_probability(configuration.superheated_probability, "superheated")
        submerged_probability = describe_probability(configuration.submerged_probability, "submerged")

        extra_message_tree = {
            "Difficulty": [
                {"Heat Damage: {:.2f} dmg/s".format(configuration.heat_damage): configuration.heat_damage != 10.0},
                {f"Energy Tank: {configuration.energy_per_tank} energy": configuration.energy_per_tank != 100},
            ],
            "Gameplay": [
                {f"Elevators: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
                {
                    "Dangerous Gravity Suit Logic":
                        configuration.allow_underwater_movement_without_gravity,
                },
            ],
            "Quality of Life": [
                {
                    "Fixes to game breaking bugs": configuration.qol_game_breaking,
                    "Pickup scans": configuration.qol_pickup_scans,
                },
                {
                    f"Phazon suit hint: {phazon_hint}": phazon_hint is not None
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
                    "Large Samus": configuration.large_samus,
                },
                {
                    "Shuffle Item Position": configuration.shuffle_item_pos,
                    "Items Every Room": configuration.items_every_room,
                },
                {
                    "Random Boss Sizes": configuration.random_boss_sizes,
                    "No Doors": configuration.no_doors,
                },
                {
                    room_rando: room_rando is not None,
                },
                {
                    superheated_probability: superheated_probability is not None,
                    submerged_probability: submerged_probability is not None,
                },
                {
                    "Spring Ball": configuration.spring_ball,
                },
                {
                    "Deterministic I. Drone RNG": configuration.deterministic_idrone,
                    "Deterministic Maze RNG": configuration.deterministic_maze,
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
