from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.hints.basic_hint_formatters import basic_hint_formatters
from randovania.exporter.hints.hint_formatters import TemplatedFormatter
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.interface_common.players_configuration import PlayersConfiguration


class CSHintNamer(HintNamer[None]):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        super().__init__(all_patches, players_config)

        patches = all_patches[players_config.player_index]

        location_hint_template = "{{start}} {determiner}{pickup} {{mid}} in {node}."
        self.location_formatters = basic_hint_formatters(
            self,
            location_hint_template,
            patches,
            lambda msg, with_color: msg,
            players_config,
            with_region=False,
        )

        def feat(loc: str) -> HintFeature:
            return patches.game.hint_feature_database[loc]

        self.location_formatters.update(
            {
                feat("specific_hint_malco"): TemplatedFormatter(
                    "BUT ALL I KNOW HOW TO DO IS MAKE {determiner.upper}{pickup}...", self, upper_pickup=True
                ),
                feat("specific_hint_jenka"): TemplatedFormatter(
                    "perhaps I'll give you {determiner}{pickup} in return...", self
                ),
                feat("specific_hint_little"): TemplatedFormatter(
                    "He was exploring the island with {determiner}{pickup}...", self
                ),
                feat("specific_hint_numahachi"): TemplatedFormatter("{determiner.capitalize}{pickup}.", self),
            }
        )

    @override
    def format_guaranteed_resource(
        self,
        resource: ItemResourceInfo,
        world_name: str | None,
        location: PickupLocation,
        hide_area: bool,
        with_color: bool,
    ) -> str:
        # TODO
        raise NotImplementedError

    @override
    @property
    def color_default(self) -> None:
        return None
