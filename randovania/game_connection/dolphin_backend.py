from typing import List, Optional

import dolphin_memory_engine

from randovania.game_connection.connection_backend import ConnectionBackend, MemoryOperation
from randovania.game_connection.connection_base import ConnectionStatus
from randovania.game_description.world import World


class DolphinBackend(ConnectionBackend):
    _world: Optional[World] = None

    def __init__(self):
        super().__init__()
        self.dolphin = dolphin_memory_engine



    @property
    def lock_identifier(self) -> Optional[str]:
        return "randovania-dolphin-backend"

    # Game Backend Stuff
    def _memory_operation(self, op: MemoryOperation) -> Optional[bytes]:
        op.validate_byte_sizes()

        address = op.address
        if op.offset is not None:
            try:
                address = self.dolphin.follow_pointers(address, [op.offset])
            except RuntimeError:
                return None

        result = None
        if op.read_byte_count is not None:
            result = self.dolphin.read_bytes(address, op.read_byte_count)
        if op.write_bytes is not None:
            self.dolphin.write_bytes(address, op.write_bytes)
        return result

    async def _perform_memory_operations(self, ops: List[MemoryOperation]) -> List[Optional[bytes]]:
        return [
            self._memory_operation(op)
            for op in ops
        ]

    def _ensure_hooked(self) -> bool:
        if not self.dolphin.is_hooked():
            self.patches = None
            self.dolphin.hook()

        return not self.dolphin.is_hooked()

    def _test_still_hooked(self):
        try:
            if len(self.dolphin.read_bytes(0x0, 4)) != 4:
                raise RuntimeError("Dolphin hook didn't read the correct byte count")
        except RuntimeError:
            self.dolphin.un_hook()

    async def update(self, dt: float):
        if self._ensure_hooked():
            return

        if not await self._identify_game():
            self._test_still_hooked()
            return

        await self._send_message_from_queue(dt)

        await self._update_current_world()
        if self._world is not None:
            self._inventory = await self._get_inventory()
            if self.checking_for_collected_index:
                await self._check_for_collected_index()

    @property
    def name(self) -> str:
        return "Dolphin"

    @property
    def current_status(self) -> ConnectionStatus:
        if not self.dolphin.is_hooked():
            return ConnectionStatus.Disconnected

        if self.patches is None:
            return ConnectionStatus.UnknownGame

        if self._world is None:
            return ConnectionStatus.TitleScreen
        elif not self.checking_for_collected_index:
            return ConnectionStatus.TrackerOnly
        else:
            return ConnectionStatus.InGame
