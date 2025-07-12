from __future__ import annotations

import dataclasses
import typing
import uuid as uuid_module
from typing import TYPE_CHECKING, Self

from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.interface_common.preset_manager import PresetManager


@dataclasses.dataclass(frozen=True)
class Preset[BaseConfigurationT: BaseConfiguration](BitPackValue):
    name: str
    uuid: uuid_module.UUID
    description: str
    game: RandovaniaGame
    configuration: BaseConfigurationT

    @property
    def as_json(self) -> dict:
        return {
            "name": self.name,
            "uuid": str(self.uuid),
            "description": self.description,
            "game": self.game.value,
            "configuration": self.configuration.as_json,
        }

    @classmethod
    def from_json_dict(cls, value: dict) -> Self:
        game = RandovaniaGame(value["game"])
        return cls(
            name=value["name"],
            uuid=uuid_module.UUID(value["uuid"]),
            description=value["description"],
            game=game,
            configuration=typing.cast("type[BaseConfigurationT]", game.data.layout.configuration).from_json(
                value["configuration"]
            ),
        )

    def dangerous_settings(self) -> list[str]:
        return self.configuration.dangerous_settings()

    def settings_incompatible_with_multiworld(self) -> list[str]:
        return self.configuration.settings_incompatible_with_multiworld()

    def is_same_configuration(self, other: Preset) -> bool:
        return self.configuration == other.configuration

    def bit_pack_encode(self, metadata: dict) -> Iterator[tuple[int, int]]:
        manager: PresetManager = metadata["manager"]

        reference = manager.reference_preset_for_game(self.game).get_preset()
        yield from self.configuration.bit_pack_encode({"reference": reference.configuration})

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata: dict) -> Self:
        manager: PresetManager = metadata["manager"]
        game: RandovaniaGame = metadata["game"]

        reference = typing.cast("Preset[BaseConfigurationT]", manager.reference_preset_for_game(game).get_preset())

        return cls(
            name=f"{game.long_name} Custom",
            description="A customized preset.",
            uuid=uuid_module.uuid4(),
            game=reference.game,
            configuration=reference.configuration.bit_pack_unpack(decoder, {"reference": reference.configuration}),
        )

    def fork(self) -> Self:
        return dataclasses.replace(
            self,
            name=f"{self.name} Copy",
            description=f"A copy version of {self.name}.",
            uuid=uuid_module.uuid4(),
        )
