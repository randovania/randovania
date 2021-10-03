import base64
import binascii
import json
import operator
from dataclasses import dataclass
from typing import Iterator, Tuple, Dict, Iterable

import bitstruct

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue, single_byte_hash
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.preset import Preset

_PERMALINK_MAX_VERSION = 16
_PERMALINK_MAX_SEED = 2 ** 31
_PERMALINK_PLAYER_COUNT_LIMITS = (2, 256)


def _dictionary_byte_hash(data: dict) -> int:
    return single_byte_hash(json.dumps(data, separators=(',', ':')).encode("UTF-8"))


def rotate_bytes(data: Iterable[int], rotation: int, per_byte_adjustment: int,
                 inverse: bool = False) -> Iterator[int]:
    """
    Rotates the elements in data, in a reversible operation.
    :param data: The byte values to rotate. Should be ints in the [0, 255] range.
    :param rotation: By how much each item should be rotated, mod 256.
    :param per_byte_adjustment: Increment the rotation by this after each byte, mod 256.
    :param inverse: If True, it performs the inverse operation.
    :return:
    """
    if inverse:
        op = operator.sub
    else:
        op = operator.add
    for b in data:
        yield op(b, rotation) % 256
        rotation = (rotation + per_byte_adjustment) % 256


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
        object.__setattr__(self, "__cached_as_bytes", None)

    @classmethod
    def current_version(cls) -> int:
        # When this reaches _PERMALINK_MAX_VERSION, we need to change how we decode to avoid breaking version detection
        # for previous Randovania versions
        return 12

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield self.current_version(), _PERMALINK_MAX_VERSION
        yield self.seed_number, _PERMALINK_MAX_SEED
        yield from bitpacking.encode_bool(self.spoiler)
        yield from bitpacking.encode_int_with_limits(self.player_count, _PERMALINK_PLAYER_COUNT_LIMITS)

        manager = PresetManager(None)

        previous_unique_presets = []
        for preset in self.presets.values():
            already_encoded_preset = preset in previous_unique_presets
            yield from bitpacking.encode_bool(already_encoded_preset)
            if already_encoded_preset:
                yield from bitpacking.pack_array_element(preset, previous_unique_presets)
            else:
                previous_unique_presets.append(preset)
                yield from preset.bit_pack_encode({"manager": manager})

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
                preset = decoder.decode_element(previous_unique_presets)
            else:
                preset = Preset.bit_pack_unpack(decoder, {"manager": manager})
                previous_unique_presets.append(preset)
            presets[index] = preset

        return Permalink(seed_number, spoiler, presets)

    @classmethod
    def _raise_if_different_version(cls, version: int):
        if version != cls.current_version():
            raise ValueError("Given permalink has version {}, but this Randovania "
                             "support only permalink of version {}.".format(version, cls.current_version()))

    @classmethod
    def validate_version(cls, b: bytes):
        version = BitPackDecoder(b).peek(_PERMALINK_MAX_VERSION)[0]
        cls._raise_if_different_version(version)

    @property
    def as_bytes(self) -> bytes:
        cached_result = object.__getattribute__(self, "__cached_as_bytes")
        if cached_result is not None:
            return cached_result

        encoded = bitpacking.pack_value(self)
        # Add extra bytes so the base64 encoding never uses == at the end
        encoded += b"\x00" * (3 - (len(encoded) + 1) % 3)

        # Rotate bytes, so the slightest change causes a cascading effect.
        # But skip the first byte so the version check can be done early in decoding.
        byte_hash = single_byte_hash(encoded)
        new_bytes = [encoded[0]]
        new_bytes.extend(rotate_bytes(encoded[1:], byte_hash, byte_hash, inverse=False))

        # Append the hash, so the rotation can be reversed and the checksum verified
        new_bytes.append(byte_hash)

        result = bytes(new_bytes)
        object.__setattr__(self, "__cached_as_bytes", result)
        return result

    @classmethod
    def from_bytes(cls, b: bytes) -> "Permalink":
        Permalink.validate_version(b)

        byte_hash = b[-1]
        new_bytes = [b[0]]
        new_bytes.extend(rotate_bytes(b[1:-1], byte_hash, byte_hash, inverse=True))

        decoded = bytes(new_bytes)
        if single_byte_hash(decoded) != byte_hash:
            raise ValueError("Incorrect checksum")

        decoder = BitPackDecoder(decoded)
        return Permalink.bit_pack_unpack(decoder, {})

    @property
    def as_base64_str(self) -> str:
        try:
            return base64.b64encode(self.as_bytes, altchars=b'-_').decode("utf-8")
        except ValueError as e:
            return "Unable to create Permalink: {}".format(e)

    @classmethod
    def from_str(cls, param: str) -> "Permalink":
        try:
            b = base64.b64decode(param.encode("utf-8"), altchars=b'-_', validate=True)
            if len(b) < 2:
                raise ValueError("Data too small")

            return cls.from_bytes(b)

        except (binascii.Error, bitstruct.Error) as e:
            raise ValueError("Unable to base64 decode '{permalink}': {error}".format(
                permalink=param,
                error=e,
            ))

    @property
    def player_count(self) -> int:
        return len(self.presets)

    def get_preset(self, index: int) -> Preset:
        return self.presets[index]
