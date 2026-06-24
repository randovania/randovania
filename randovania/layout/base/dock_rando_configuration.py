from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Self

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackEnum, BitPackValue
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.db.dock import DockType, DockWeakness
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.dock import DockTypeDatabase


class DockRandoMode(BitPackEnum, Enum):
    long_name: str
    description: str

    VANILLA = "vanilla"
    DOCKS = "docks"
    WEAKNESSES = "weaknesses"


enum_lib.add_long_name(
    DockRandoMode,
    {
        DockRandoMode.VANILLA: "Vanilla",
        DockRandoMode.DOCKS: "Individual Doors",
        DockRandoMode.WEAKNESSES: "Door Types",
    },
)

enum_lib.add_per_enum_field(
    DockRandoMode,
    "description",
    {
        DockRandoMode.VANILLA: "Original door locks",
        DockRandoMode.DOCKS: "Randomizes each door individually",
        DockRandoMode.WEAKNESSES: "Randomizes all doors by type, turning all of one type into another",
    },
)


@dataclass(frozen=True)
class DockTypeState(BitPackValue, DataclassPostInitTypeCheck):
    game: RandovaniaGame
    dock_type_name: str
    can_change_from: set[DockWeakness]
    can_change_to: set[DockWeakness]

    @staticmethod
    def _get_weakness_database(game: RandovaniaGame) -> DockTypeDatabase:
        return default_database.game_description_for(game).dock_type_database

    @property
    def weakness_database(self) -> DockTypeDatabase:
        return self._get_weakness_database(self.game)

    @property
    def dock_type(self) -> DockType:
        return self.weakness_database.find_type(self.dock_type_name)

    @property
    def can_shuffle(self) -> bool:
        return len(self.can_change_from) > 0

    @property
    def as_json(self) -> dict:
        return {
            "can_change_from": sorted(weakness.name for weakness in self.can_change_from),
            "can_change_to": sorted(weakness.name for weakness in self.can_change_to),
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame, dock_type_name: str) -> DockTypeState:
        weakness_database = cls._get_weakness_database(game)
        return cls(
            game=game,
            dock_type_name=dock_type_name,
            can_change_from={
                weakness_database.get_by_weakness(dock_type_name, weakness) for weakness in value["can_change_from"]
            },
            can_change_to={
                weakness_database.get_by_weakness(dock_type_name, weakness) for weakness in value["can_change_to"]
            },
        )

    def bit_pack_encode(self, metadata: dict) -> Iterator[tuple[int, int]]:
        yield from bitpacking.pack_sorted_array_elements(
            sorted(self.can_change_from),
            sorted(self.possible_change_from),
        )
        yield from bitpacking.pack_sorted_array_elements(
            sorted(self.can_change_to),
            sorted(self.possible_change_to),
        )

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata: dict) -> DockTypeState:
        reference: DockTypeState = metadata["reference"]
        ref_change_from = sorted(cls._possible_change_from(reference.game, reference.dock_type_name))
        ref_change_to = sorted(cls._possible_change_to(reference.game, reference.dock_type_name))

        return cls(
            game=reference.game,
            dock_type_name=reference.dock_type_name,
            can_change_from=set(bitpacking.decode_sorted_array_elements(decoder, ref_change_from)),
            can_change_to=set(bitpacking.decode_sorted_array_elements(decoder, ref_change_to)),
        )

    @staticmethod
    def _possible_change_from(game: RandovaniaGame, dock_type_name: str) -> Iterator[DockWeakness]:
        weakness_database = DockTypeState._get_weakness_database(game)
        yield from weakness_database.find_type(dock_type_name).get_weakness_distributor().change_from

    @property
    def possible_change_from(self) -> Iterator[DockWeakness]:
        yield from self._possible_change_from(self.game, self.dock_type_name)

    @staticmethod
    def _possible_change_to(game: RandovaniaGame, dock_type_name: str) -> Iterator[DockWeakness]:
        weakness_database = DockTypeState._get_weakness_database(game)
        yield from weakness_database.find_type(dock_type_name).get_weakness_distributor().change_to

    @property
    def possible_change_to(self) -> Iterator[DockWeakness]:
        yield from self._possible_change_to(self.game, self.dock_type_name)


