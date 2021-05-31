from random import Random
from typing import Dict, List

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintType, Hint, HintLocationPrecision
from randovania.game_description.world.world_list import WorldList
from randovania.games.prime.patcher_file_lib import hint_lib
from randovania.games.prime.patcher_file_lib.hint_formatters import LocationFormatter
from randovania.games.prime.patcher_file_lib.item_hints import create_pickup_hint
from randovania.games.prime.patcher_file_lib.temple_key_hint import create_temple_key_hint
from randovania.interface_common.players_configuration import PlayersConfiguration


class LocationHintCreator:
    world_list: WorldList
    area_namers: Dict[int, hint_lib.AreaNamer]
    joke_hints: List[str]

    def __init__(self, world_list: WorldList, area_namers: Dict[int, hint_lib.AreaNamer],
                 rng: Random, base_joke_hints: List[str]):
        self.world_list = world_list
        self.area_namers = area_namers
        self.rng = rng
        self.base_joke_hints = base_joke_hints
        self.joke_hints = []

    def create_joke_hint(self) -> str:
        if not self.joke_hints:
            self.joke_hints = sorted(self.base_joke_hints)
            self.rng.shuffle(self.joke_hints)
        return self.joke_hints.pop()

    def create_message_for_hint(self, hint: Hint,
                                all_patches: Dict[int, GamePatches],
                                players_config: PlayersConfiguration,
                                location_formatters: Dict[HintLocationPrecision, LocationFormatter],
                                ) -> str:
        if hint.hint_type == HintType.JOKE:
            return hint_lib.color_text(hint_lib.TextColor.JOKE, self.create_joke_hint())

        elif hint.hint_type == HintType.RED_TEMPLE_KEY_SET:
            return create_temple_key_hint(all_patches, players_config.player_index, hint.dark_temple, self.area_namers)

        else:
            assert hint.hint_type == HintType.LOCATION
            patches = all_patches[players_config.player_index]
            pickup_target = patches.pickup_assignment.get(hint.target)
            determiner, pickup_name = create_pickup_hint(patches.pickup_assignment,
                                                         self.world_list,
                                                         hint.precision.item,
                                                         pickup_target,
                                                         players_config,
                                                         hint.precision.include_owner)

            return location_formatters[hint.precision.location].format(
                determiner,
                hint_lib.color_text(hint_lib.TextColor.ITEM, pickup_name),
                hint,
            )
