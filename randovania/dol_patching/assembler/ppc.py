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


class Instruction:
    value: int

    def __init__(self, value: int):
        self.value = value

    def __iter__(self):
        return iter(_pack(">I", self.value))

    @classmethod
    def compose(cls, data):
        value = 0
        bits_left = 32
        for item, bit_size, signed in data:
            bits_left -= bit_size
            if signed:
                assert -(1 << (bit_size - 1)) <= item < (1 << (bit_size - 1))
                if item < 0:
                    item += (1 << bit_size)
            else:
                assert 0 <= item < (1 << bit_size)
            value += item << bits_left

        assert bits_left == 0
        return cls(value)


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
r10 = GeneralRegister(10)
r25 = GeneralRegister(25)
r26 = GeneralRegister(26)
r27 = GeneralRegister(27)
r28 = GeneralRegister(28)
r29 = GeneralRegister(29)
r30 = GeneralRegister(30)
r31 = GeneralRegister(31)

f0 = FloatRegister(0)
f1 = FloatRegister(1)


def lwz(output_register: GeneralRegister, offset: int, input_register: GeneralRegister):
    """
    *(output_register + offset) = input_register
    """
    return Instruction.compose(((32, 6, False),
                                (output_register.number, 5, False),
                                (input_register.number, 5, False),
                                (offset, 16, True)))


def or_(output_register: GeneralRegister, input_register_a: GeneralRegister, input_register_b: GeneralRegister,
        record_bit: bool = False):
    """
    output_register = input_register_a | input_register_b
    """
    # See https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/assembler/idalangref_or_instruction.html
    return Instruction.compose(((31, 6, False),
                                (input_register_a.number, 5, False),
                                (output_register.number, 5, False),
                                (input_register_b.number, 5, False),
                                (444, 10, False),
                                (int(record_bit), 1, False),
                                ))


def ori(output_register: GeneralRegister, input_register: GeneralRegister, constant: int):
    """
    output_register = input_register | constant
    """
    return Instruction.compose(((24, 6, False),
                                (output_register.number, 5, False),
                                (input_register.number, 5, False),
                                (constant, 16, False)))


def nop():
    return ori(r0, r0, 0x0)


def li(register: GeneralRegister, literal: int):
    """
    register = literal
    """
    return addi(register, r0, literal)


def lfs(output_register: FloatRegister, offset: int, input_register: GeneralRegister):
    """
    output_register = (float) *(input_register + offset)

    output_register is a float register.
    """
    return Instruction.compose(((48, 6, False),
                                (output_register.number, 5, False),
                                (input_register.number, 5, False),
                                (offset, 16, True)))


def bl(address_or_symbol: int):
    """
    jumps to the given address
    """

    def with_inc_address(instruction_address: int):
        jump_offset = (address_or_symbol - instruction_address) // 4
        return Instruction.compose(((18, 6, False),
                                    (jump_offset, 24, True),
                                    (0, 1, False),
                                    (1, 1, False)))

    return with_inc_address


def _store(input_register: Register, offset: int, output_register: GeneralRegister, op_code: int):
    return Instruction.compose(((op_code, 6, False),
                                (input_register.number, 5, False),
                                (output_register.number, 5, False),
                                (offset, 16, True)))


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
    return Instruction(value)


def isync():
    return Instruction(0x4C00012C)


def addi(output_register: GeneralRegister, input_register: GeneralRegister, literal: int):
    """
    output_register = input_register + literal
    """
    return Instruction.compose(((14, 6, False),
                                (output_register.number, 5, False),
                                (input_register.number, 5, False),
                                (literal, 16, True)))
