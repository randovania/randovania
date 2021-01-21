from typing import Tuple

from randovania.dol_patching.assembler import ppc


class CompositeInstruction(ppc.BaseInstruction):
    def __init__(self, instructions: Tuple[ppc.BaseInstruction, ...]):
        super().__init__()
        self.instructions = instructions

    def bytes_for(self, address: int):
        for instruction in self.instructions:
            yield from instruction.bytes_for(address)
            address += instruction.byte_count

    def __eq__(self, other):
        return isinstance(other, CompositeInstruction) and other.instructions == self.instructions

    @property
    def byte_count(self):
        return sum(instruction.byte_count for instruction in self.instructions)


def load_unsigned_32bit(output_register: ppc.GeneralRegister, value: int) -> CompositeInstruction:
    return CompositeInstruction((
        ppc.lis(output_register, value >> 16),
        ppc.ori(output_register, output_register, value & 0xFFFF),
    ))
