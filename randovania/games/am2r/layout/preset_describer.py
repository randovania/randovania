from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.am2r.layout.am2r_configuration import AM2RArtifactConfig, AM2RConfiguration
from randovania.games.am2r.layout.hint_configuration import ItemHintMode
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
    message_for_required_mains,
)

if TYPE_CHECKING:
    from randovania.games.game import ProgressiveItemTuples
    from randovania.layout.base.base_configuration import BaseConfiguration


def describe_artifacts(artifacts: AM2RArtifactConfig) -> list[dict[str, bool]]:
    has_artifacts = artifacts.required_artifacts > 0
    if has_artifacts and artifacts.prefer_anywhere:
        return [
            {
                f"{artifacts.required_artifacts} Metroid DNA": True,
            },
            {
                "Place anywhere": artifacts.prefer_anywhere,
            },
        ]
    elif has_artifacts:
        return [
            {
                f"{artifacts.required_artifacts} Metroid DNA": True,
            },
            {
                "Prefers Metroids": artifacts.prefer_metroids,
                "Prefers major bosses": artifacts.prefer_bosses,
            },
        ]
    else:
        return [
            {
                "Kill the Queen": True,
            }
        ]


_AM2R_HINT_TEXT = {
    ItemHintMode.DISABLED: None,
    ItemHintMode.HIDE_AREA: "Area only",
    ItemHintMode.PRECISE: "Area and room",
}


class AM2RPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, AM2RConfiguration)
        template_strings = super().format_params(configuration)

        dna_hint = _AM2R_HINT_TEXT[configuration.hints.artifacts]
        ice_beam_hint = _AM2R_HINT_TEXT[configuration.hints.ice_beam]

        extra_message_tree = {
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Missiles need Launcher": "Missile Expansion",
                        "Super Missiles need Launcher": "Super Missile Expansion",
                        "Power Bombs need Launcher": "Power Bomb Expansion",
                    },
                ),
                {f"Energy per Tank: {configuration.energy_per_tank}": configuration.energy_per_tank != 100},
                {
                    "Enable Septoggs": configuration.septogg_helpers,
                    "Add new Nest Pipes": configuration.nest_pipes,
                    "Respawn bomb blocks": configuration.respawn_bomb_blocks,
                    "Softlock block checks": configuration.softlock_prevention_blocks,
                    "Screw blocks near Pipes": configuration.screw_blocks,
                    "Grave Grotto Bomb Blocks": configuration.grave_grotto_blocks,
                    "Industrial Complex Bomb Blocks": configuration.a3_entrance_blocks,
                },
                {
                    "Skip gameplay cutscenes": configuration.skip_cutscenes,
                    "Skip item cutscenes": configuration.skip_item_cutscenes,
                    "Enable Fusion Mode": configuration.fusion_mode,
                    "Open Missile Doors with Supers": configuration.supers_on_missile_doors,
                },
            ],
            "Goal": describe_artifacts(configuration.artifacts),
            "Hints": [
                {f"DNA Hint: {dna_hint}": dna_hint is not None},
                {f"Ice Beam Hint: {ice_beam_hint}": ice_beam_hint is not None},
            ],
        }

        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def progressive_items(self) -> ProgressiveItemTuples:
        from randovania.games.am2r.pickup_database import progressive_items

        return progressive_items.tuples()
