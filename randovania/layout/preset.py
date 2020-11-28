import dataclasses
import json
from typing import Optional, List, Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.layout.echoes_configuration import EchoesConfiguration
from randovania.layout.patcher_configuration import PatcherConfiguration


def _dictionary_byte_hash(data: dict) -> int:
    return bitpacking.single_byte_hash(json.dumps(data, separators=(',', ':')).encode("UTF-8"))


@dataclasses.dataclass(frozen=True)
class Preset(BitPackValue):
    name: str
    description: str
    base_preset_name: Optional[str]
    patcher_configuration: PatcherConfiguration
    configuration: EchoesConfiguration

    @property
    def as_json(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "base_preset_name": self.base_preset_name,
            "patcher_configuration": self.patcher_configuration.as_json,
            "configuration": self.configuration.as_json,
        }

    @classmethod
    def from_json_dict(cls, value) -> "Preset":
        return Preset(
            name=value["name"],
            description=value["description"],
            base_preset_name=value["base_preset_name"],
            patcher_configuration=PatcherConfiguration.from_json_dict(value["patcher_configuration"]),
            configuration=EchoesConfiguration.from_json_dict(value["configuration"]),
        )

    def dangerous_settings(self) -> List[str]:
        return self.configuration.dangerous_settings()

    def is_same_configuration(self, other: "Preset") -> bool:
        return (self.patcher_configuration == other.patcher_configuration
                and self.configuration == other.configuration)

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        from randovania.interface_common.preset_manager import PresetManager
        manager: PresetManager = metadata["manager"]

        # Is this a custom preset?
        is_custom_preset = self.base_preset_name is not None
        if is_custom_preset:
            reference_versioned = manager.included_preset_with_name(self.base_preset_name)
            if reference_versioned is None:
                reference_versioned = manager.default_preset_for_game(self.configuration.game)
            reference = reference_versioned.get_preset()
        else:
            reference = self

        included_presets = [versioned.get_preset() for versioned in manager.included_presets]

        yield from bitpacking.encode_bool(is_custom_preset)
        yield from bitpacking.pack_array_element(reference, included_presets)
        if is_custom_preset:
            yield from self.patcher_configuration.bit_pack_encode({"reference": reference.patcher_configuration})
            yield from self.configuration.bit_pack_encode({"reference": reference.configuration})
        yield _dictionary_byte_hash(self.configuration.game_data), 256

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "Preset":
        from randovania.interface_common.preset_manager import PresetManager
        manager: PresetManager = metadata["manager"]

        included_presets = [versioned.get_preset() for versioned in manager.included_presets]

        is_custom_preset = bitpacking.decode_bool(decoder)
        reference = decoder.decode_element(included_presets)
        if is_custom_preset:
            patcher_configuration = PatcherConfiguration.bit_pack_unpack(
                decoder, {"reference": reference.patcher_configuration})
            game_configuration = EchoesConfiguration.bit_pack_unpack(
                decoder, {"reference": reference.configuration})
            preset = Preset(
                name="{} Custom".format(reference.name),
                description="A customized preset.",
                base_preset_name=reference.name,
                patcher_configuration=patcher_configuration,
                configuration=game_configuration,
            )
        else:
            preset = reference

        included_data_hash = decoder.decode_single(256)
        expected_data_hash = _dictionary_byte_hash(preset.configuration.game_data)
        if included_data_hash != expected_data_hash:
            raise ValueError("Given permalink is for a Randovania database with hash '{}', "
                             "but current database has hash '{}'.".format(included_data_hash, expected_data_hash))
        return preset
