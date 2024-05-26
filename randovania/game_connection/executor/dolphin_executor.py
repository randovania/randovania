from __future__ import annotations

import platform

import dolphin_memory_engine
import pid
from dolphin_memory_engine._dolphin_memory_engine import DolphinStatus

from randovania.game_connection.executor.memory_operation import (
    MemoryOperation,
    MemoryOperationException,
    MemoryOperationExecutor,
)

MEM1_START = 0x80000000
MEM1_END = 0x81800000


def _validate_range(address: int, size: int):
    if address < MEM1_START or address + size > MEM1_END:
        raise MemoryOperationException(
            f"Range {address:x} -> {address + size:x} is outside of the GameCube memory range."
        )


class DolphinExecutor(MemoryOperationExecutor):
    def __init__(self):
        super().__init__()
        self.dolphin = dolphin_memory_engine
        self._pid = pid.PidFile("randovania-dolphin-backend")

    @property
    def lock_identifier(self) -> str | None:
        return "randovania-dolphin-backend"

    async def connect(self) -> str | None:
        if platform.system() == "Darwin":
            return "macOS is not supported"

        if not self.dolphin.is_hooked():
            self.dolphin.hook()

        if not self.dolphin.is_hooked():
            status = self.dolphin.get_status()
            if status == DolphinStatus.notRunning:
                return "Unable to connect. Dolphin isn't started"
            if status == DolphinStatus.noEmu:
                return "Unable to connect. Dolphin is currently not emulating any games"

            return "Unable to connect to Dolphin"

        try:
            self._pid.create()
        except pid.PidFileError:
            return (
                "Another Randovania is connected to Dolphin already. Make sure you only have one instance of "
                "Randovania running"
            )

        return None

    def disconnect(self):
        self._pid.close()
        self.dolphin.un_hook()

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
    def _memory_operation(self, op: MemoryOperation, pointers: dict[int, int | None]) -> bytes | None:
        op.validate_byte_sizes()

        address = op.address
        if op.offset is not None:
            if address not in pointers:
                raise MemoryOperationException(f"Invalid op: {address:x} is not in pointers")

            new_address = pointers[address]
            if new_address is None:
                return None
            address = new_address + op.offset

        _validate_range(address, op.byte_count)

        if not self.dolphin.is_hooked():
            raise MemoryOperationException("Lost connection do Dolphin")

        try:
            result = None
            if op.read_byte_count is not None:
                result = self.dolphin.read_bytes(address, op.read_byte_count)

            if op.write_bytes is not None:
                self.dolphin.write_bytes(address, op.write_bytes)
                self.logger.debug(f"Wrote {op.write_bytes.hex()} to {address:x}")

        except RuntimeError as e:
            raise MemoryOperationException(f"Lost connection do Dolphin: {e}")

        return result

    async def perform_memory_operations(self, ops: list[MemoryOperation]) -> dict[MemoryOperation, bytes]:
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
                pointers[pointer] = None
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
