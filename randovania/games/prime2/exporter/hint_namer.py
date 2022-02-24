from randovania.exporter.hints.hint_formatters import TemplatedFormatter
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintLocationPrecision
from randovania.games.common.prime_family.exporter.hint_namer import PrimeFamilyHintNamer, colorize_text
from randovania.games.prime2.exporter.hint_formaters import GuardianFormatter
from randovania.interface_common.players_configuration import PlayersConfiguration


class EchoesHintNamer(PrimeFamilyHintNamer):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        super().__init__(all_patches, players_config)

        self.location_formatters[HintLocationPrecision.KEYBEARER] = TemplatedFormatter(
            "The Flying Ing Cache in {node} contains {determiner}{pickup}.",
            self
        )
        self.location_formatters[HintLocationPrecision.GUARDIAN] = GuardianFormatter(
            lambda msg, with_color: colorize_text("#FF3333", msg, with_color),
        )
        self.location_formatters[HintLocationPrecision.LIGHT_SUIT_LOCATION] = TemplatedFormatter(
            "U-Mos's reward for returning the Sanctuary energy is {determiner}{pickup}.",
            self,
        )

    def format_temple_name(self, temple_name: str, with_color: bool) -> str:
        return colorize_text(self.color_item, temple_name, with_color)

    @property
    def color_joke(self) -> str:
        return "#45F731"

    @property
    def color_item(self) -> str:
        return "#FF6705B3"

    @property
    def color_player(self) -> str:
        return "#d4cc33"

    @property
    def color_location(self) -> str:
        return "#FF3333"
