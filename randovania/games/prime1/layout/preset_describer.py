from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime1.layout.prime_configuration import (
    DamageReduction,
    LayoutCutsceneMode,
    PrimeConfiguration,
    RoomRandoMode,
)
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
    message_for_required_mains,
)

if TYPE_CHECKING:
    from randovania.layout.base.base_configuration import BaseConfiguration

_PRIME1_CUTSCENE_MODE_DESCRIPTION = {
    LayoutCutsceneMode.MAJOR: "Major cutscene removal",
    LayoutCutsceneMode.MINOR: "Minor cutscene removal",
    LayoutCutsceneMode.COMPETITIVE: "Competitive cutscene removal",
    LayoutCutsceneMode.SKIPPABLE: None,
    LayoutCutsceneMode.SKIPPABLE_COMPETITIVE: "Competitive cutscenes",
    LayoutCutsceneMode.ORIGINAL: "Original cutscenes",
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
        ingame_difficulty = configuration.ingame_difficulty.description

        room_rando = _PRIME1_ROOM_RANDO_MODE_DESCRIPTION[configuration.room_rando]

        def describe_probability(probability: float, attribute: str) -> str | None:
            if probability == 0:
                return None

            return f"{probability / 10:.1f}% chance of {attribute}"

        superheated_probability = describe_probability(configuration.superheated_probability, "superheated")
        submerged_probability = describe_probability(configuration.submerged_probability, "submerged")

        def attribute_in_range(rand_range: tuple[float, float], attribute: str) -> str | None:
            if rand_range[0] == 1.0 and rand_range[1] == 1.0:
                return None
            elif rand_range[0] > rand_range[1]:
                rand_range = (rand_range[1], rand_range[0])

            return f"Random {attribute} within range {rand_range[0]} - {rand_range[1]}"

        def different_xyz_randomization(diff_xyz: bool) -> str | None:
            if enemy_rando_range_scale is None:
                return None
            elif diff_xyz:
                return "Enemies will be stretched randomly"
            return None

        if configuration.enemy_attributes is not None:
            enemy_rando_range_scale = attribute_in_range(
                (
                    configuration.enemy_attributes.enemy_rando_range_scale_low,
                    configuration.enemy_attributes.enemy_rando_range_scale_high,
                ),
                "Size",
            )
            enemy_rando_range_health = attribute_in_range(
                (
                    configuration.enemy_attributes.enemy_rando_range_health_low,
                    configuration.enemy_attributes.enemy_rando_range_health_high,
                ),
                "Health",
            )
            enemy_rando_range_speed = attribute_in_range(
                (
                    configuration.enemy_attributes.enemy_rando_range_speed_low,
                    configuration.enemy_attributes.enemy_rando_range_speed_high,
                ),
                "Speed",
            )
            enemy_rando_range_damage = attribute_in_range(
                (
                    configuration.enemy_attributes.enemy_rando_range_damage_low,
                    configuration.enemy_attributes.enemy_rando_range_damage_high,
                ),
                "Damage",
            )
            enemy_rando_range_knockback = attribute_in_range(
                (
                    configuration.enemy_attributes.enemy_rando_range_knockback_low,
                    configuration.enemy_attributes.enemy_rando_range_knockback_high,
                ),
                "Knockback",
            )
            enemy_rando_diff_xyz = different_xyz_randomization(configuration.enemy_attributes.enemy_rando_diff_xyz)
        else:
            enemy_rando_range_scale = None
            enemy_rando_range_health = None
            enemy_rando_range_speed = None
            enemy_rando_range_damage = None
            enemy_rando_range_knockback = None
            enemy_rando_diff_xyz = None

        extra_message_tree = {
            "Difficulty": [
                {f"Heat Damage: {configuration.heat_damage:.2f} dmg/s": configuration.heat_damage != 10.0},
                {f"{configuration.energy_per_tank} energy per Energy Tank": configuration.energy_per_tank != 100},
            ],
            "Gameplay": [
                {
                    f"Elevators: {configuration.teleporters.description('elevators')}": (
                        not configuration.teleporters.is_vanilla
                    )
                },
                {
                    "Dangerous Gravity Suit Logic": configuration.allow_underwater_movement_without_gravity,
                },
            ],
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Missiles needs Launcher": "Missile Expansion",
                        "Power Bomb needs Main": "Power Bomb Expansion",
                    },
                ),
                {
                    "Warp to start": configuration.warp_to_start,
                    "Final bosses removed": configuration.teleporters.skip_final_bosses,
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
                    cutscene_removal: cutscene_removal is not None,
                },
                {
                    ingame_difficulty: ingame_difficulty is not None,
                },
                {
                    "Unlocked Save Station doors": configuration.blue_save_doors,
                    "Blast Shield Lock-On": configuration.blast_shield_lockon,
                },
                {
                    enemy_rando_range_scale: enemy_rando_range_scale is not None,
                    enemy_rando_range_health: enemy_rando_range_health is not None,
                    enemy_rando_range_speed: enemy_rando_range_speed is not None,
                    enemy_rando_range_damage: enemy_rando_range_damage is not None,
                    enemy_rando_range_knockback: enemy_rando_range_knockback is not None,
                    enemy_rando_diff_xyz: enemy_rando_diff_xyz is not None,
                },
            ],
        }
        if enemy_rando_range_scale is not None:
            for listing in extra_message_tree["Game Changes"]:
                if "Random Boss Sizes" in listing.keys():
                    listing["Random Boss Sizes"] = False

        fill_template_strings_from_tree(template_strings, extra_message_tree)
        if configuration.damage_reduction != DamageReduction.DEFAULT:
            template_strings["Game Changes"].append(f"Damage reduction: {configuration.damage_reduction.value}")

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

        if configuration.legacy_mode:
            template_strings["Game Changes"].append("Legacy Mode")

        # Artifacts
        template_strings["Item Pool"].append(
            f"{configuration.artifact_target.num_artifacts} Artifacts, "
            f"{configuration.artifact_minimum_progression} min actions"
        )
        if configuration.pre_place_artifact:
            template_strings["Item Pool"].append("Pre-place Artifacts")
        if configuration.pre_place_phazon:
            template_strings["Item Pool"].append("Pre-place Phazon Suit")

        return template_strings
