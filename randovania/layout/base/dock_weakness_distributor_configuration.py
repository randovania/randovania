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

    ORIGINAL = "original"
    INDIVIDUAL_DOCK = "individual-dock"
    WEAKNESS_TO_WEAKNESS = "weaknesses-to-weakness"
    # INDIVIDUAL_BLIND = "individual_blind"


enum_lib.add_long_name(
    DockWeaknessDistributorMode,
    {
        DockWeaknessDistributorMode.ORIGINAL: "Unmodified",
        DockWeaknessDistributorMode.INDIVIDUAL_DOCK: "Individually",
        DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS: "By Type",
        # DockWeaknessDistributorMode.INDIVIDUAL_BLIND: "Individually (Blind)",
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
        # DockWeaknessDistributorMode.INDIVIDUAL_BLIND: (
        #     "Randomizes each door, while door placement is blind to the player's equipment"
        # ),
    },
)


def _get_weakness_database(game: RandovaniaGame) -> DockTypeDatabase:
    return default_database.game_description_for(game).dock_type_database


def _distributor_enabled_types(database: DockTypeDatabase) -> list[DockType]:
    return [dock_type for dock_type in database.dock_types if dock_type.weakness_distributor is not None]


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

    # Doors-then-items implementation
    doors_first: bool = False  # TODO remove eventually to focus repo on items-then-doors alt method

    # Makes sure seeds don't feel too locked down, while also significantly reducing generation time
    locked_percentage: float = 0.2  # TODO add to GUI

    # Temporary until I'm ready to add a DockWeaknessDistributorMode for my blind-to-equipment approach
    temp_blind_mode = True

    # Not sure if this SHOULD be an alternate setting. I do think it'd help with normal INDIVIDUAL, so it's worth a try?
    # attempt_variety? balance_ something or other? It's generally about making sure all doors end up in similar
    # quantities. I dunno
    attempt_similar_quantities = True

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

        types_state = {}

        for dock_type in _distributor_enabled_types(weakness_database):
            # Raises KeyError if the preset doesn't have a configuration for the given type
            # When adding support for DWD to a type, a preset migration is required.
            types_state[dock_type] = WeaknessDistributorTypeState.from_json(
                value["types_state"][dock_type.short_name], game, dock_type.short_name
            )

        return cls(
            types_state=types_state,
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
        yield from bitpacking.pack_sorted_array_elements(
            modified_types, sorted(_distributor_enabled_types(weakness_database))
        )
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
            decoder, sorted(_distributor_enabled_types(_get_weakness_database(game)))
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
        return any(type_state.mode == mode for type_state in self.types_state.values())

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
                distributor_config = dock_type.weakness_distributor
                if distributor_config is not None:
                    for weakness in sorted(state.can_change_to):
                        if weakness.unsafe_target_in_distributor_wtw:
                            result.append(
                                f"{distributor_config.ui_label}: {weakness.name} is unsafe as "
                                f"a target in mode {state.mode.long_name}"
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
