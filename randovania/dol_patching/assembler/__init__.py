from typing import Iterable

from randovania.dol_patching.assembler.ppc import Instruction


def assemble_instructions(address: int, instructions: Iterable[Instruction]) -> Iterable[int]:
    for i, instruction in enumerate(instructions):
        data = list(instruction.bytes_for(address))
        yield from data
        address += len(data)


def byte_count(instructions: Iterable[Instruction]) -> int:
    return sum(instruction.byte_count for instruction in instructions)
