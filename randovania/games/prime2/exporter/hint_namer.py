from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.hints.hint_formatters import TemplatedFormatter
from randovania.games.common.prime_family.exporter.hint_namer import PrimeFamilyHintNamer
from randovania.games.prime2.exporter.hint_formaters import GuardianFormatter

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.hint_features import HintFeature
    from randovania.interface_common.players_configuration import PlayersConfiguration


class EchoesHintNamer(PrimeFamilyHintNamer):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        super().__init__(all_patches, players_config)

        patches = all_patches[players_config.player_index]

        def feat(loc: str) -> HintFeature:
            return patches.game.hint_feature_database[loc]

        self.location_formatters[feat("specific_hint_keybearer")] = TemplatedFormatter(
            "The Flying Ing Cache in {node} contains {determiner}{pickup}.", self
        )
        self.location_formatters[feat("specific_hint_guardian")] = GuardianFormatter(
            lambda msg, with_color: self.colorize_text("#FF3333", msg, with_color),
        )
        self.location_formatters[feat("specific_hint_2mos")] = TemplatedFormatter(
            "U-Mos's reward for returning the Sanctuary energy is {determiner}{pickup}.",
            self,
        )

    def format_temple_name(self, temple_name: str, with_color: bool) -> str:
        return self.colorize_text(self.color_item, temple_name, with_color)

    @override
    @property
    def color_joke(self) -> str:
        return "#45F731"

    @override
    @property
    def color_item(self) -> str:
        return "#FF6705B3"

    @override
    @property
    def color_world(self) -> str:
        return "#d4cc33"

    @override
    @property
    def color_location(self) -> str:
        return "#FF3333"
