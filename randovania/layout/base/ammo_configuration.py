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
    maximum_ammo: Dict[int, int]
    items_state: Dict[Ammo, AmmoState]

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        default: AmmoConfiguration = metadata["reference"]

        assert list(self.maximum_ammo.keys()) == list(default.maximum_ammo.keys())
        assert list(self.items_state.keys()) == list(default.items_state.keys())

        for this, reference in zip(self.maximum_ammo.values(), default.maximum_ammo.values()):
            is_different = this != reference
            yield from bitpacking.encode_bool(is_different)
            if is_different:
                yield this, 256

        for this, reference in zip(self.items_state.values(), default.items_state.values()):
            is_different = this != reference
            yield from bitpacking.encode_bool(is_different)
            if is_different:
                yield from this.bit_pack_encode({})

    @classmethod
    def bit_pack_unpack(cls, decoder: bitpacking.BitPackDecoder, metadata):
        default: AmmoConfiguration = metadata["reference"]

        # Maximum Ammo
        maximum_ammo = {}
        for item_key, default_value in default.maximum_ammo.items():
            is_different = bitpacking.decode_bool(decoder)
            if is_different:
                maximum_ammo[item_key] = decoder.decode_single(256)
            else:
                maximum_ammo[item_key] = default_value

        items_state = {}
        for item, default_state in default.items_state.items():
            is_different = bitpacking.decode_bool(decoder)
            if is_different:
                items_state[item] = AmmoState.bit_pack_unpack(decoder, {})
            else:
                items_state[item] = default_state

        return cls(maximum_ammo, items_state)

    @property
    def as_json(self) -> dict:
        return {
            "maximum_ammo": {
                str(ammo_item): maximum
                for ammo_item, maximum in self.maximum_ammo.items()
            },
            "items_state": {
                ammo.name: state.as_json
                for ammo, state in self.items_state.items()
            },
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame) -> "AmmoConfiguration":
        item_database = default_database.item_database_for_game(game)
        return cls(
            maximum_ammo={
                int(ammo_item): maximum
                for ammo_item, maximum in value["maximum_ammo"].items()
            },
            items_state={
                item_database.ammo[name]: AmmoState.from_json(state)
                for name, state in value["items_state"].items()
            },
        )

    def replace_maximum_for_item(self, item: int, maximum: int) -> "AmmoConfiguration":
        return AmmoConfiguration(
            maximum_ammo={
                key: maximum if key == item else value
                for key, value in self.maximum_ammo.items()
            },
            items_state=copy.copy(self.items_state),
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

        return AmmoConfiguration(copy.copy(self.maximum_ammo), items_state)
