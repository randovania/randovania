import pytest

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
    codes = []
    for instruction in custom_ppc.load_unsigned_32bit(ppc.r1, value):
        codes.extend(instruction.bytes_for(0))
    assert bytes(codes) == expected
