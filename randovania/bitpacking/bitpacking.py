import dataclasses
import hashlib
import math
from enum import Enum
from typing import Iterator, Tuple, TypeVar, List, Optional

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
        if len(array) == 1:
            return array[0]
        return array[self.decode_single(len(array))]

    def peek(self, *args) -> Tuple[int, ...]:
        """Decodes values from the current buffer, *NOT* advancing the current pointer"""
        compiled = _compile_format(*args)
        return compiled.unpack_from(self._data, self._offset)


class BitPackValue:
    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        raise NotImplementedError()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        raise NotImplementedError()


class BitPackBool(BitPackValue):
    value: bool

    def __init__(self, value: bool):
        self.value = value

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield int(self.value), 2

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> bool:
        return bool(decoder.decode_single(2))


class BitPackFloat(BitPackValue):
    value: float

    def __init__(self, value: float):
        self.value = value

    def bit_pack_encode(self, metadata: dict) -> Iterator[Tuple[int, int]]:
        if "if_different" in metadata:
            same = self.value == metadata["if_different"]
            yield from encode_bool(same)
            if same:
                return

        value_range = (metadata["max"] - metadata["min"]) * (10 ** metadata["precision"])
        yield int((self.value - metadata["min"]) * (10 ** metadata["precision"])), value_range

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> float:
        if "if_different" in metadata:
            same = decode_bool(decoder)
            if same:
                return metadata["if_different"]

        value_range = (metadata["max"] - metadata["min"]) * (10 ** metadata["precision"])
        decoded = decoder.decode_single(value_range)
        return float((decoded / (10 ** metadata["precision"])) + metadata["min"])


class BitPackInt(BitPackValue):
    value: int

    def __init__(self, value: int):
        self.value = value

    def bit_pack_encode(self, metadata: dict) -> Iterator[Tuple[int, int]]:
        if "if_different" in metadata:
            same = self.value == metadata["if_different"]
            yield from encode_bool(same)
            if same:
                return

        value_range = metadata["max"] - metadata["min"]
        yield self.value - metadata["min"], value_range

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> float:
        if "if_different" in metadata:
            same = decode_bool(decoder)
            if same:
                return metadata["if_different"]

        value_range = (metadata["max"] - metadata["min"])
        decoded = decoder.decode_single(value_range)
        return decoded + metadata["min"]


class BitPackEnum(BitPackValue):
    def __reduce__(self):
        return None

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        cls: Enum = self.__class__
        values = list(cls.__members__.values())
        yield from pack_array_element(self, values)

    @classmethod
    def bit_pack_unpack(cls: "Enum", decoder: BitPackDecoder, metadata):
        items = list(cls.__members__.values())
        return decoder.decode_element(items)


