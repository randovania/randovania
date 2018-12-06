import base64
import bz2
import dataclasses
import lzma
import math
from typing import Iterator

import bitstruct


def do_stuff(quantity):
    x = math.ceil(math.log2(quantity))
    return bitstruct.compile('u{}'.format(x))


def pack(enum_class, value):
    enum_list = list(enum_class)
    compiled = do_stuff(len(enum_list))
    return compiled.pack(enum_list.index(value))


class BitPackValue:
    def bit_pack_format(self) -> Iterator[int]:
        raise NotImplementedError()

    def bit_pack_arguments(self) -> Iterator[int]:
        raise NotImplementedError()


def pack_value(value: BitPackValue):
    # for i, (count, v) in enumerate(zip(value.bit_pack_format(), value.bit_pack_arguments())):
    #     f = "u{}".format(math.ceil(math.log2(count)))
    #     print(i, count, v, f)
    #     print(bitstruct.pack(f, v))
    # return
    f = "".join(
        "u{}".format(math.ceil(math.log2(v)))
        for v in value.bit_pack_format()
    )
    print(f)
    compiled = bitstruct.compile(f)
    return compiled.pack(*value.bit_pack_arguments())


def do_pack(value):
    object_class = type(value)

    print("===============")
    for x in dataclasses.fields(value):
        print(x.name, x.type, getattr(value, x.name))

    print("=========!!!======")
    uncompressed = pack_value(value)
    print(len(uncompressed), uncompressed)
    print("base64", base64.b64encode(uncompressed))
    print("=========!!!======")
    # print(">>>>>>>>", LayoutTrickLevel.bit_pack_format())

    # for field_name, field_type in value.__annotations__.items():
    #     if issubclass(field_type, Enum):
    #         print(field_name, len(field_type))


def main():
    from randovania.resolver.layout_configuration import LayoutTrickLevel, LayoutConfiguration, LayoutRandomizedFlag, \
        LayoutEnabledFlag

    config = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.HYPERMODE,
                                             sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                             item_loss=LayoutEnabledFlag.ENABLED,
                                             elevators=LayoutRandomizedFlag.VANILLA,
                                             pickup_quantities={
                                                 "Space Jump Boots": 0
                                             })
    do_pack(config)


if __name__ == "__main__":
    main()
