import base64
import binascii
import dataclasses
import hashlib
import json
import operator
from typing import Iterator, Iterable

import bitstruct
import construct

import randovania
from randovania.bitpacking.bitpacking import single_byte_hash
from randovania.games.game import RandovaniaGame
from randovania.layout import generator_parameters
from randovania.layout.generator_parameters import GeneratorParameters

_CURRENT_SCHEMA_VERSION = 13
_PERMALINK_MAX_VERSION = 256


class UnsupportedPermalink(Exception):
    seed_hash: bytes | None
    randovania_version: bytes
    games: tuple[RandovaniaGame, ...] | None

    def __init__(self, msg, seed_hash, version, games):
        super().__init__(msg)
        self.seed_hash = seed_hash
        self.randovania_version = version
        self.games = games


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


def create_rotator(inverse: bool):
    return lambda obj, ctx: bytes(rotate_bytes(obj, ctx.header.bytes_rotation, ctx.header.bytes_rotation, inverse))


PermalinkBinary = construct.FocusedSeq(
    "fields",
    schema_version=construct.Const(_CURRENT_SCHEMA_VERSION, construct.Byte),
    fields=construct.RawCopy(construct.Aligned(3, construct.Struct(
        header=construct.BitStruct(
            has_seed_hash=construct.Rebuild(construct.Flag, construct.this._.seed_hash != None),
            bytes_rotation=construct.Rebuild(
                construct.BitsInteger(7),
                lambda ctx: single_byte_hash(ctx._.generator_params) >> 1,
            )
        ),
        seed_hash=construct.If(construct.this.header.has_seed_hash, construct.Bytes(5)),
        randovania_version=construct.Bytes(4),  # short git hash
        generator_params=construct.ExprAdapter(
            construct.Prefixed(construct.VarInt, construct.GreedyBytes),
            # parsing
            decoder=create_rotator(inverse=True),
            # building
            encoder=create_rotator(inverse=False),
        ),
    ))),
    permalink_checksum=construct.Checksum(
        construct.Bytes(2),
        lambda data: hashlib.blake2b(data, digest_size=2).digest(),
        construct.this.fields.data,
    ),
    end=construct.Terminated,
)


@dataclasses.dataclass(frozen=True)
class Permalink:
    parameters: GeneratorParameters
    seed_hash: bytes | None
    randovania_version: bytes

    def __post_init__(self):
        if len(self.randovania_version) != 4:
            raise ValueError(f"randovania_version must be 4 bytes long, got {len(self.randovania_version)}")

        if self.seed_hash is not None and len(self.seed_hash) != 5:
            raise ValueError(f"seed_hash must be 5 bytes long if present, got {len(self.seed_hash)}")

    @classmethod
    def current_schema_version(cls) -> int:
        return _CURRENT_SCHEMA_VERSION

    @classmethod
    def _raise_if_different_schema_version(cls, version: int):
        if version != cls.current_schema_version():
            raise ValueError(
                "Given permalink has version {}, but this Randovania support only permalink of version {}.".format(
                    version, cls.current_schema_version()))

    @classmethod
    def validate_version(cls, b: bytes):
        cls._raise_if_different_schema_version(b[0])

    @classmethod
    def current_randovania_version(cls):
        return randovania.GIT_HASH

    @classmethod
    def from_parameters(cls, parameters: GeneratorParameters, seed_hash: bytes | None = None) -> "Permalink":
        return Permalink(
            parameters=parameters,
            seed_hash=seed_hash,
            randovania_version=cls.current_randovania_version(),
        )

    @property
    def as_base64_str(self) -> str:
        try:
            encoded = PermalinkBinary.build({
                "value": {
                    "header": {},
                    "seed_hash": self.seed_hash,
                    "randovania_version": self.randovania_version,
                    "generator_params": self.parameters.as_bytes,
                }
            })
            return base64.b64encode(encoded, altchars=b'-_').decode("utf-8")
        except ValueError as e:
            return f"Unable to create Permalink: {e}"

    @classmethod
    def from_str(cls, param: str) -> "Permalink":
        encoded_param = param.encode("utf-8")
        encoded_param += b"=" * ((4 - len(encoded_param)) % 4)

        try:
            b = base64.b64decode(encoded_param, altchars=b'-_', validate=True)
            if len(b) < 4:
                raise ValueError("String too short")

            cls.validate_version(b)
            data = PermalinkBinary.parse(b).value

        except construct.core.TerminatedError:
            raise ValueError("Extra text at the end")

        except construct.core.StreamError:
            raise ValueError("Missing text at the end")

        except construct.core.ChecksumError:
            raise ValueError("Incorrect checksum")

        except (binascii.Error, bitstruct.Error, construct.ConstructError) as e:
            raise ValueError(str(e))

        try:
            return Permalink(
                parameters=GeneratorParameters.from_bytes(data.generator_params),
                seed_hash=data.seed_hash,
                randovania_version=data.randovania_version,
            )
        except Exception as e:
            games = generator_parameters.try_decode_game_list(data.generator_params)

            if data.randovania_version != cls.current_randovania_version():
                msg = "Detected version {}, current version is {}".format(data.randovania_version.hex(),
                                                                          cls.current_randovania_version().hex())
            else:
                msg = f"Error decoding parameters - {e}"
            raise UnsupportedPermalink(msg, data.seed_hash, data.randovania_version, games) from e
