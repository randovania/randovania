import copy
from dataclasses import dataclass
from typing import Dict, Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.game_description import default_database
from randovania.game_description.item.ammo import Ammo
from randovania.games.game import RandovaniaGame
from randovania.layout.base.ammo_state import AmmoState


@dataclass(frozen=True)
class AmmoConfiguration(bitpacking.BitPackValue):
    items_state: Dict[Ammo, AmmoState]

    def __post_init__(self):
        for ammo, state in self.items_state.items():
            state.check_consistency(ammo)

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        default: AmmoConfiguration = metadata["reference"]

        assert list(self.items_state.keys()) == list(default.items_state.keys())

        for ammo, this in self.items_state.items():
            reference = default.items_state[ammo]
            is_different = this != reference
            yield from bitpacking.encode_bool(is_different)
            if is_different:
                yield from this.bit_pack_encode({
                    "ammo": ammo,
                })

    @classmethod
    def bit_pack_unpack(cls, decoder: bitpacking.BitPackDecoder, metadata):
        default: AmmoConfiguration = metadata["reference"]

        items_state = {}
        for ammo, default_state in default.items_state.items():
            is_different = bitpacking.decode_bool(decoder)
            if is_different:
                items_state[ammo] = AmmoState.bit_pack_unpack(decoder, {"ammo": ammo})
            else:
                items_state[ammo] = default_state

        return cls(items_state)

    @property
    def as_json(self) -> dict:
        return {
            "items_state": {
                ammo.name: state.as_json
                for ammo, state in self.items_state.items()
            },
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame) -> "AmmoConfiguration":
        item_database = default_database.item_database_for_game(game)
        return cls(
            items_state={
                item_database.ammo[name]: AmmoState.from_json(state)
                for name, state in value["items_state"].items()
            },
        )

    def replace_state_for_ammo(self, ammo: Ammo, state: AmmoState) -> "AmmoConfiguration":
        return self.replace_states({ammo: state})

    def replace_states(self, new_states: Dict[Ammo, AmmoState]) -> "AmmoConfiguration":
        """
        Creates a copy of this AmmoConfiguration where the state of all given items are replaced by the given
        states.
        :param new_states:
        :return:
        """
        items_state = copy.copy(self.items_state)

        for item, state in new_states.items():
            items_state[item] = state

        return AmmoConfiguration(items_state)
