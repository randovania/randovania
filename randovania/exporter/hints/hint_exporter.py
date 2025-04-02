from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter.hints import pickup_hint
from randovania.exporter.hints.temple_key_hint import create_temple_key_hint
from randovania.game_description.hint import Hint, JokeHint, LocationHint, RedTempleHint, SpecificHintPrecision
from randovania.games.prime2.exporter.hint_namer import EchoesHintNamer
from randovania.layout import filtered_database

if TYPE_CHECKING:
    from random import Random

    from randovania.exporter.hints.hint_namer import HintNamer


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

    def create_message_for_hint(
        self,
        hint: Hint,
        with_color: bool,
    ) -> str:
        all_patches = self.namer.all_patches
        players_config = self.namer.players_config

        patches = all_patches[players_config.player_index]

        if isinstance(hint, JokeHint):
            return self.namer.format_joke(self.create_joke_hint(), with_color)

        elif isinstance(hint, RedTempleHint):
            assert isinstance(self.namer, EchoesHintNamer)
            return create_temple_key_hint(
                all_patches, players_config.player_index, hint.dark_temple, self.namer, with_color
            )

        else:
            assert isinstance(hint, LocationHint)
            assert hint.precision.include_owner is not None
            assert not isinstance(hint.precision.item, SpecificHintPrecision)

            configuration = all_patches[players_config.player_index].configuration

            pickup_target = patches.pickup_assignment.get(hint.target)
            phint = pickup_hint.create_pickup_hint(
                patches.pickup_assignment,
                filtered_database.game_description_for_layout(configuration).region_list,
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
