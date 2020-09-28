import base64
import binascii
import json
from dataclasses import dataclass
from typing import Iterator, Tuple, Dict

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue, single_byte_hash
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.preset import Preset

_PERMALINK_MAX_VERSION = 16
_PERMALINK_MAX_SEED = 2 ** 31
_PERMALINK_PLAYER_COUNT_LIMITS = (2, 256)


def _dictionary_byte_hash(data: dict) -> int:
    return single_byte_hash(json.dumps(data, separators=(',', ':')).encode("UTF-8"))


def _encode_preset(preset: Preset, manager: PresetManager):
    """

    :param preset:
    :param manager:
    :return:
    """
    # Is this a custom preset?
    is_custom_preset = preset.base_preset_name is not None
    if is_custom_preset:
        reference_preset = manager.preset_for_name(preset.base_preset_name)
    else:
        reference_preset = preset

    yield from bitpacking.encode_bool(is_custom_preset)
    yield from bitpacking.pack_array_element(reference_preset, manager.included_presets)
    if is_custom_preset:
        yield from preset.patcher_configuration.bit_pack_encode(
            {"reference": reference_preset.patcher_configuration})
        yield from preset.layout_configuration.bit_pack_encode(
            {"reference": reference_preset.layout_configuration})
    yield _dictionary_byte_hash(preset.layout_configuration.game_data), 256


def _decode_preset(decoder: BitPackDecoder, manager: PresetManager) -> Preset:
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
    included_data_hash = decoder.decode_single(256)
    expected_data_hash = _dictionary_byte_hash(preset.layout_configuration.game_data)
    if included_data_hash != expected_data_hash:
        raise ValueError("Given permalink is for a Randovania database with hash '{}', "
                         "but current database has hash '{}'.".format(included_data_hash, expected_data_hash))
    return preset


@dataclass(frozen=True)
class Permalink(BitPackValue):
    seed_number: int
    spoiler: bool
    presets: Dict[int, Preset]

    def __post_init__(self):
        if self.seed_number is None:
            raise ValueError("Missing seed number")
        if not (0 <= self.seed_number < _PERMALINK_MAX_SEED):
            raise ValueError("Invalid seed number: {}".format(self.seed_number))
        object.__setattr__(self, "__cached_as_str", None)

    @classmethod
    def current_version(cls) -> int:
        # When this reaches _PERMALINK_MAX_VERSION, we need to change how we decode to avoid breaking version detection
        # for previous Randovania versions
        return 10

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield self.current_version(), _PERMALINK_MAX_VERSION
        yield self.seed_number, _PERMALINK_MAX_SEED
        yield from bitpacking.encode_bool(self.spoiler)
        yield from bitpacking.encode_int_with_limits(self.player_count, _PERMALINK_PLAYER_COUNT_LIMITS)

        manager = PresetManager(None)

        previous_unique_presets = []
        for preset in self.presets.values():
            yield from bitpacking.encode_bool(preset in previous_unique_presets)
            if preset in previous_unique_presets:
                yield from bitpacking.pack_array_element(preset, previous_unique_presets)
                continue

            previous_unique_presets.append(preset)
            yield from _encode_preset(preset, manager)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "Permalink":
        version, seed_number = decoder.decode(_PERMALINK_MAX_VERSION, _PERMALINK_MAX_SEED)
        cls._raise_if_different_version(version)

        spoiler = bitpacking.decode_bool(decoder)
        player_count = bitpacking.decode_int_with_limits(decoder, _PERMALINK_PLAYER_COUNT_LIMITS)
        manager = PresetManager(None)

        previous_unique_presets = []
        presets = {}

        for index in range(player_count):
            in_previous_presets = bitpacking.decode_bool(decoder)
            if in_previous_presets:
                presets[index] = decoder.decode_element(previous_unique_presets)
                continue

            preset = _decode_preset(decoder, manager)
            previous_unique_presets.append(preset)
            presets[index] = preset

        return Permalink(seed_number, spoiler, presets)

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
    def from_json_dict(cls, param: dict) -> "Permalink":
        return Permalink(
            seed_number=param["seed"],
            spoiler=param["spoiler"],
            presets={
                index: Preset.from_json_dict(preset)
                for index, preset in enumerate(param["presets"])
            },
        )

    @property
    def as_json(self) -> dict:
        return {
            "link": self.as_str,
            "seed": self.seed_number,
            "spoiler": self.spoiler,
            "presets": [preset.as_json for preset in self.presets.values()],
        }

    @property
    def as_str(self) -> str:
        cached_result = object.__getattribute__(self, "__cached_as_str")
        if cached_result is not None:
            return cached_result
        try:
            b = bitpacking.pack_value(self)
            b += bytes([single_byte_hash(b)])
            result = base64.b64encode(b).decode("utf-8")
            object.__setattr__(self, "__cached_as_str", result)
            return result
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

    @property
    def player_count(self) -> int:
        return len(self.presets)

    def get_preset(self, index: int) -> Preset:
        return self.presets[index]
