from __future__ import annotations

import copy
import dataclasses
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


class LayoutForceFieldRequirement(BitPackEnum, Enum):
    POWER_BEAM = "power-beam"
    VOLT_DRIVER = "volt-driver"
    MISSILE = "missile"
    BATTLEHAMMER = "battlehammer"
    IMPERIALIST = "imperialist"
    JUDICATOR = "judicator"
    MAGMAUL = "magmaul"
    SHOCK_COIL = "shock-coil"
    RANDOM = "random"

    @classmethod
    def from_item_short_name(cls, name: str) -> LayoutForceFieldRequirement:
        for key, value in ITEM_NAMES.items():
            if value == name:
                return key
        raise KeyError(f"Unknown name: {name}")

    @property
    def item_name(self) -> str:
        if self == LayoutForceFieldRequirement.RANDOM:
            raise ValueError("The random Requirement shouldn't be used for item_index")
        return ITEM_NAMES[self]


ITEM_NAMES = {
    LayoutForceFieldRequirement.POWER_BEAM: "PowerBeam",
    LayoutForceFieldRequirement.VOLT_DRIVER: "VoltDriver",
    LayoutForceFieldRequirement.MISSILE: "Missile",
    LayoutForceFieldRequirement.BATTLEHAMMER: "Battlehammer",
    LayoutForceFieldRequirement.IMPERIALIST: "Imperialist",
    LayoutForceFieldRequirement.JUDICATOR: "Judicator",
    LayoutForceFieldRequirement.MAGMAUL: "Magmaul",
    LayoutForceFieldRequirement.SHOCK_COIL: "ShockCoil",
}
enum_lib.add_long_name(
    LayoutForceFieldRequirement,
    {
        LayoutForceFieldRequirement.POWER_BEAM: "Power Beam",
        LayoutForceFieldRequirement.VOLT_DRIVER: "Volt Driver",
        LayoutForceFieldRequirement.MISSILE: "Missile",
        LayoutForceFieldRequirement.BATTLEHAMMER: "Battlehammer",
        LayoutForceFieldRequirement.IMPERIALIST: "Imperialist",
        LayoutForceFieldRequirement.JUDICATOR: "Judicator",
        LayoutForceFieldRequirement.MAGMAUL: "Magmaul",
        LayoutForceFieldRequirement.SHOCK_COIL: "Shock Coil",
        LayoutForceFieldRequirement.RANDOM: "Random",
    },
)


def _get_vanilla_force_field_configuration() -> dict[NodeIdentifier, LayoutForceFieldRequirement]:
    from randovania.game_description import default_database

    game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_HUNTERS)
    return {
        node.identifier: LayoutForceFieldRequirement.from_item_short_name(node.extra["entity_type_data"]["weapon"])
        for node in game.region_list.iterate_nodes_of_type(ConfigurableNode)
    }


@dataclasses.dataclass(frozen=True)
class ForceFieldConfiguration(BitPackValue):
    force_field_requirement: dict[NodeIdentifier, LayoutForceFieldRequirement]

    def bit_pack_encode(self, metadata: dict) -> Iterator[tuple[int, int]]:
        templates = [
            _get_vanilla_force_field_configuration(),
            self.with_full_random().force_field_requirement,
            self.force_field_requirement,
        ]
        yield from bitpacking.pack_array_element(self.force_field_requirement, templates)
        if templates.index(self.force_field_requirement) == 2:
            for force_field in self.force_field_requirement.values():
                yield from force_field.bit_pack_encode({})

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata: dict) -> Self:
        templates = (
            _get_vanilla_force_field_configuration(),
            cls.default().with_full_random().force_field_requirement,
            None,
        )
        force_field_requirement = decoder.decode_element(templates)
        if force_field_requirement is None:
            force_field_requirement = {}
            for force_field in templates[0].keys():
                force_field_requirement[force_field] = LayoutForceFieldRequirement.bit_pack_unpack(decoder, {})

        return cls(
            force_field_requirement,
        )

    @property
    def as_json(self) -> dict:
        return {
            "force_field_requirement": {
                key.as_string: item.value for key, item in self.force_field_requirement.items()
            },
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        default = cls.default()

        params = copy.copy(value)

        force_field_requirement = copy.copy(default.force_field_requirement)
        for key, item in params.pop("force_field_requirement").items():
            force_field_requirement[NodeIdentifier.from_string(key)] = LayoutForceFieldRequirement(item)

        return cls(force_field_requirement, **params)

    @classmethod
    def default(cls) -> Self:
        return cls(_get_vanilla_force_field_configuration())

    def with_vanilla(self) -> Self:
        return dataclasses.replace(
            self,
            force_field_requirement=_get_vanilla_force_field_configuration(),
        )

    def with_full_random(self) -> Self:
        return dataclasses.replace(
            self,
            force_field_requirement=dict.fromkeys(
                self.force_field_requirement.keys(), LayoutForceFieldRequirement.RANDOM
            ),
        )

    def replace_requirement_for_force_field(
        self,
        force_field: NodeIdentifier,
        requirement: LayoutForceFieldRequirement,
    ) -> Self:
        """
        Replaces the requirement for the given force field. The force field must already have a requirement.
        :param force_field:
        :param requirement:
        :return:
        """
        assert force_field in self.force_field_requirement
        result = copy.copy(self)

        new_requirement = copy.copy(self.force_field_requirement)
        new_requirement[force_field] = requirement

        return dataclasses.replace(result, force_field_requirement=new_requirement)

    def description(self) -> str:
        force_field_configurations = [
            (self.with_vanilla(), "Vanilla"),
            (self.with_full_random(), "Random"),
        ]
        for force_field_config, name in force_field_configurations:
            if force_field_config == self:
                return name

        return "Custom"
