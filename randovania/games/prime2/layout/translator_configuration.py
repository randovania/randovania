from __future__ import annotations

import copy
import dataclasses
import functools
from enum import Enum
from typing import TYPE_CHECKING, Self

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackEnum, BitPackValue
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from collections.abc import Iterator


class LayoutTranslatorRequirement(BitPackEnum, Enum):
    long_name: str

    VIOLET = "violet"
    AMBER = "amber"
    EMERALD = "emerald"
    COBALT = "cobalt"
    RANDOM = "random"
    REMOVED = "removed"
    RANDOM_WITH_REMOVED = "random-removed"

    @classmethod
    def from_item_short_name(cls, name: str) -> LayoutTranslatorRequirement:
        for key, value in ITEM_NAMES.items():
            if value == name:
                return key
        raise KeyError(f"Unknown name: {name}")

    @property
    def item_name(self) -> str:
        if self in (LayoutTranslatorRequirement.RANDOM, LayoutTranslatorRequirement.RANDOM_WITH_REMOVED):
            raise ValueError("The random Requirement shouldn't be used for item_index")
        return ITEM_NAMES[self]


ITEM_NAMES = {
    LayoutTranslatorRequirement.VIOLET: "Violet",
    LayoutTranslatorRequirement.AMBER: "Amber",
    LayoutTranslatorRequirement.EMERALD: "Emerald",
    LayoutTranslatorRequirement.COBALT: "Cobalt",
    LayoutTranslatorRequirement.REMOVED: "Scan",
}
enum_lib.add_long_name(
    LayoutTranslatorRequirement,
    {
        LayoutTranslatorRequirement.VIOLET: "Violet Translator",
        LayoutTranslatorRequirement.AMBER: "Amber Translator",
        LayoutTranslatorRequirement.EMERALD: "Emerald Translator",
        LayoutTranslatorRequirement.COBALT: "Cobalt Translator",
        LayoutTranslatorRequirement.RANDOM: "Random",
        LayoutTranslatorRequirement.REMOVED: "Unlocked",
        LayoutTranslatorRequirement.RANDOM_WITH_REMOVED: "Random with Unlocked",
    },
)


def _get_vanilla_translator_configuration(extra_field: str) -> dict[NodeIdentifier, LayoutTranslatorRequirement]:
    from randovania.game_description import default_database

    game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)
    return {
        node.identifier: LayoutTranslatorRequirement.from_item_short_name(node.extra[extra_field])
        for node in game.region_list.iterate_nodes_of_type(ConfigurableNode)
    }


@functools.lru_cache
def _get_vanilla_actual_translator_configurations() -> dict[NodeIdentifier, LayoutTranslatorRequirement]:
    return _get_vanilla_translator_configuration("vanilla_actual")


@functools.lru_cache
def _get_vanilla_colors_translator_configurations() -> dict[NodeIdentifier, LayoutTranslatorRequirement]:
    return _get_vanilla_translator_configuration("vanilla_color")


@dataclasses.dataclass(frozen=True)
class TranslatorConfiguration(BitPackValue):
    translator_requirement: dict[NodeIdentifier, LayoutTranslatorRequirement]
    fixed_gfmc_compound: bool = True
    fixed_torvus_temple: bool = True
    fixed_great_temple: bool = True

    def bit_pack_encode(self, metadata: dict) -> Iterator[tuple[int, int]]:
        templates = [
            _get_vanilla_actual_translator_configurations(),
            _get_vanilla_colors_translator_configurations(),
            self.with_full_random().translator_requirement,
            self.translator_requirement,
        ]
        yield from bitpacking.pack_array_element(self.translator_requirement, templates)
        if templates.index(self.translator_requirement) == 3:
            for translator in self.translator_requirement.values():
                yield from translator.bit_pack_encode({})

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata: dict) -> Self:
        templates = (
            _get_vanilla_actual_translator_configurations(),
            _get_vanilla_colors_translator_configurations(),
            cls.default().with_full_random().translator_requirement,
            None,
        )
        translator_requirement = decoder.decode_element(templates)
        if translator_requirement is None:
            translator_requirement = {}
            for gate in templates[0].keys():
                translator_requirement[gate] = LayoutTranslatorRequirement.bit_pack_unpack(decoder, {})

        return cls(
            translator_requirement,
        )

    @property
    def as_json(self) -> dict:
        return {
            "translator_requirement": {key.as_string: item.value for key, item in self.translator_requirement.items()},
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        default = cls.default()

        params = copy.copy(value)

        translator_requirement = copy.copy(default.translator_requirement)
        for key, item in params.pop("translator_requirement").items():
            translator_requirement[NodeIdentifier.from_string(key)] = LayoutTranslatorRequirement(item)

        return cls(translator_requirement, **params)

    @classmethod
    def default(cls) -> Self:
        return cls(_get_vanilla_actual_translator_configurations())

    def with_vanilla_actual(self) -> Self:
        return dataclasses.replace(
            self,
            translator_requirement=_get_vanilla_actual_translator_configurations(),
        )

    def with_vanilla_colors(self) -> Self:
        return dataclasses.replace(
            self,
            translator_requirement=_get_vanilla_colors_translator_configurations(),
        )

    def with_full_random(self) -> Self:
        return dataclasses.replace(
            self,
            translator_requirement=dict.fromkeys(
                self.translator_requirement.keys(), LayoutTranslatorRequirement.RANDOM
            ),
        )

    def with_full_random_with_unlocked(self) -> Self:
        return dataclasses.replace(
            self,
            translator_requirement=dict.fromkeys(
                self.translator_requirement.keys(), LayoutTranslatorRequirement.RANDOM_WITH_REMOVED
            ),
        )

    def replace_requirement_for_gate(
        self,
        gate: NodeIdentifier,
        requirement: LayoutTranslatorRequirement,
    ) -> Self:
        """
        Replaces the requirement for the given gate. The gate must already have a requirement.
        :param gate:
        :param requirement:
        :return:
        """
        assert gate in self.translator_requirement
        result = copy.copy(self)

        new_requirement = copy.copy(self.translator_requirement)
        new_requirement[gate] = requirement

        return dataclasses.replace(result, translator_requirement=new_requirement)

    def description(self) -> str:
        translator_configurations = [
            (self.with_vanilla_actual(), "Vanilla (Actual)"),
            (self.with_vanilla_colors(), "Vanilla (Colors)"),
            (self.with_full_random(), "Random"),
            (self.with_full_random_with_unlocked(), "Random with Unlocked"),
        ]
        for translator_config, name in translator_configurations:
            if translator_config == self:
                return name

        return "Custom"
