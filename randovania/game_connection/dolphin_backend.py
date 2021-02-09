from typing import List, Optional, Dict

import dolphin_memory_engine

from randovania.game_connection.backend_choice import GameBackendChoice
from randovania.game_connection.connection_backend import ConnectionBackend, MemoryOperation, MemoryOperationException
from randovania.game_connection.connection_base import GameConnectionStatus
from randovania.game_description.world import World

MEM1_START = 0x80000000
MEM1_END = 0x81800000


def _validate_range(address: int, size: int):
    if address < MEM1_START or address + size > MEM1_END:
        raise MemoryOperationException(
            f"Range {address:x} -> {address + size:x} is outside of the GameCube memory range.")


class DolphinBackend(ConnectionBackend):
    _world: Optional[World] = None

    def __init__(self):
        super().__init__()
        self.dolphin = dolphin_memory_engine

    @property
    def lock_identifier(self) -> Optional[str]:
        return "randovania-dolphin-backend"

    @property
    def backend_choice(self) -> GameBackendChoice:
        return GameBackendChoice.DOLPHIN

    # Game Backend Stuff
    def _memory_operation(self, op: MemoryOperation, pointers: Dict[int, Optional[int]]) -> Optional[bytes]:
        op.validate_byte_sizes()

        address = op.address
        if op.offset is not None:
            if address not in pointers:
                raise MemoryOperationException(f"Invalid op: {address} is not in pointers")
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

    async def _perform_memory_operations(self, ops: List[MemoryOperation]) -> Dict[MemoryOperation, bytes]:
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

    def _ensure_hooked(self) -> bool:
        if not self.dolphin.is_hooked():
            self.patches = None
            self.dolphin.hook()

        return not self.dolphin.is_hooked()

    def _test_still_hooked(self):
        try:
            if len(self.dolphin.read_bytes(0x0, 4)) != 4:
                raise RuntimeError("Dolphin hook didn't read the correct byte count")
        except RuntimeError as e:
            self.logger.warning(f"Test read for Dolphin hook didn't work: {e}")
            self.dolphin.un_hook()

    async def update(self, dt: float):
        if not self._enabled:
            return

        if self._ensure_hooked():
            return

        if not await self._identify_game():
            self._test_still_hooked()
            return

        await self._interact_with_game(dt)

    @property
    def name(self) -> str:
        return "Dolphin"

    @property
    def current_status(self) -> GameConnectionStatus:
        if not self.dolphin.is_hooked():
            return GameConnectionStatus.Disconnected

        if self.patches is None:
            return GameConnectionStatus.UnknownGame

        if self._world is None:
            return GameConnectionStatus.TitleScreen
        elif not self.checking_for_collected_index:
            return GameConnectionStatus.TrackerOnly
        else:
            return GameConnectionStatus.InGame
