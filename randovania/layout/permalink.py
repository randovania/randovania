import base64
import binascii
import dataclasses
import json
import operator
from typing import Iterator, Iterable, Optional, Union

import bitstruct

from randovania.bitpacking.bitpacking import BitPackDecoder, single_byte_hash
from randovania.layout.generator_parameters import GeneratorParameters

_PERMALINK_MAX_VERSION = 256


# Permalink format:
# Byte 0: version
# Byte 1-2: hash


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


@dataclasses.dataclass(frozen=True)
class Permalink:
    parameters: GeneratorParameters
    seed_hash: Optional[bytes]

    # Either an index of the releases array, or a short git commit hash
    version: Union[int, bytes]

    @classmethod
    def current_schema_version(cls) -> int:
        return 13

    @classmethod
    def _raise_if_different_schema_version(cls, version: int):
        if version != cls.current_schema_version():
            raise ValueError("Given permalink has version {}, but this Randovania "
                             "support only permalink of version {}.".format(version, cls.current_schema_version()))

    @classmethod
    def validate_version(cls, b: bytes):
        cls._raise_if_different_schema_version(b[0])

    @classmethod
    def from_parameters(cls, parameters: GeneratorParameters) -> "Permalink":
        return Permalink(
            parameters=parameters,
            seed_hash=None,
            version=0,
        )

    @property
    def as_base64_str(self) -> str:
        try:
            encoded = self.parameters.as_bytes

            # Add extra bytes so the base64 encoding never uses == at the end
            encoded += b"\x00" * (3 - (len(encoded) + 1) % 3)

            # Rotate bytes, so the slightest change causes a cascading effect.
            # But skip the first byte so the version check can be done early in decoding.
            byte_hash = single_byte_hash(encoded)
            new_bytes = [encoded[0]]
            new_bytes.extend(rotate_bytes(encoded[1:], byte_hash, byte_hash, inverse=False))

            # Append the hash, so the rotation can be reversed and the checksum verified
            new_bytes.append(byte_hash)

            return base64.b64encode(bytes(new_bytes), altchars=b'-_').decode("utf-8")
        except ValueError as e:
            return "Unable to create Permalink: {}".format(e)

    @classmethod
    def from_str(cls, param: str) -> "Permalink":
        try:
            b = base64.b64decode(param.encode("utf-8"), altchars=b'-_', validate=True)
            if len(b) < 2:
                raise ValueError("Data too small")

            cls.validate_version(b)

            byte_hash = b[-1]
            new_bytes = [b[0]]
            new_bytes.extend(rotate_bytes(b[1:-1], byte_hash, byte_hash, inverse=True))

            decoded = bytes(new_bytes)
            if single_byte_hash(decoded) != byte_hash:
                raise ValueError("Incorrect checksum")

            return Permalink(
                parameters=GeneratorParameters.from_bytes(decoded),
                seed_hash=None,
                version=0,
            )

        except (binascii.Error, bitstruct.Error) as e:
            raise ValueError("Unable to base64 decode '{permalink}': {error}".format(
                permalink=param,
                error=e,
            ))
