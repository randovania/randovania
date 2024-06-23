from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Self

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackEnum, BitPackValue
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game_description import default_database
from randovania.game_description.db.dock import DockType, DockWeakness
from randovania.games.game import RandovaniaGame
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.dock import DockWeaknessDatabase


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
        DockRandoMode.DOCKS: "Doors",
        DockRandoMode.WEAKNESSES: "Types",
    },
)

enum_lib.add_per_enum_field(
    DockRandoMode,
    "description",
    {
        DockRandoMode.VANILLA: "Original door locks",
        DockRandoMode.DOCKS: "Randomize the type of each door individually",
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
    def _get_weakness_database(game: RandovaniaGame) -> DockWeaknessDatabase:
        return default_database.game_description_for(game).dock_weakness_database

    @property
    def weakness_database(self) -> DockWeaknessDatabase:
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

    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        yield from bitpacking.pack_sorted_array_elements(
            sorted(self.can_change_from),
            sorted(self.possible_change_from),
        )
        yield from bitpacking.pack_sorted_array_elements(
            sorted(self.can_change_to),
            sorted(self.possible_change_to),
        )

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> DockTypeState:
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
        yield from weakness_database.dock_rando_params[weakness_database.find_type(dock_type_name)].change_from

    @property
    def possible_change_from(self) -> Iterator[DockWeakness]:
        yield from self._possible_change_from(self.game, self.dock_type_name)

    @staticmethod
    def _possible_change_to(game: RandovaniaGame, dock_type_name: str) -> Iterator[DockWeakness]:
        weakness_database = DockTypeState._get_weakness_database(game)
        yield from weakness_database.dock_rando_params[weakness_database.find_type(dock_type_name)].change_to

    @property
    def possible_change_to(self) -> Iterator[DockWeakness]:
        yield from self._possible_change_to(self.game, self.dock_type_name)


@dataclass(frozen=True)
class DockRandoConfiguration(BitPackValue, DataclassPostInitTypeCheck):
    game: RandovaniaGame
    mode: DockRandoMode
    types_state: dict[DockType, DockTypeState]

    @staticmethod
    def _get_weakness_database(game: RandovaniaGame) -> DockWeaknessDatabase:
        return default_database.game_description_for(game).dock_weakness_database

    @property
    def weakness_database(self) -> DockWeaknessDatabase:
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

    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        reference: DockRandoConfiguration = metadata["reference"]

        yield from self.mode.bit_pack_encode(None)

        modified_types = sorted(
            dock_type
            for dock_type, type_state in self.types_state.items()
            if type_state != reference.types_state[dock_type]
        )
        yield from bitpacking.pack_sorted_array_elements(modified_types, sorted(self.weakness_database.dock_types))
        for dock_type in modified_types:
            yield from self.types_state[dock_type].bit_pack_encode({"reference": reference.types_state[dock_type]})

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> Self:
        reference: DockRandoConfiguration = metadata["reference"]

        mode = DockRandoMode.bit_pack_unpack(decoder, None)

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

    def is_enabled(self) -> bool:
        return self.mode != DockRandoMode.VANILLA

    def can_shuffle(self, dock_type: DockType) -> bool:
        return dock_type in self.weakness_database.dock_rando_params and self.types_state[dock_type].can_shuffle

    def settings_incompatible_with_multiworld(self) -> list[str]:
        danger = []
        if self.mode == DockRandoMode.DOCKS:
            danger.append(f"{self.mode.long_name}: {self.mode.description}")
        return danger

    def dangerous_settings(self) -> list[str]:
        result = []

        weakness_database = self.weakness_database

        if self.mode == DockRandoMode.WEAKNESSES:
            for dock_type, state in self.types_state.items():
                dock_rando_params = weakness_database.dock_rando_params.get(dock_type)
                if dock_rando_params is not None and dock_rando_params.locked in state.can_change_to:
                    result.append(f"{dock_rando_params.locked.name} is unsafe as a target in Door Lock Types")

        return result