_default_bit_pack_classes = {
    bool: BitPackBool,
    int: BitPackInt,
    float: BitPackFloat,
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
    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        reference = metadata.get("reference")

        for field in dataclasses.fields(self):
            if not field.init:
                continue

            item = getattr(self, field.name)
            if reference is not None:
                is_different = item != getattr(reference, field.name)
                yield from encode_bool(is_different)
                if not is_different:
                    continue

            yield from _get_bit_pack_value_for(item).bit_pack_encode(field.metadata)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        reference = metadata.get("reference")
        args = {}

        for field in dataclasses.fields(cls):
            if not field.init:
                continue

            should_decode = True
            if reference is not None:
                if not decode_bool(decoder):
                    item = getattr(reference, field.name)
                    should_decode = False

            if should_decode:
                item = _get_bit_pack_value_for_type(field.type).bit_pack_unpack(decoder, field.metadata)

            args[field.name] = item

        return cls(**args)


def pack_array_element(element: T, array: List[T]) -> Iterator[Tuple[int, int]]:
    if len(array) > 1:
        yield array.index(element), len(array)
    else:
        if element not in array:
            raise ValueError("given element is not in array")


def _is_sorted(array: List[T]) -> bool:
    return array == list(sorted(array))


def _limits_for_size(remaining_size: int) -> Tuple[int, ...]:
    if remaining_size > 4:
        return 4, remaining_size
    elif remaining_size > 0:
        return remaining_size,
    else:
        return ()


def _aux_pack_sorted_array_elements(elements: List[T], array: List[T]) -> Iterator[Tuple[int, int]]:
    yield len(elements), len(array) + 1

    previous_index = 0
    for i, item in enumerate(elements):
        index = array.index(item)
        assert index is not None

        remaining_size = len(array) - previous_index - (len(elements) - i)
        yield from encode_int_with_limits(index - previous_index, _limits_for_size(remaining_size))
        previous_index = index


def pack_sorted_array_elements(elements: List[T], array: List[T]) -> Iterator[Tuple[int, int]]:
    assert _is_sorted(elements)
    assert _is_sorted(array)
    assert len(array) == len(set(array))

    if not array:
        return

    inverted_elements = [item for item in array if item not in elements]

    normal_results = list(_aux_pack_sorted_array_elements(elements, array))
    inverted_results = list(_aux_pack_sorted_array_elements(inverted_elements, array))

    bits_for_normal = sum(_bits_for_number(v[1]) for v in normal_results)
    bits_for_inverted = sum(_bits_for_number(v[1]) for v in inverted_results)

    should_invert = bits_for_normal > bits_for_inverted
    yield from encode_bool(should_invert)
    if should_invert:
        yield from inverted_results
    else:
        yield from normal_results


def decode_sorted_array_elements(decoder: BitPackDecoder, array: List[T]) -> List[T]:
    result = []

    if not array:
        return []

    inverted = decode_bool(decoder)
    elements_size = decoder.decode_single(len(array) + 1)

    previous_index = 0
    for i in range(elements_size):
        remaining_size = len(array) - previous_index - (elements_size - i)
        index = decode_int_with_limits(decoder, _limits_for_size(remaining_size))

        previous_index += index
        result.append(array[previous_index])

    if inverted:
        return [item for item in array if item not in result]
    else:
        return result


def encode_int_with_limits(value: int, limits: Tuple[int, ...]) -> Iterator[Tuple[int, int]]:
    previous_limit_sum = 0

    for i, limit in enumerate(limits):
        limit -= previous_limit_sum
        previous_limit_sum += limit

        if i == len(limits) - 1 or value < limit:
            yield value, limit + 1
            break

        yield limit, limit + 1
        value -= limit


def decode_int_with_limits(decoder: BitPackDecoder, limits: Tuple[int, ...]) -> int:
    value = 0
    previous_limit_sum = 0

    for limit in limits:
        limit -= previous_limit_sum
        previous_limit_sum += limit

        new_value = decoder.decode_single(limit + 1)
        value += new_value
        if new_value < limit:
            break

    return value


def encode_bool(value: bool) -> Iterator[Tuple[int, int]]:
    yield int(value), 2


def decode_bool(decoder: BitPackDecoder) -> bool:
    return bool(decoder.decode_single(2))


def _format_string_for(values: List[Tuple[int, int]]) -> str:
    return "".join(
        "u{}".format(_bits_for_number(v))
        for _, v in values
    )


def _pack_encode_results(values: List[Tuple[int, int]]):
    f = _format_string_for(values)
    return bitstruct.compile(f).pack(*[argument for argument, _ in values])


def pack_value(value: BitPackValue, metadata: Optional[dict] = None) -> bytes:
    if metadata is None:
        metadata = {}

    return _pack_encode_results([
        (value_argument, value_format)
        for value_argument, value_format in value.bit_pack_encode(metadata)
    ])


def round_trip(value: T,
               metadata: Optional[dict] = None) -> T:
    """
    Encodes the given value and then recreates it using the encoded value
    :param value:
    :param metadata:
    :return:
    """
    if metadata is None:
        metadata = {}

    b = pack_value(value, metadata)
    decoder = BitPackDecoder(b)
    return value.__class__.bit_pack_unpack(decoder, metadata)
