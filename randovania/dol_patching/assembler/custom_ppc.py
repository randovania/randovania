from typing import List

from randovania.dol_patching.assembler import ppc


def load_unsigned_32bit(output_register: ppc.GeneralRegister, value: int) -> List[ppc.Instruction]:
    return [
        ppc.lis(output_register, value >> 16),
        ppc.ori(output_register, output_register, value & 0xFFFF),
    ]
