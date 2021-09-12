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
    REMOVED = "removed"
    RANDOM_WITH_REMOVED = "random-removed"

    @property
    def item_index(self) -> int:
        if self in (LayoutTranslatorRequirement.RANDOM, LayoutTranslatorRequirement.RANDOM_WITH_REMOVED):
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
    LayoutTranslatorRequirement.REMOVED: 9,
}

LONG_NAMES = {
    LayoutTranslatorRequirement.VIOLET: "Violet Translator",
    LayoutTranslatorRequirement.AMBER: "Amber Translator",
    LayoutTranslatorRequirement.EMERALD: "Emerald Translator",
    LayoutTranslatorRequirement.COBALT: "Cobalt Translator",
    LayoutTranslatorRequirement.RANDOM: "Random",
    LayoutTranslatorRequirement.REMOVED: "Unlocked",
    LayoutTranslatorRequirement.RANDOM_WITH_REMOVED: "Random with Unlocked",
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
            "translator_requirement": {
                str(key.index): item.value
                for key, item in self.translator_requirement.items()
            },
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

    def with_full_random_with_unlocked(self) -> "TranslatorConfiguration":
        result = copy.copy(self)
        return dataclasses.replace(result,
                                   translator_requirement={
                                       key: LayoutTranslatorRequirement.RANDOM_WITH_REMOVED
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

    def description(self) -> str:
        translator_configurations = [
            (self.with_vanilla_actual(), "Vanilla (Actual)"),
            (self.with_vanilla_colors(), "Vanilla (Colors)"),
            (self.with_full_random(), "Random"),
            (self.with_full_random_with_unlocked(), "Random with Unlocked")
        ]
        for translator_config, name in translator_configurations:
            if translator_config == self:
                return name

        return "Custom"
