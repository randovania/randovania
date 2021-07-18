from typing import List, Optional, Dict

import dolphin_memory_engine

from randovania.game_connection.backend_choice import GameBackendChoice
from randovania.game_connection.memory_operation import (MemoryOperationException, MemoryOperation,
                                                         MemoryOperatorExecutor)

MEM1_START = 0x80000000
MEM1_END = 0x81800000


def _validate_range(address: int, size: int):
    if address < MEM1_START or address + size > MEM1_END:
        raise MemoryOperationException(
            f"Range {address:x} -> {address + size:x} is outside of the GameCube memory range.")


class DolphinExecutor(MemoryOperatorExecutor):
    def __init__(self):
        super().__init__()
        self.dolphin = dolphin_memory_engine

    @property
    def lock_identifier(self) -> Optional[str]:
        return "randovania-dolphin-backend"

    @property
    def backend_choice(self) -> GameBackendChoice:
        return GameBackendChoice.DOLPHIN

    async def connect(self) -> bool:
        if not self.dolphin.is_hooked():
            self.dolphin.hook()

        return self.dolphin.is_hooked()

    async def disconnect(self):
        raise NotImplementedError()

    def _test_still_hooked(self):
        try:
            if len(self.dolphin.read_bytes(0x0, 4)) != 4:
                raise RuntimeError("Dolphin hook didn't read the correct byte count")
        except RuntimeError as e:
            self.logger.warning(f"Test read for Dolphin hook didn't work: {e}")
            self.dolphin.un_hook()

    def is_connected(self) -> bool:
        if self.dolphin.is_hooked():
            self._test_still_hooked()

        return self.dolphin.is_hooked()

    # Game Backend Stuff
    def _memory_operation(self, op: MemoryOperation, pointers: Dict[int, Optional[int]]) -> Optional[bytes]:
        op.validate_byte_sizes()

        address = op.address
        if op.offset is not None:
            if address not in pointers:
                raise MemoryOperationException(f"Invalid op: {address:x} is not in pointers")
            address = pointers[address] + op.offset

        _validate_range(address, op.byte_count)

        if not self.dolphin.is_hooked():
            raise MemoryOperationException("Lost connection do Dolphin")

        result = None
        if op.read_byte_count is not None:
            result = self.dolphin.read_bytes(address, op.read_byte_count)

        if op.write_bytes is not None:
            self.dolphin.write_bytes(address, op.write_bytes)
            self.logger.debug(f"Wrote {op.write_bytes.hex()} to {address:x}")

        return result

    async def perform_memory_operations(self, ops: List[MemoryOperation]) -> Dict[MemoryOperation, bytes]:
        pointers_to_read = set()
        for op in ops:
            if op.offset is not None:
                pointers_to_read.add(op.address)

        pointers = {}
        for pointer in pointers_to_read:
            if not self.dolphin.is_hooked():
                raise MemoryOperationException("Lost connection do Dolphin")

            try:
                pointers[pointer] = self.dolphin.follow_pointers(pointer, [0])
            except RuntimeError:
                self.logger.debug(f"Failed to read a valid pointer from {pointer:x}")
                self._test_still_hooked()

            if not self.dolphin.is_hooked():
                raise MemoryOperationException("Lost connection do Dolphin")

        result = {}
        for op in ops:
            op_result = self._memory_operation(op, pointers)
            if op_result is not None:
                result[op] = op_result
        return result

    @property
    def name(self) -> str:
        return "Dolphin"
