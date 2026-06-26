from __future__ import annotations

import copy
import dataclasses
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


class DockWeaknessDistributorMode(BitPackEnum, Enum):
    long_name: str
    description: str

    ORIGINAL = "vanilla"
    INDIVIDUAL_DOCK = "docks"
    WEAKNESS_TO_WEAKNESS = "weaknesses"


enum_lib.add_long_name(
    DockWeaknessDistributorMode,
    {
        DockWeaknessDistributorMode.ORIGINAL: "Unmodified",
        DockWeaknessDistributorMode.INDIVIDUAL_DOCK: "Individually",
        DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS: "By Type",
    },
)

enum_lib.add_per_enum_field(
    DockWeaknessDistributorMode,
    "description",
    {
        # FIXME: these are Door specific
        DockWeaknessDistributorMode.ORIGINAL: "Original door locks",
        DockWeaknessDistributorMode.INDIVIDUAL_DOCK: "Randomizes each door individually",
        DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS: (
            "Randomizes all doors by type, turning all of one type into another"
        ),
    },
)


def _get_weakness_database(game: RandovaniaGame) -> DockTypeDatabase:
    return default_database.game_description_for(game).dock_type_database


@dataclass(frozen=True)
class WeaknessDistributorTypeState(BitPackValue, DataclassPostInitTypeCheck):
    """Controls how any given Dock is randomized in DockWeaknessDistributor."""

    dock_type_name: str
    mode: DockWeaknessDistributorMode
    can_change_from: set[DockWeakness]
    can_change_to: set[DockWeakness]

    @property
    def can_shuffle(self) -> bool:
        return len(self.can_change_from) > 0

    @property
    def as_json(self) -> dict:
        return {
            "mode": self.mode.value,
            "can_change_from": sorted(weakness.name for weakness in self.can_change_from),
            "can_change_to": sorted(weakness.name for weakness in self.can_change_to),
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame, dock_type_name: str) -> WeaknessDistributorTypeState:
        weakness_database = _get_weakness_database(game)
        return cls(
            dock_type_name=dock_type_name,
            mode=DockWeaknessDistributorMode(value["mode"]),
            can_change_from={
                weakness_database.get_by_weakness(dock_type_name, weakness) for weakness in value["can_change_from"]
            },
            can_change_to={
                weakness_database.get_by_weakness(dock_type_name, weakness) for weakness in value["can_change_to"]
            },
        )

    def bit_pack_encode(self, metadata: dict) -> Iterator[tuple[int, int]]:
        game: RandovaniaGame = metadata["game"]
        yield from self.mode.bit_pack_encode({})
        yield from bitpacking.pack_sorted_array_elements(
            sorted(self.can_change_from),
            sorted(self.possible_change_from(game)),
        )
        yield from bitpacking.pack_sorted_array_elements(
            sorted(self.can_change_to),
            sorted(self.possible_change_to(game)),
        )

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata: dict) -> WeaknessDistributorTypeState:
        game: RandovaniaGame = metadata["game"]
        reference: WeaknessDistributorTypeState = metadata["reference"]
        ref_change_from = sorted(cls._possible_change_from(game, reference.dock_type_name))
        ref_change_to = sorted(cls._possible_change_to(game, reference.dock_type_name))

        mode = DockWeaknessDistributorMode.bit_pack_unpack(decoder, {})

        return cls(
            dock_type_name=reference.dock_type_name,
            mode=mode,
            can_change_from=set(bitpacking.decode_sorted_array_elements(decoder, ref_change_from)),
            can_change_to=set(bitpacking.decode_sorted_array_elements(decoder, ref_change_to)),
        )

    @staticmethod
    def _possible_change_from(game: RandovaniaGame, dock_type_name: str) -> Iterator[DockWeakness]:
        weakness_database = _get_weakness_database(game)
        yield from weakness_database.find_type(dock_type_name).get_weakness_distributor().change_from

    def possible_change_from(self, game: RandovaniaGame) -> Iterator[DockWeakness]:
        yield from self._possible_change_from(game, self.dock_type_name)

    @staticmethod
    def _possible_change_to(game: RandovaniaGame, dock_type_name: str) -> Iterator[DockWeakness]:
        weakness_database = _get_weakness_database(game)
        yield from weakness_database.find_type(dock_type_name).get_weakness_distributor().change_to

    def possible_change_to(self, game: RandovaniaGame) -> Iterator[DockWeakness]:
        yield from self._possible_change_to(game, self.dock_type_name)


