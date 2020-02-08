import base64
import binascii
import json
from dataclasses import dataclass
from typing import Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue, single_byte_hash
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.preset import Preset

_PERMALINK_MAX_VERSION = 16
_PERMALINK_MAX_SEED = 2 ** 31


def _dictionary_byte_hash(data: dict) -> int:
    return single_byte_hash(json.dumps(data, separators=(',', ':')).encode("UTF-8"))


@dataclass(frozen=True)
class Permalink(BitPackValue):
    seed_number: int
    spoiler: bool
    preset: Preset

    def __post_init__(self):
        if self.seed_number is None:
            raise ValueError("Missing seed number")
        if not (0 <= self.seed_number < _PERMALINK_MAX_SEED):
            raise ValueError("Invalid seed number: {}".format(self.seed_number))

    @property
    def patcher_configuration(self) -> PatcherConfiguration:
        return self.preset.patcher_configuration

    @property
    def layout_configuration(self) -> LayoutConfiguration:
        return self.preset.layout_configuration

    @classmethod
    def current_version(cls) -> int:
        # When this reaches _PERMALINK_MAX_VERSION, we need to change how we decode to avoid breaking version detection
        # for previous Randovania versions
        return 9

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield self.current_version(), _PERMALINK_MAX_VERSION
        yield self.seed_number, _PERMALINK_MAX_SEED
        yield int(self.spoiler), 2
        yield _dictionary_byte_hash(self.layout_configuration.game_data), 256

        manager = PresetManager(None)

        # Is this a custom preset?
        is_custom_preset = self.preset.base_preset_name is not None
        if is_custom_preset:
            reference_preset = manager.preset_for_name(self.preset.base_preset_name)
        else:
            reference_preset = self.preset

        yield from bitpacking.encode_bool(is_custom_preset)
        yield from bitpacking.pack_array_element(reference_preset, manager.included_presets)
        if is_custom_preset:
            yield from self.patcher_configuration.bit_pack_encode({"reference": reference_preset.patcher_configuration})
            yield from self.layout_configuration.bit_pack_encode({"reference": reference_preset.layout_configuration})

    @classmethod
    def _raise_if_different_version(cls, version: int):
        if version != cls.current_version():
            raise ValueError("Given permalink has version {}, but this Randovania "
                             "support only permalink of version {}.".format(version, cls.current_version()))

    @classmethod
    def validate_version(cls, decoder: BitPackDecoder):
        version = decoder.peek(_PERMALINK_MAX_VERSION)[0]
        cls._raise_if_different_version(version)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "Permalink":
        version, seed, spoiler = decoder.decode(_PERMALINK_MAX_VERSION, _PERMALINK_MAX_SEED, 2)
        cls._raise_if_different_version(version)

        included_data_hash = decoder.decode_single(256)

        manager = PresetManager(None)
        is_custom_preset = bitpacking.decode_bool(decoder)
        reference_preset = decoder.decode_element(manager.included_presets)

        if is_custom_preset:
            patcher_configuration = PatcherConfiguration.bit_pack_unpack(
                decoder, {"reference": reference_preset.patcher_configuration})
            layout_configuration = LayoutConfiguration.bit_pack_unpack(
                decoder, {"reference": reference_preset.layout_configuration})
            preset = Preset(
                name="{} Custom".format(reference_preset.name),
                description="A customized preset.",
                base_preset_name=reference_preset.name,
                patcher_configuration=patcher_configuration,
                layout_configuration=layout_configuration,
            )

        else:
            preset = reference_preset

        expected_data_hash = _dictionary_byte_hash(preset.layout_configuration.game_data)
        if included_data_hash != expected_data_hash:
            raise ValueError("Given permalink is for a Randovania database with hash '{}', "
                             "but current database has hash '{}'.".format(included_data_hash, expected_data_hash))

        return Permalink(
            seed,
            bool(spoiler),
            preset,
        )

    @classmethod
    def from_json_dict(cls, param: dict) -> "Permalink":
        return Permalink(
            seed_number=param["seed"],
            spoiler=param["spoiler"],
            preset=Preset.from_json_dict(param["preset"]),
        )

    @property
    def as_json(self) -> dict:
        return {
            "link": self.as_str,
            "seed": self.seed_number,
            "spoiler": self.spoiler,
            "preset": self.preset.as_json,
        }

    @property
    def as_str(self) -> str:
        try:
            b = bitpacking.pack_value(self)
            b += bytes([single_byte_hash(b)])
            return base64.b64encode(b).decode("utf-8")
        except ValueError as e:
            return "Unable to create Permalink: {}".format(e)

    @classmethod
    def from_str(cls, param: str) -> "Permalink":
        try:
            b = base64.b64decode(param.encode("utf-8"), validate=True)
            if len(b) < 2:
                raise ValueError("Data too small")

            decoder = BitPackDecoder(b)
            Permalink.validate_version(decoder)

            checksum = single_byte_hash(b[:-1])
            if checksum != b[-1]:
                raise ValueError("Incorrect checksum")

            return Permalink.bit_pack_unpack(decoder, {})

        except binascii.Error as e:
            raise ValueError("Unable to base64 decode '{permalink}': {error}".format(
                permalink=param,
                error=e,
            ))
