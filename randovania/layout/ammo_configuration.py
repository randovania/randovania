import copy
from dataclasses import dataclass
from typing import Dict, Iterator

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_database import ItemDatabase
from randovania.layout.ammo_state import AmmoState


@dataclass(frozen=True)
class AmmoConfiguration(BitPackValue):
    maximum_ammo: Dict[int, int]
    items_state: Dict[Ammo, AmmoState]

    def bit_pack_format(self) -> Iterator[int]:
        for _ in self.maximum_ammo.values():
            yield 256
        for value in self.items_state.values():
            yield from value.bit_pack_format()

    def bit_pack_arguments(self) -> Iterator[int]:
        for value in self.maximum_ammo.values():
            yield value
        for value in self.items_state.values():
            yield from value.bit_pack_arguments()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        from randovania.game_description import default_database
        item_database = default_database.default_prime2_item_database()

        maximum_ammo = {
            44: 0,
            43: 0,
            45: 0,
            46: 0
        }
        for item_key in maximum_ammo.keys():
            maximum_ammo[item_key] = decoder.decode(256)[0]

        items_state = {}
        for item in item_database.ammo.values():
            items_state[item] = AmmoState.bit_pack_unpack(decoder)

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
    def from_json(cls, value: dict, item_database: ItemDatabase) -> "AmmoConfiguration":
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
        return AmmoConfiguration(
            maximum_ammo=copy.copy(self.maximum_ammo),
            items_state={
                key: state if key == ammo else value
                for key, value in self.items_state.items()
            }
        )
