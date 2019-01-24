from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Dict

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description.resources import SimpleResourceInfo, ResourceDatabase


class StartingResourcesConfiguration(BitPackEnum, Enum):
    VANILLA_ITEM_LOSS_ENABLED = "vanilla-item-loss-enabled"
    VANILLA_ITEM_LOSS_DISABLED = "vanilla-item-loss-disabled"
    CUSTOM = "custom"


@dataclass(frozen=True)
class StartingResources(BitPackValue):
    configuration: StartingResourcesConfiguration
    _database: ResourceDatabase
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
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        configuration = StartingResourcesConfiguration.bit_pack_unpack(decoder)

        if configuration != StartingResourcesConfiguration.CUSTOM:
            return cls.from_non_custom_configuration(configuration)

        # TODO: unpack custom format
        return NotImplemented()

    @classmethod
    def from_non_custom_configuration(cls, configuration: StartingResourcesConfiguration):
        if configuration == StartingResourcesConfiguration.CUSTOM:
            raise ValueError("from_non_custom_configuration shouldn't receive CUSTOM configuration")

        return NotImplemented()
