from typing import Iterable

from randovania.dol_patching.assembler.ppc import Instruction


def assemble_instructions(address: int, instructions: Iterable[Instruction]) -> Iterable[int]:
    for i, instruction in enumerate(instructions):
        yield from instruction.bytes_for(address + i * 4)