@dataclass(frozen=True)
class DockWeaknessDistributorConfiguration(BitPackValue, DataclassPostInitTypeCheck):
    types_state: dict[DockType, WeaknessDistributorTypeState]

    @property
    def as_json(self) -> dict:
        return {
            "types_state": {
                dock_type.short_name: type_state.as_json for dock_type, type_state in self.types_state.items()
            },
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame) -> Self:
        weakness_database = _get_weakness_database(game)
        return cls(
            types_state={
                weakness_database.find_type(dock_type): WeaknessDistributorTypeState.from_json(
                    type_state, game, dock_type
                )
                for dock_type, type_state in value["types_state"].items()
            },
        )

    def bit_pack_encode(self, metadata: dict) -> Iterator[tuple[int, int]]:
        game: RandovaniaGame = metadata["parent_metadata"]["game"]
        reference: DockWeaknessDistributorConfiguration = metadata["reference"]

        weakness_database = _get_weakness_database(game)

        modified_types = sorted(
            dock_type
            for dock_type, type_state in self.types_state.items()
            if type_state != reference.types_state[dock_type]
        )
        yield from bitpacking.pack_sorted_array_elements(modified_types, sorted(weakness_database.dock_types))
        for dock_type in modified_types:
            yield from self.types_state[dock_type].bit_pack_encode(
                {
                    "reference": reference.types_state[dock_type],
                    "game": game,
                    "parent_object": self,
                    "parent_metadata": metadata,
                }
            )

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata: dict) -> Self:
        game: RandovaniaGame = metadata["parent_metadata"]["game"]
        reference: DockWeaknessDistributorConfiguration = metadata["reference"]

        modified_types = bitpacking.decode_sorted_array_elements(
            decoder, sorted(_get_weakness_database(game).dock_types)
        )
        types_state = copy.copy(reference.types_state)
        for dock_type in modified_types:
            types_state[dock_type] = WeaknessDistributorTypeState.bit_pack_unpack(
                decoder,
                {
                    "game": game,
                    "reference": reference.types_state[dock_type],
                },
            )

        return cls(
            types_state=types_state,
        )

    def is_enabled_for(self, dock_type: DockType) -> bool:
        """
        If the given dock_type has any mode enabled. Safe for any kind of dock type.
        """
        return (
            dock_type in self.types_state and self.types_state[dock_type].mode != DockWeaknessDistributorMode.ORIGINAL
        )

    def is_any_type_mode(self, mode: DockWeaknessDistributorMode) -> bool:
        """
        True, if at least one type is configured as the given mode.
        """
        return any(type_state == mode for type_state in self.types_state.values())

    def get_mode_for(self, dock_type: DockType) -> DockWeaknessDistributorMode:
        """
        Gets what mode is configured for the given type.
        Not safe to be called with dock types that doesn't support weakness distribution.
        """
        return self.types_state[dock_type].mode

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

        for dock_type in self.types_state:
            mode = self.get_mode_for(dock_type)
            if mode == DockWeaknessDistributorMode.INDIVIDUAL_DOCK:
                danger.append(f"{dock_type.get_weakness_distributor().ui_label} - {mode.long_name}: {mode.description}")
        return danger

    def dangerous_settings(self) -> list[str]:
        result = []

        for dock_type, state in self.types_state.items():
            if state.mode == DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS:
                weakness_distributor = dock_type.weakness_distributor
                if weakness_distributor is not None and weakness_distributor.locked in state.can_change_to:
                    result.append(
                        f"{weakness_distributor.locked.name} is unsafe as a target in mode {state.mode.long_name}"
                    )

        return result

    def settings_incompatible_with_map_tracker(self) -> list[str]:
        result = []

        if self.is_enabled_for_any_type():
            result.append("Door Lock Rando")

        return result

    def replace_state(self, dock_type: DockType, state: WeaknessDistributorTypeState) -> Self:
        types_state = copy.copy(self.types_state)
        types_state[dock_type] = state
        return dataclasses.replace(
            self,
            types_state=types_state,
        )
