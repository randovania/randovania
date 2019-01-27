from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Dict

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description import default_database
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import SimpleResourceInfo

_vanilla_item_loss_enabled_items = {
    0: 1,  # Power Beam
    8: 1,  # Combat Visor
    9: 1,  # Scan Visor
    12: 1,  # Varia Suit
    15: 1,  # Morph Ball
    22: 1,  # Charge Beam
}

_vanilla_item_loss_disabled_items: Dict[int, int] = {
    0: 1,  # Power Beam
    8: 1,  # Combat Visor
    9: 1,  # Scan Visor
    12: 1,  # Varia Suit
    15: 1,  # Morph Ball
    16: 1,  # Boost Ball
    17: 1,  # Spider Ball
    18: 1,  # Morph Ball Bomb
    22: 1,  # Charge Beam
    24: 1,  # Space Jump Boots
    44: 5,  # Missile
}


class StartingResourcesConfiguration(BitPackEnum, Enum):
    VANILLA_ITEM_LOSS_ENABLED = "vanilla-item-loss-enabled"
    VANILLA_ITEM_LOSS_DISABLED = "vanilla-item-loss-disabled"
    CUSTOM = "custom"


_reference_starting_equipment = {
    StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED: _vanilla_item_loss_enabled_items,
    StartingResourcesConfiguration.VANILLA_ITEM_LOSS_DISABLED: _vanilla_item_loss_disabled_items,
}


@dataclass(frozen=True)
class StartingResources(BitPackValue):
    """
    This class contains configuration for what items you chose to start the game with, no random involved.
    """
    configuration: StartingResourcesConfiguration
    _resources: Dict[SimpleResourceInfo, int]

    def bit_pack_format(self) -> Iterator[int]:
        yield from self.configuration.bit_pack_format()

        if self.configuration != StartingResourcesConfiguration.CUSTOM:
            return

        # TODO: pack custom format
        yield from []

    def bit_pack_arguments(self) -> Iterator[int]:
        yield from self.configuration.bit_pack_arguments()

        if self.configuration != StartingResourcesConfiguration.CUSTOM:
            return

        # TODO: pack custom format
        yield from []

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "StartingResources":
        configuration = StartingResourcesConfiguration.bit_pack_unpack(decoder)

        if configuration != StartingResourcesConfiguration.CUSTOM:
            return cls.from_non_custom_configuration(configuration)

        # TODO: unpack custom format
        if not decoder:
            items = {}
            return cls(configuration, items)

        raise NotImplementedError()

    @classmethod
    def from_non_custom_configuration(cls, configuration: StartingResourcesConfiguration) -> "StartingResources":
        if configuration == StartingResourcesConfiguration.CUSTOM:
            raise ValueError("from_non_custom_configuration shouldn't receive CUSTOM configuration")

        items = _reference_starting_equipment[configuration]
        database = default_database.default_prime2_resource_database()

        return cls(
            configuration,
            {
                database.get_by_type_and_index(ResourceType.ITEM, index): quantity
                for index, quantity in items.items()
            })

    @classmethod
    def default(cls) -> "StartingResources":
        return cls.from_non_custom_configuration(StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED)

    @property
    def as_json(self):
        return ""

    @classmethod
    def from_json(cls, value) -> "StartingResources":
        # TODO: add an actual implementation
        return cls.default()
