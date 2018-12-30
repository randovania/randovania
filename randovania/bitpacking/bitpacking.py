import dataclasses
import hashlib
import math
from enum import Enum
from typing import Iterator, Tuple

import bitstruct


def _bits_for_number(value: int) -> int:
    return int(math.ceil(math.log2(value)))


def single_byte_hash(data: bytes) -> int:
    return hashlib.blake2b(data, digest_size=1).digest()[0]


def _compile_format(*args):
    return bitstruct.CompiledFormat("".join("u{}".format(_bits_for_number(v)) for v in args))


class BitPackDecoder:
    _data: bytes
    _offset: int

    def __init__(self, data: bytes):
        self._data = data
        self._offset = 0

    def decode(self, *args) -> Tuple[int, ...]:
        """Decodes values from the current buffer, advancing the current pointer"""
        compiled = _compile_format(*args)
        offset = self._offset
        self._offset += compiled.calcsize()
        return compiled.unpack_from(self._data, offset)

    def peek(self, *args) -> Tuple[int, ...]:
        """Decodes values from the current buffer, *NOT* advancing the current pointer"""
        compiled = _compile_format(*args)
        return compiled.unpack_from(self._data, self._offset)


class BitPackValue:
    def bit_pack_format(self) -> Iterator[int]:
        raise NotImplementedError()

    def bit_pack_arguments(self) -> Iterator[int]:
        raise NotImplementedError()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        raise NotImplementedError()


class BitPackEnum(BitPackValue):
    def __reduce__(self):
        return None

    def bit_pack_format(self) -> Iterator[int]:
        cls: Enum = self.__class__
        yield len(cls.__members__)

    def bit_pack_arguments(self) -> Iterator[int]:
        cls: Enum = self.__class__
        yield list(cls.__members__.values()).index(self)

    @classmethod
    def bit_pack_unpack(cls: "Enum", decoder: BitPackDecoder):
        items = list(cls.__members__.values())
        index = decoder.decode(len(items))[0]
        return items[index]


class BitPackDataClass(BitPackValue):
    def bit_pack_format(self) -> Iterator[int]:
        for field in dataclasses.fields(self):
            yield from getattr(self, field.name).bit_pack_format()

    def bit_pack_arguments(self) -> Iterator[int]:
        for field in dataclasses.fields(self):
            yield from getattr(self, field.name).bit_pack_arguments()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        args = {
            field.name: field.type.bit_pack_unpack(decoder)
            for field in dataclasses.fields(cls)
            if field.init
        }
        return cls(**args)


def pack_value(value: BitPackValue) -> bytes:
    f = "".join(
        "u{}".format(_bits_for_number(v))
        for v in value.bit_pack_format()
    )
    return bitstruct.compile(f).pack(*value.bit_pack_arguments())
