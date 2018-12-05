import dataclasses
import math

import bitstruct

from randovania.resolver.layout_configuration import LayoutTrickLevel, LayoutConfiguration, LayoutRandomizedFlag, \
    LayoutEnabledFlag


def do_stuff(quantity):
    x = math.ceil(math.log2(quantity))
    return bitstruct.compile('u{}'.format(x))


def pack(enum_class, value):
    enum_list = list(enum_class)
    compiled = do_stuff(len(enum_list))
    return compiled.pack(enum_list.index(value))


def do_pack(value: LayoutConfiguration):
    object_class = type(value)

    print("===============")
    for x in dataclasses.fields(value):
        print(x.name, x.type, getattr(value, x.name))

    print("===============")
    print(value.bit_pack_format())
    print(list(value.bit_pack_arguments()))
    print("===============")
    # print(">>>>>>>>", LayoutTrickLevel.bit_pack_format())

    # for field_name, field_type in value.__annotations__.items():
    #     if issubclass(field_type, Enum):
    #         print(field_name, len(field_type))


def main():
    print(pack(LayoutTrickLevel, LayoutTrickLevel.NO_TRICKS))

    config = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.HYPERMODE,
                                             sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                             item_loss=LayoutEnabledFlag.ENABLED,
                                             elevators=LayoutRandomizedFlag.VANILLA,
                                             pickup_quantities={})
    do_pack(config)

    cf = bitstruct.compile('u1u3u4u16')
    print(cf.pack(1, 2, 3, 4))


if __name__ == "__main__":
    main()
