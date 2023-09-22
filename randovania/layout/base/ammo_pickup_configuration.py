from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING

from randovania.bitpacking import bitpacking
from randovania.game_description import default_database
from randovania.layout.base.ammo_pickup_state import AmmoPickupState

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.pickup.ammo_pickup import AmmoPickupDefinition
    from randovania.games.game import RandovaniaGame


@dataclass(frozen=True)
class AmmoPickupConfiguration(bitpacking.BitPackValue):
    pickups_state: dict[AmmoPickupDefinition, AmmoPickupState]

    def __post_init__(self):
        for ammo, state in self.pickups_state.items():
            state.check_consistency(ammo)

    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        default: AmmoPickupConfiguration = metadata["reference"]

        assert list(self.pickups_state.keys()) == list(default.pickups_state.keys())

        for ammo, this in self.pickups_state.items():
            reference = default.pickups_state[ammo]
            is_different = this != reference
            yield from bitpacking.encode_bool(is_different)
            if is_different:
                yield from this.bit_pack_encode(
                    {
                        "ammo": ammo,
                    }
                )

    @classmethod
    def bit_pack_unpack(cls, decoder: bitpacking.BitPackDecoder, metadata):
        default: AmmoPickupConfiguration = metadata["reference"]

        pickups_state = {}
        for ammo, default_state in default.pickups_state.items():
            is_different = bitpacking.decode_bool(decoder)
            if is_different:
                pickups_state[ammo] = AmmoPickupState.bit_pack_unpack(decoder, {"ammo": ammo})
            else:
                pickups_state[ammo] = default_state

        return cls(pickups_state)

    @property
    def as_json(self) -> dict:
        return {
            "pickups_state": {ammo.name: state.as_json for ammo, state in self.pickups_state.items()},
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame) -> AmmoPickupConfiguration:
        pickup_database = default_database.pickup_database_for_game(game)
        return cls(
            pickups_state={
                pickup_database.ammo_pickups[name]: AmmoPickupState.from_json(state)
                for name, state in value["pickups_state"].items()
            },
        )

    def replace_state_for_ammo(self, ammo: AmmoPickupDefinition, state: AmmoPickupState) -> AmmoPickupConfiguration:
        return self.replace_states({ammo: state})

    def replace_states(self, new_states: dict[AmmoPickupDefinition, AmmoPickupState]) -> AmmoPickupConfiguration:
        """
        Creates a copy of this AmmoConfiguration where the state of all given pickups are replaced by the given
        states.
        :param new_states:
        :return:
        """
        pickups_state = copy.copy(self.pickups_state)

        for pickup, state in new_states.items():
            pickups_state[pickup] = state

        return AmmoPickupConfiguration(pickups_state)
