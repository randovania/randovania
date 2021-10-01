import dataclasses
import json
import uuid
from typing import Optional, List, Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.games.game import RandovaniaGame
from randovania.layout.game_to_class import AnyGameConfiguration, GAME_TO_CONFIGURATION


def _dictionary_byte_hash(data: dict) -> int:
    return bitpacking.single_byte_hash(json.dumps(data, separators=(',', ':')).encode("UTF-8"))


@dataclasses.dataclass(frozen=True)
class Preset(BitPackValue):
    name: str
    uuid: uuid.UUID
    description: str
    base_preset_uuid: Optional[uuid.UUID]
    game: RandovaniaGame
    configuration: AnyGameConfiguration

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
            configuration=GAME_TO_CONFIGURATION[game].from_json(value["configuration"]),
        )

    def dangerous_settings(self) -> List[str]:
        return self.configuration.dangerous_settings()

    def is_same_configuration(self, other: "Preset") -> bool:
        return self.configuration == other.configuration

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        from randovania.interface_common.preset_manager import PresetManager
        manager: PresetManager = metadata["manager"]

        # Is this a custom preset?
        is_custom_preset = self.base_preset_uuid is not None
        reference = self
        if is_custom_preset:
            while reference.base_preset_uuid is not None:
                reference_versioned = manager.preset_for_uuid(reference.base_preset_uuid)
                if reference_versioned is None:
                    reference_versioned = manager.default_preset_for_game(reference.game)
                reference = reference_versioned.get_preset()

        included_preset_uuids = [versioned.uuid for versioned in manager.included_presets.values()]
        yield from bitpacking.encode_bool(is_custom_preset)
        yield from bitpacking.pack_array_element(reference.uuid, included_preset_uuids)
        if is_custom_preset:
            yield from self.configuration.bit_pack_encode({"reference": reference.configuration})
        yield _dictionary_byte_hash(self.configuration.game_data), 256

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "Preset":
        from randovania.interface_common.preset_manager import PresetManager
        manager: PresetManager = metadata["manager"]

        included_presets = [versioned for versioned in manager.included_presets.values()]

        is_custom_preset = bitpacking.decode_bool(decoder)
        reference = decoder.decode_element(included_presets).get_preset()
        if is_custom_preset:
            preset = Preset(
                name="{} Custom".format(reference.name),
                description="A customized preset.",
                uuid=uuid.uuid4(),
                base_preset_uuid=reference.uuid,
                game=reference.game,
                configuration=reference.configuration.bit_pack_unpack(decoder, {"reference": reference.configuration}),
            )
        else:
            preset = reference

        included_data_hash = decoder.decode_single(256)
        expected_data_hash = _dictionary_byte_hash(preset.configuration.game_data)
        if included_data_hash != expected_data_hash:
            raise ValueError("Given permalink is for a Randovania database with hash '{}', "
                             "but current database has hash '{}'.".format(included_data_hash, expected_data_hash))
        return preset

    def fork(self) -> "Preset":
        return dataclasses.replace(self, name=f"{self.name} Copy",
                                   description=f"A copy version of {self.name}.",
                                   uuid=uuid.uuid4(), base_preset_uuid=self.uuid)
