import copy
from typing import Iterable

from randovania.dol_patching.assembler.ppc import Instruction, BaseInstruction


def assemble_instructions(address: int, instructions: list[BaseInstruction], symbols: dict[str, int] = None) -> \
        Iterable[int]:
    if symbols is not None:
        symbols = copy.copy(symbols)
    else:
        symbols = {}

    b = address
    for instruction in instructions:
        if instruction.label is not None:
            symbols[instruction.label] = b
        b += instruction.byte_count

    for i, instruction in enumerate(instructions):
        data = list(instruction.bytes_for(address, symbols=symbols))
        yield from data
        address += len(data)


def byte_count(instructions: Iterable[BaseInstruction]) -> int:
    return sum(instruction.byte_count for instruction in instructions)