@dataclass(frozen=True)
class DockRandoConfiguration(BitPackValue, DataclassPostInitTypeCheck):
    game: RandovaniaGame
    mode: DockRandoMode
    types_state: dict[DockType, DockTypeState]

    @staticmethod
    def _get_weakness_database(game: RandovaniaGame) -> DockTypeDatabase:
        return default_database.game_description_for(game).dock_type_database

    @property
    def weakness_database(self) -> DockTypeDatabase:
        return self._get_weakness_database(self.game)

    @property
    def as_json(self) -> dict:
        return {
            "mode": self.mode.value,
            "types_state": {
                dock_type.short_name: type_state.as_json for dock_type, type_state in self.types_state.items()
            },
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame) -> Self:
        weakness_database = cls._get_weakness_database(game)
        return cls(
            game=game,
            mode=DockRandoMode(value["mode"]),
            types_state={
                weakness_database.find_type(dock_type): DockTypeState.from_json(type_state, game, dock_type)
                for dock_type, type_state in value["types_state"].items()
            },
        )

    def bit_pack_encode(self, metadata: dict) -> Iterator[tuple[int, int]]:
        reference: DockRandoConfiguration = metadata["reference"]

        yield from self.mode.bit_pack_encode({})

        modified_types = sorted(
            dock_type
            for dock_type, type_state in self.types_state.items()
            if type_state != reference.types_state[dock_type]
        )
        yield from bitpacking.pack_sorted_array_elements(modified_types, sorted(self.weakness_database.dock_types))
        for dock_type in modified_types:
            yield from self.types_state[dock_type].bit_pack_encode({"reference": reference.types_state[dock_type]})

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata: dict) -> Self:
        reference: DockRandoConfiguration = metadata["reference"]

        mode = DockRandoMode.bit_pack_unpack(decoder, {})

        modified_types = bitpacking.decode_sorted_array_elements(
            decoder, sorted(reference.weakness_database.dock_types)
        )
        types_state = copy.copy(reference.types_state)
        for dock_type in modified_types:
            types_state[dock_type] = DockTypeState.bit_pack_unpack(
                decoder, {"reference": reference.types_state[dock_type]}
            )

        return cls(
            game=reference.game,
            mode=mode,
            types_state=types_state,
        )

    def is_enabled_for(self, dock_type: DockType) -> bool:
        # FIXME: this really should be per type :)
        return self.mode != DockRandoMode.VANILLA

    def get_mode_for(self, dock_type: DockType) -> DockRandoMode:
        # FIXME: this really should be per type :)
        return self.mode

    def is_enabled_for_any_type(self) -> bool:
        return any(self.is_enabled_for(dock_type) for dock_type in self.types_state)

    def can_shuffle(self, dock_type: DockType) -> bool:
        return (
            self.is_enabled_for(dock_type)
            and dock_type.weakness_distributor is not None
            and self.types_state[dock_type].can_shuffle
        )

    def settings_incompatible_with_multiworld(self) -> list[str]:
        danger = []
        if self.mode == DockRandoMode.DOCKS:
            danger.append(f"{self.mode.long_name}: {self.mode.description}")
        return danger

    def dangerous_settings(self) -> list[str]:
        result = []

        if self.mode == DockRandoMode.WEAKNESSES:
            for dock_type, state in self.types_state.items():
                weakness_distributor = dock_type.weakness_distributor
                if weakness_distributor is not None and weakness_distributor.locked in state.can_change_to:
                    result.append(f"{weakness_distributor.locked.name} is unsafe as a target in Door Lock Types")

        return result

    def settings_incompatible_with_map_tracker(self) -> list[str]:
        result = []

        if self.is_enabled_for_any_type():
            result.append("Door Lock Rando")

        return result
