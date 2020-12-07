import dataclasses
import json
from typing import Optional, List, Iterator, Tuple, Union

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.games.game import RandovaniaGame
from randovania.layout.corruption_configuration import CorruptionConfiguration
from randovania.layout.echoes_configuration import EchoesConfiguration
from randovania.layout.prime_configuration import PrimeConfiguration


def _dictionary_byte_hash(data: dict) -> int:
    return bitpacking.single_byte_hash(json.dumps(data, separators=(',', ':')).encode("UTF-8"))


_game_to_config = {
    RandovaniaGame.PRIME1: PrimeConfiguration,
    RandovaniaGame.PRIME2: EchoesConfiguration,
    RandovaniaGame.PRIME3: CorruptionConfiguration,
}


@dataclasses.dataclass(frozen=True)
class Preset(BitPackValue):
    name: str
    description: str
    base_preset_name: Optional[str]
    game: RandovaniaGame
    configuration: Union[EchoesConfiguration, CorruptionConfiguration]

    @property
    def as_json(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "base_preset_name": self.base_preset_name,
            "game": self.game.value,
            "configuration": self.configuration.as_json,
        }

    @classmethod
    def from_json_dict(cls, value) -> "Preset":
        game = RandovaniaGame(value["game"])
        return Preset(
            name=value["name"],
            description=value["description"],
            base_preset_name=value["base_preset_name"],
            game=game,
            configuration=_game_to_config[game].from_json(value["configuration"]),
        )

    def dangerous_settings(self) -> List[str]:
        return self.configuration.dangerous_settings()

    def is_same_configuration(self, other: "Preset") -> bool:
        return self.configuration == other.configuration

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        from randovania.interface_common.preset_manager import PresetManager
        manager: PresetManager = metadata["manager"]

        # Is this a custom preset?
        is_custom_preset = self.base_preset_name is not None
        if is_custom_preset:
            reference_versioned = manager.included_preset_with_name(self.base_preset_name)
            if reference_versioned is None:
                reference_versioned = manager.default_preset_for_game(self.game)
            reference = reference_versioned.get_preset()
        else:
            reference = self

        included_presets = [versioned.get_preset() for versioned in manager.included_presets]

        yield from bitpacking.encode_bool(is_custom_preset)
        yield from bitpacking.pack_array_element(reference, included_presets)
        if is_custom_preset:
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
            preset = Preset(
                name="{} Custom".format(reference.name),
                description="A customized preset.",
                base_preset_name=reference.name,
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
