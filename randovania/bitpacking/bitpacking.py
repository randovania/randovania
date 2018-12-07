import base64
import dataclasses
import math
from enum import Enum
from typing import Iterator, Tuple

import bitstruct


def _bits_for_number(value: int) -> int:
    return int(math.ceil(math.log2(value)))


class BitPackDecoder:
    _data: bytes
    _offset: int

    def __init__(self, data: bytes):
        self._data = data
        self._offset = 0

    def decode(self, *args) -> Tuple[int, ...]:
        compiled = bitstruct.CompiledFormat("".join("u{}".format(_bits_for_number(v)) for v in args))
        compiled.calcsize()
        offset = self._offset
        self._offset += compiled.calcsize()
        return compiled.unpack_from(self._data, offset)


class BitPackValue:
    def bit_pack_format(self) -> Iterator[int]:
        raise NotImplementedError()

    def bit_pack_arguments(self) -> Iterator[int]:
        raise NotImplementedError()

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        raise NotImplementedError()


class BitPackEnum(BitPackValue):
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


def do_stuff(quantity):
    x = math.ceil(math.log2(quantity))
    return bitstruct.compile('u{}'.format(x))


def pack(enum_class, value):
    enum_list = list(enum_class)
    compiled = do_stuff(len(enum_list))
    return compiled.pack(enum_list.index(value))


def pack_value(value: BitPackValue):
    # for i, (count, v) in enumerate(zip(value.bit_pack_format(), value.bit_pack_arguments())):
    #     f = "u{}".format(math.ceil(math.log2(count)))
    #     print(i, count, v, f)
    #     print(bitstruct.pack(f, v))
    # return
    f = "".join(
        "u{}".format(_bits_for_number(v))
        for v in value.bit_pack_format()
    )
    print(f)
    compiled = bitstruct.compile(f)
    return compiled.pack(*value.bit_pack_arguments())


def do_pack(value):

    print("=========!!!======")
    uncompressed = pack_value(value)
    print(len(uncompressed), uncompressed)
    print("base64", base64.b64encode(uncompressed))
    print("=========!!!======")
    # print(">>>>>>>>", LayoutTrickLevel.bit_pack_format())

    # for field_name, field_type in value.__annotations__.items():
    #     if issubclass(field_type, Enum):
    #         print(field_name, len(field_type))

    return uncompressed


def main():
    from randovania.resolver.layout_configuration import LayoutTrickLevel, LayoutConfiguration, LayoutRandomizedFlag, \
        LayoutEnabledFlag

    config = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.HYPERMODE,
                                             sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                             item_loss=LayoutEnabledFlag.ENABLED,
                                             elevators=LayoutRandomizedFlag.RANDOMIZED,
                                             pickup_quantities={
                                                 "Space Jump Boots": 0
                                             })

    from randovania.resolver.permalink import PermalinkConfiguration
    perma_config = PermalinkConfiguration(
        spoiler=LayoutEnabledFlag.ENABLED,
        disable_hud_popup=LayoutEnabledFlag.ENABLED,
        menu_mod=LayoutEnabledFlag.ENABLED,
    )

    from randovania.resolver.permalink import Permalink
    do_pack(config)

    permalink = Permalink(
        50000,
        permalink_configuration=perma_config,
        layout_configuration=config
    )

    encoded = do_pack(permalink)

    decoder = BitPackDecoder(encoded)
    decoded_permalink = Permalink.bit_pack_unpack(decoder)

    print(permalink == decoded_permalink)


if __name__ == "__main__":
    main()
