import dataclasses
import uuid
from typing import Optional, List, Iterator, Tuple

from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class Preset(BitPackValue):
    name: str
    uuid: uuid.UUID
    description: str
    base_preset_uuid: Optional[uuid.UUID]
    game: RandovaniaGame
    configuration: BaseConfiguration

    @property
    def as_json(self) -> dict:
        return {
            "name": self.name,
            "uuid": str(self.uuid),
            "description": self.description,
            "base_preset_uuid": str(self.base_preset_uuid) if self.base_preset_uuid is not None else None,
            "game": self.game.value,
            "configuration": self.configuration.as_json,
        }

    @classmethod
    def from_json_dict(cls, value) -> "Preset":
        game = RandovaniaGame(value["game"])
        return Preset(
            name=value["name"],
            uuid=uuid.UUID(value["uuid"]),
            description=value["description"],
            base_preset_uuid=uuid.UUID(value["base_preset_uuid"]) if value["base_preset_uuid"] is not None else None,
            game=game,
            configuration=game.data.layout.configuration.from_json(value["configuration"]),
        )

    def dangerous_settings(self) -> List[str]:
        return self.configuration.dangerous_settings()

    def is_same_configuration(self, other: "Preset") -> bool:
        return self.configuration == other.configuration

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        from randovania.interface_common.preset_manager import PresetManager
        manager: PresetManager = metadata["manager"]

        reference = manager.reference_preset_for_game(self.game).get_preset()
        yield from self.configuration.bit_pack_encode({"reference": reference.configuration})

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "Preset":
        from randovania.interface_common.preset_manager import PresetManager
        manager: PresetManager = metadata["manager"]
        game: RandovaniaGame = metadata["game"]

        reference = manager.reference_preset_for_game(game).get_preset()

        return Preset(
            name="{} Custom".format(game.long_name),
            description="A customized preset.",
            uuid=uuid.uuid4(),
            base_preset_uuid=reference.uuid,
            game=reference.game,
            configuration=reference.configuration.bit_pack_unpack(decoder, {"reference": reference.configuration}),
        )

    def fork(self) -> "Preset":
        return dataclasses.replace(self, name=f"{self.name} Copy",
                                   description=f"A copy version of {self.name}.",
                                   uuid=uuid.uuid4(), base_preset_uuid=self.uuid)
