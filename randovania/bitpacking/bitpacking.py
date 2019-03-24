import dataclasses
import hashlib
import math
from enum import Enum
from typing import Iterator, Tuple, TypeVar, Any, List

import bitstruct

T = TypeVar("T")


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

    def decode_single(self, value: int) -> int:
        return self.decode(value)[0]

    def decode_element(self, array: List[T]) -> T:
        return array[self.decode_single(len(array))]

    def peek(self, *args) -> Tuple[int, ...]:
        """Decodes values from the current buffer, *NOT* advancing the current pointer"""
        compiled = _compile_format(*args)
        return compiled.unpack_from(self._data, self._offset)


class BitPackValue:
    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        raise NotImplementedError()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        raise NotImplementedError()


class BitPackBool(BitPackValue):
    value: bool

    def __init__(self, value: bool):
        self.value = value

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        yield int(self.value), 2

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> bool:
        return bool(decoder.decode(2)[0])


class BitPackEnum(BitPackValue):
    def __reduce__(self):
        return None

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        cls: Enum = self.__class__
        values = list(cls.__members__.values())
        yield values.index(self), len(values)

    @classmethod
    def bit_pack_unpack(cls: "Enum", decoder: BitPackDecoder):
        items = list(cls.__members__.values())
        index = decoder.decode(len(items))[0]
        return items[index]


_default_bit_pack_classes = {
    bool: BitPackBool,
}


def _get_bit_pack_value_for_type(value_type):
    if issubclass(value_type, BitPackValue):
        return value_type

    if value_type in _default_bit_pack_classes:
        return _default_bit_pack_classes[value_type]

    else:
        raise NotImplementedError("Unsupported bit packing for type {}".format(value_type))


def _get_bit_pack_value_for(value):
    if isinstance(value, BitPackValue):
        return value

    return _get_bit_pack_value_for_type(type(value))(value)


class BitPackDataClass(BitPackValue):
    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        for field in dataclasses.fields(self):
            yield from _get_bit_pack_value_for(getattr(self, field.name)).bit_pack_encode()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        args = {
            field.name: _get_bit_pack_value_for_type(field.type).bit_pack_unpack(decoder)
            for field in dataclasses.fields(cls)
            if field.init
        }
        return cls(**args)


def pack_array_element(element: T, array: List[T]) -> Iterator[Tuple[int, int]]:
    yield array.index(element), len(array)


def _pack_encode_results(values: List[Tuple[int, int]]):
    f = "".join(
        "u{}".format(_bits_for_number(v))
        for _, v in values
    )
    return bitstruct.compile(f).pack(*[argument for argument, _ in values])


def pack_value(value: BitPackValue) -> bytes:
    return _pack_encode_results([
        (value_argument, value_format)
        for value_argument, value_format in value.bit_pack_encode()
    ])


def round_trip(value: BitPackValue):
    """
    Encodes the given value and then recreates it using the encoded value
    :param value:
    :return:
    """
    b = pack_value(value)
    decoder = BitPackDecoder(b)
    return value.__class__.bit_pack_unpack(decoder)
