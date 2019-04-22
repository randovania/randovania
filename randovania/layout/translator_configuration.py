import copy
import dataclasses
from enum import Enum
from typing import Dict, Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description.resources.translator_gate import TranslatorGate


class LayoutTranslatorRequirement(BitPackEnum, Enum):
    VIOLET = "violet"
    AMBER = "amber"
    EMERALD = "emerald"
    COBALT = "cobalt"
    RANDOM = "random"

    @property
    def item_index(self) -> int:
        if self == LayoutTranslatorRequirement.RANDOM:
            raise ValueError("The random Requirement shouldn't be used for item_index")
        return ITEM_INDICES[self]

    @property
    def long_name(self) -> str:
        return LONG_NAMES[self]


ITEM_INDICES = {
    LayoutTranslatorRequirement.VIOLET: 97,
    LayoutTranslatorRequirement.AMBER: 98,
    LayoutTranslatorRequirement.EMERALD: 99,
    LayoutTranslatorRequirement.COBALT: 100,
}

LONG_NAMES = {
    LayoutTranslatorRequirement.VIOLET: "Violet Translator",
    LayoutTranslatorRequirement.AMBER: "Amber Translator",
    LayoutTranslatorRequirement.EMERALD: "Emerald Translator",
    LayoutTranslatorRequirement.COBALT: "Cobalt Translator",
    LayoutTranslatorRequirement.RANDOM: "Random",
}


@dataclasses.dataclass(frozen=True)
class TranslatorConfiguration(BitPackValue):
    translator_requirement: Dict[TranslatorGate, LayoutTranslatorRequirement]
    fixed_gfmc_compound: bool = True
    fixed_torvus_temple: bool = True
    fixed_great_temple: bool = True

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        from randovania.layout import configuration_factory
        templates = [
            configuration_factory.get_vanilla_actual_translator_configurations(),
            configuration_factory.get_vanilla_colors_translator_configurations(),
            self.with_full_random().translator_requirement,
            self.translator_requirement,
        ]
        yield from bitpacking.encode_bool(self.fixed_gfmc_compound)
        yield from bitpacking.encode_bool(self.fixed_torvus_temple)
        yield from bitpacking.encode_bool(self.fixed_great_temple)

        yield from bitpacking.pack_array_element(self.translator_requirement, templates)
        if templates.index(self.translator_requirement) == 3:
            for translator in self.translator_requirement.values():
                yield from translator.bit_pack_encode({})

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "TranslatorConfiguration":
        from randovania.layout import configuration_factory
        templates = [
            configuration_factory.get_vanilla_actual_translator_configurations(),
            configuration_factory.get_vanilla_colors_translator_configurations(),
            cls.default().with_full_random().translator_requirement,
            None,
        ]

        fixed_gfmc_compound = bitpacking.decode_bool(decoder)
        fixed_torvus_temple = bitpacking.decode_bool(decoder)
        fixed_great_temple = bitpacking.decode_bool(decoder)

        translator_requirement = decoder.decode_element(templates)
        if translator_requirement is None:
            translator_requirement = {}
            for gate in templates[0].keys():
                translator_requirement[gate] = LayoutTranslatorRequirement.bit_pack_unpack(decoder, {})

        return cls(
            translator_requirement,
            fixed_gfmc_compound=fixed_gfmc_compound,
            fixed_torvus_temple=fixed_torvus_temple,
            fixed_great_temple=fixed_great_temple,
        )

    @property
    def as_json(self) -> dict:
        default = TranslatorConfiguration.default()

        return {
            "translator_requirement": {
                str(key.index): item.value
                for key, item in self.translator_requirement.items()
                if item != default.translator_requirement[key]
            },
            "fixed_gfmc_compound": self.fixed_gfmc_compound,
            "fixed_torvus_temple": self.fixed_torvus_temple,
            "fixed_great_temple": self.fixed_great_temple,
        }

    @classmethod
    def from_json(cls, value: dict) -> "TranslatorConfiguration":
        default = cls.default()

        params = copy.copy(value)

        translator_requirement = copy.copy(default.translator_requirement)
        for key, item in params.pop("translator_requirement").items():
            translator_requirement[TranslatorGate(int(key))] = LayoutTranslatorRequirement(item)

        return cls(translator_requirement, **params)

    @classmethod
    def default(cls) -> "TranslatorConfiguration":
        from randovania.layout import configuration_factory
        return cls(configuration_factory.get_vanilla_actual_translator_configurations())

    def with_vanilla_actual(self):
        from randovania.layout import configuration_factory

        result = copy.copy(self)
        return dataclasses.replace(
            result,
            translator_requirement=configuration_factory.get_vanilla_actual_translator_configurations())

    def with_vanilla_colors(self) -> "TranslatorConfiguration":
        from randovania.layout import configuration_factory

        result = copy.copy(self)
        return dataclasses.replace(
            result,
            translator_requirement=configuration_factory.get_vanilla_colors_translator_configurations())

    def with_full_random(self) -> "TranslatorConfiguration":
        result = copy.copy(self)
        return dataclasses.replace(result,
                                   translator_requirement={
                                       key: LayoutTranslatorRequirement.RANDOM
                                       for key in self.translator_requirement.keys()
                                   })

    def replace_requirement_for_gate(self, gate: TranslatorGate,
                                     requirement: LayoutTranslatorRequirement,
                                     ) -> "TranslatorConfiguration":
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
