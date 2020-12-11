import dataclasses as _dataclasses
import struct as _struct


def _pack(*args):
    return _struct.pack(*args)


@_dataclasses.dataclass(frozen=True)
class Register:
    number: int


class GeneralRegister(Register):
    pass


class FloatRegister(Register):
    pass


r0 = GeneralRegister(0)
r1 = GeneralRegister(1)
r2 = GeneralRegister(2)
r3 = GeneralRegister(3)
r4 = GeneralRegister(4)
r5 = GeneralRegister(5)
r6 = GeneralRegister(6)
r7 = GeneralRegister(7)
r8 = GeneralRegister(8)
r9 = GeneralRegister(9)
r30 = GeneralRegister(30)
r31 = GeneralRegister(31)

f0 = FloatRegister(0)
f1 = FloatRegister(1)


def lwz(input_register: GeneralRegister, offset: int, output_register: GeneralRegister):
    """
    *(output_register + offset) = input_register
    """
    pass


def or_(output_register: GeneralRegister, input_register_a: GeneralRegister, input_register_b: GeneralRegister,
        record_bit: bool = False):
    """
    output_register = input_register_a | input_register_b
    """
    # See https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/assembler/idalangref_or_instruction.html
    value = (
            (31 << 26)
            + (input_register_a.number << 21)
            + (output_register.number << 16)
            + (input_register_b.number << 11)
            + (444 << 1)
            + int(record_bit)
    )
    return list(_pack(">I", value))


def ori(output_register: GeneralRegister, input_register: GeneralRegister, constant: int):
    """
    output_register = input_register | constant
    """
    return [
        0x60,
        output_register.number << 5 + input_register.number,
        *_pack(">h", constant),
    ]


def nop():
    return ori(r0, r0, 0x0)


def li(register: GeneralRegister, literal: int):
    """
    register = literal
    """
    top_bytes = 0x3800 + (register.number << 5)
    return [
        top_bytes >> 8,
        top_bytes & 0xFF,
        *_pack(">h", literal),
    ]


def lfs(output_register: FloatRegister, offset: int, input_register: GeneralRegister):
    """
    output_register = (float) *(input_register + offset)

    output_register is a float register.
    """
    # first byte: C0
    # top 4 bits of the second byte: output register
    # bottom 4 bits of the second byte: input_register
    # last two bytes: offset
    return [
        0xC0,
        output_register.number << 5 + input_register.number,
        *_pack(">h", offset),
    ]


def bl(address_or_symbol: int, instruction_address: int):
    """
    jumps to the given address
    """
    address = (instruction_address - address_or_symbol) // 4
    if address < 0:
        address += 1 << 24

    value = (
            (18 << 26)
            + (address << 2)
            + (0 << 1)  # Absolute Address Bit (AA)
            + (1 << 0)  # Link Bit (LK)
    )
    return list(_pack(">I", value))


def _store(input_register: Register, offset: int, output_register: GeneralRegister, op_code: int):
    return list(_pack(">I", ((op_code << 26)
                             + (input_register.number << 21)
                             + (output_register.number << 16)
                             + offset
                             )))


def stb(input_register: GeneralRegister, offset: int, output_register: GeneralRegister):
    """
    *(output_register +offset) = input_register
    """
    return _store(input_register, offset, output_register, 38)


def stw(input_register: GeneralRegister, offset: int, output_register: GeneralRegister):
    """
    *(output_register +offset) = input_register
    """
    return _store(input_register, offset, output_register, 36)


def stfs(input_register: FloatRegister, offset: int, output_register: GeneralRegister):
    """
    *(float*)(output_register +offset) = input_register
    """
    return _store(input_register, offset, output_register, 52)


def icbi(ra: int, rb: int):
    value = 0x7C0007AC + (ra << 16) + (rb << 11)
    return list(_pack(">I", value))


def isync():
    return [
        0x4C,
        0x00,
        0x01,
        0x2C,
    ]
