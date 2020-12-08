import struct

r0 = 0
r1 = 1
r2 = 2
r3 = 3
r4 = 4
r5 = 5
r6 = 6
r7 = 7
r8 = 8
r9 = 9
r30 = 30
r31 = 31

f0 = 0
f1 = 1


def lwz(input_register, offset: int, output_register):
    """
    *(output_register + offset) = input_register
    """
    pass


def or_(output_register, input_register_a, input_register_b, record_bit: bool = False):
    """
    output_register = input_register_a | input_register_b
    """
    # See https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/assembler/idalangref_or_instruction.html
    value = (
        (31 << 26)
        + (input_register_a << 21)
        + (output_register << 16)
        + (input_register_b << 11)
        + (444 << 1)
        + int(record_bit)
    )
    return list(struct.pack(">I", value))


def ori(output_register, input_register, constant):
    """
    output_register = input_register | constant
    """
    return [
        0x60,
        output_register << 5 + input_register,
        *struct.pack(">h", constant),
    ]


def li(register, literal):
    """
    register = literal
    """
    top_bytes = 0x3800 + (register << 5)
    return [
        top_bytes >> 8,
        top_bytes & 0xFF,
        *struct.pack(">h", literal),
    ]


def lfs(output_register, offset: int, input_register):
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
        output_register << 5 + input_register,
        *struct.pack(">h", offset),
    ]


def bl(address_or_symbol, instruction_address: int):
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
    return list(struct.pack(">I", value))


def stfs(input_register, offset: int, output_register):
    """
    *(float*)(output_register +offset) = input_register

    input_register is a float register.
    """
    return [
        0xD0,
        input_register << 5 + output_register,
        *struct.pack(">h", offset),
    ]


def icbi(ra, rb):
    value = 0x7C0007AC + (ra << 16) + (rb << 11)
    return list(struct.pack(">I", value))


def isync():
    return [
        0x4C,
        0x00,
        0x01,
        0x2C,
    ]
