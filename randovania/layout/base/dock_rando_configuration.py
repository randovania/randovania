import copy
from dataclasses import dataclass
from enum import Enum
from typing import Iterator

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackEnum, BitPackValue
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game_description import default_database
from randovania.game_description.world.dock import DockType, DockWeakness, DockWeaknessDatabase
from randovania.games.game import RandovaniaGame


class DockRandoMode(BitPackEnum, Enum):
    VANILLA = "vanilla"
    TWO_WAY = "two-way"
    ONE_WAY = "one-way"

    @property
    def long_name(self) -> str:
        if self == DockRandoMode.VANILLA:
            return "Vanilla"
        if self == DockRandoMode.TWO_WAY:
            return "Two-way"
        if self == DockRandoMode.ONE_WAY:
            return "One-way"
        raise ValueError(f"Unknown value: {self}")

    @property
    def description(self) -> str:
        if self == DockRandoMode.VANILLA:
            return "Original door locks."
        if self == DockRandoMode.TWO_WAY:
            return "Random door locks; same lock on both sides."
        if self == DockRandoMode.ONE_WAY:
            return "Random door locks; each side is separate."
        raise ValueError(f"Unknown value: {self}")


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
    def from_json(cls, value: dict, game: RandovaniaGame, dock_type_name: str) -> "DockTypeState":
        weakness_database = cls._get_weakness_database(game)
        return cls(
            game=game,
            dock_type_name=dock_type_name,
            can_change_from={
                weakness_database.get_by_weakness(dock_type_name, weakness)
                for weakness in value["can_change_from"]
            },
            can_change_to={
                weakness_database.get_by_weakness(dock_type_name, weakness)
                for weakness in value["can_change_to"]
            },
        )

    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        yield from bitpacking.pack_sorted_array_elements(
            sorted(self.can_change_from), sorted(self.possible_change_from),
        )
        yield from bitpacking.pack_sorted_array_elements(
            sorted(self.can_change_to), sorted(self.possible_change_to),
        )

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "DockTypeState":
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

    @classmethod
    def default_state(cls, game: RandovaniaGame, dock_type_name: str):
        return cls(
            game=game,
            dock_type_name=dock_type_name,
            can_change_from=set(cls._possible_change_from(game, dock_type_name)),
            can_change_to=set(cls._possible_change_to(game, dock_type_name)),
        )


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
                dock_type.short_name: type_state.as_json
                for dock_type, type_state in self.types_state.items()
            }
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame) -> "DockRandoConfiguration":
        weakness_database = cls._get_weakness_database(game)
        return cls(
            game=game,
            mode=DockRandoMode(value["mode"]),
            types_state={
                weakness_database.find_type(dock_type): DockTypeState.from_json(type_state, game, dock_type)
                for dock_type, type_state in value["types_state"].items()
            }
        )

    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        reference: DockRandoConfiguration = metadata["reference"]

        yield from self.mode.bit_pack_encode(None)

        modified_types = sorted(
            dock_type for dock_type, type_state in self.types_state.items()
            if type_state != reference.types_state[dock_type]
        )
        yield from bitpacking.pack_sorted_array_elements(modified_types, sorted(self.weakness_database.dock_types))
        for dock_type in modified_types:
            yield from self.types_state[dock_type].bit_pack_encode({"reference": reference.types_state[dock_type]})

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "DockRandoConfiguration":
        reference: DockRandoConfiguration = metadata["reference"]

        mode = DockRandoMode.bit_pack_unpack(decoder, None)

        modified_types = bitpacking.decode_sorted_array_elements(decoder,
                                                                 sorted(reference.weakness_database.dock_types))
        types_state = copy.copy(reference.types_state)
        for dock_type in modified_types:
            types_state[dock_type] = DockTypeState.bit_pack_unpack(decoder,
                                                                   {"reference": reference.types_state[dock_type]})

        return cls(
            game=reference.game,
            mode=mode,
            types_state=types_state,
        )

    def settings_incompatible_with_multiworld(self) -> list[str]:
        danger = []
        if self.mode != DockRandoMode.VANILLA:
            danger.append("Door Lock randomizer")
        return danger
