import base64
import binascii
import dataclasses
import json
import operator
import struct
from typing import Iterator, Iterable, Optional, Union

import bitstruct
import construct

from randovania.bitpacking.bitpacking import single_byte_hash, two_byte_hash
from randovania.layout.generator_parameters import GeneratorParameters

_PERMALINK_MAX_VERSION = 256


class UnsupportedPermalink(Exception):
    pass


# Permalink format:
# Byte 0: schema version
# Byte 1-2: hash
# Byte 3+, PermalinkBinary


PermalinkBinary = construct.Struct(
    header=construct.BitStruct(
        has_seed_hash=construct.Rebuild(construct.Flag, construct.this._.seed_hash != None),
        is_dev_version=construct.Flag,
        _filler=construct.Const(b"\x00" * 6),
    ),
    seed_hash=construct.If(construct.this.header.has_seed_hash, construct.Bytes(5)),
    version=construct.IfThenElse(
        construct.this.header.is_dev_version,
        construct.Bytes(4),  # short git hash
        construct.Byte,  # index of releases array
    ),
    generator_params=construct.Prefixed(construct.VarInt, construct.GreedyBytes),
)


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
    def from_parameters(cls, parameters: GeneratorParameters, seed_hash: Optional[bytes] = None) -> "Permalink":
        return Permalink(
            parameters=parameters,
            seed_hash=seed_hash,
            version=0,
        )

    @property
    def as_base64_str(self) -> str:
        try:
            encoded = PermalinkBinary.build({
                "header": {
                    "is_dev_version": False,
                },
                "seed_hash": self.seed_hash,
                "version": self.version,
                "generator_params": self.parameters.as_bytes,
            })
            # Add extra bytes so the base64 encoding never uses == at the end
            encoded += b"\x00" * ((3 - len(encoded)) % 3)

            # Rotate bytes, so the slightest change causes a cascading effect.
            # But skip the first byte so the version check can be done early in decoding.
            byte_hash = struct.unpack(">H", two_byte_hash(encoded))[0]
            new_bytes = [encoded[0]]
            new_bytes.extend(rotate_bytes(encoded[1:], byte_hash, byte_hash, inverse=False))

            result = struct.pack(">BH", self.current_schema_version(), byte_hash) + bytes(new_bytes)
            return base64.b64encode(result, altchars=b'-_').decode("utf-8")
        except ValueError as e:
            return "Unable to create Permalink: {}".format(e)

    @classmethod
    def from_str(cls, param: str) -> "Permalink":
        try:
            b = base64.b64decode(param.encode("utf-8"), altchars=b'-_', validate=True)
            if len(b) < 4:
                raise ValueError("String too short")

            cls.validate_version(b)
            byte_hash = struct.unpack_from(">H", b, 1)[0]
            new_bytes = [b[3]]
            new_bytes.extend(rotate_bytes(b[4:], byte_hash, byte_hash, inverse=True))

            decoded = bytes(new_bytes)
            if struct.unpack(">H", two_byte_hash(decoded))[0] != byte_hash:
                raise ValueError("Incorrect checksum")

            data = PermalinkBinary.parse(decoded)

        except (binascii.Error, bitstruct.Error) as e:
            raise ValueError("Unable to base64 decode '{permalink}': {error}".format(
                permalink=param,
                error=e,
            ))

        try:
            return Permalink(
                parameters=GeneratorParameters.from_bytes(data.generator_params),
                seed_hash=data.seed_hash,
                version=data.version,
            )
        except Exception as e:
            raise UnsupportedPermalink(param) from e
