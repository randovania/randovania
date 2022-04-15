from random import Random

from randovania.exporter.hints import pickup_hint
from randovania.exporter.hints.hint_namer import HintNamer
from randovania.exporter.hints.temple_key_hint import create_temple_key_hint
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout import filtered_database


class HintExporter:
    namer: HintNamer
    joke_hints: list[str]

    def __init__(self, namer: HintNamer, rng: Random, base_joke_hints: list[str]):
        self.namer = namer
        self.rng = rng
        self.base_joke_hints = base_joke_hints
        self.joke_hints = []

    def create_joke_hint(self) -> str:
        if not self.joke_hints:
            self.joke_hints = sorted(self.base_joke_hints)
            self.rng.shuffle(self.joke_hints)
        return self.joke_hints.pop()

    def create_message_for_hint(self, hint: Hint,
                                all_patches: dict[int, GamePatches],
                                players_config: PlayersConfiguration,
                                with_color: bool,
                                ) -> str:
        patches = all_patches[players_config.player_index]

        if hint.hint_type == HintType.JOKE:
            return self.namer.format_joke(self.create_joke_hint(), with_color)

        elif hint.hint_type == HintType.RED_TEMPLE_KEY_SET:
            return create_temple_key_hint(all_patches, players_config.player_index, hint.dark_temple, self.namer,
                                          with_color)

        else:
            assert hint.hint_type == HintType.LOCATION

            configuration = all_patches[players_config.player_index].configuration

            pickup_target = patches.pickup_assignment.get(hint.target)
            phint = pickup_hint.create_pickup_hint(
                patches.pickup_assignment,
                filtered_database.game_description_for_layout(configuration).world_list,
                hint.precision.item,
                pickup_target,
                players_config,
                hint.precision.include_owner,
            )
            return self.namer.format_location_hint(
                configuration.game,
                phint,
                hint,
                with_color,
            )
