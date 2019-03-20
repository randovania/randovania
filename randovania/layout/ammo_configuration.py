import copy
from dataclasses import dataclass
from typing import Dict, Iterator, Tuple, List

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_database import ItemDatabase
from randovania.layout.ammo_state import AmmoState


@dataclass(frozen=True)
class AmmoConfiguration(BitPackValue):
    maximum_ammo: Dict[int, int]
    items_state: Dict[Ammo, AmmoState]

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        default = AmmoConfiguration.default()

        for key, value in self.maximum_ammo.items():
            yield int(value != default.maximum_ammo[key]), 2

        for key, value in self.maximum_ammo.items():
            if value != default.maximum_ammo[key]:
                yield value, 256

        result: List[Tuple[int, Ammo, AmmoState]] = []
        for i, (item, state) in enumerate(self.items_state.items()):
            if state != default.items_state[item]:
                result.append((i, item, state))

        yield len(result), len(self.items_state)
        for index, _, _ in result:
            yield index, len(self.items_state)

        for index, _, state in result:
            yield from state.bit_pack_encode()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        from randovania.game_description import default_database
        item_database = default_database.default_prime2_item_database()

        default = cls.default()
        has_value = {
            item_key: bool(decoder.decode_single(2))
            for item_key in default.maximum_ammo.keys()
        }

        maximum_ammo = {
            item_key: decoder.decode_single(256) if has_value[item_key] else default.maximum_ammo[item_key]
            for item_key, default_value in default.maximum_ammo.items()
        }

        num_items = decoder.decode_single(len(default.items_state))
        indices_with_custom = {
            decoder.decode_single(len(default.items_state))
            for _ in range(num_items)
        }

        items_state = {}
        for index, item in enumerate(item_database.ammo.values()):
            if index in indices_with_custom:
                items_state[item] = AmmoState.bit_pack_unpack(decoder)
            else:
                items_state[item] = default.items_state[item]

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

    @classmethod
    def default(cls):
        from randovania.layout import configuration_factory
        return configuration_factory.get_default_ammo_configurations()
