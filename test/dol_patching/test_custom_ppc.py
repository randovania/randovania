import pytest

from randovania.dol_patching import assembler
from randovania.dol_patching.assembler import custom_ppc, ppc


@pytest.mark.parametrize("value", [-1, 0x100000000])
def test_load_unsigned_32bit_invalid(value):
    with pytest.raises(AssertionError):
        custom_ppc.load_unsigned_32bit(ppc.r1, value)


@pytest.mark.parametrize(["value", "expected"], [
    (0x00000000, b"\x3c\x20\x00\x00\x60\x21\x00\x00"),
    (0xFFFFFFFF, b"\x3c\x20\xFF\xFF\x60\x21\xFF\xFF"),
])
def test_load_unsigned_32bit_valid(value, expected):
    codes = list(custom_ppc.load_unsigned_32bit(ppc.r1, value).bytes_for(0, symbols={}))
    assert bytes(codes) == expected


def test_composite_bl_single():
    inc = ppc.bl(0x80085760)
    comp = custom_ppc.CompositeInstruction((inc,))

    assert list(comp.bytes_for(0x80085760 + 0x9C, symbols={})) == [0x4b, 0xff, 0xff, 0x65]


def test_composite_bl_double():
    target_address = 0x80085760
    start_address = 0x80085760 + 0x9C

    inc = ppc.bl(target_address)
    comp = custom_ppc.CompositeInstruction((inc, inc))

    composite_bytes = list(comp.bytes_for(start_address, symbols={}))
    assembled_bytes = list(assembler.assemble_instructions(start_address, [inc, inc]))

    assert composite_bytes == [0x4b, 0xff, 0xff, 0x65, 0x4b, 0xff, 0xff, 0x61]
    assert composite_bytes == assembled_bytes


def test_assemble_with_label():
    start_address = 0x80085760 + 0x9C

    patch = [
        ppc.bl(8, relative=True),
        ppc.bl("other"),
        ppc.nop(),
        ppc.nop().with_label("other"),
    ]

    assembled_bytes = list(assembler.assemble_instructions(start_address, patch))

    assert assembled_bytes == [
        0x48, 0x00, 0x00, 0x09,
        0x48, 0x00, 0x00, 0x09,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
    ]
