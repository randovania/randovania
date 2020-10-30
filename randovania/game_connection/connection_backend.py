import dataclasses
import logging
import struct
from typing import Optional, List, Dict, NamedTuple

from randovania.game_connection.connection_base import ConnectionBase, InventoryItem
from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.games.prime import dol_patcher, default_data
from randovania.games.prime.dol_patcher import PatchesForVersion


@dataclasses.dataclass(frozen=True)
class MemoryOperation:
    address: int
    offset: Optional[int] = None
    read_byte_count: Optional[int] = None
    write_bytes: Optional[bytes] = None

    def validate_byte_sizes(self):
        if self.read_byte_count is not None and self.read_byte_count > 60:
            raise ValueError(f"Attempting to read {self.read_byte_count} bytes, which is more than the allowed 60.")

        if (self.write_bytes is not None
                and self.read_byte_count is not None
                and len(self.write_bytes) != self.read_byte_count):
            raise ValueError(f"Attempting to read {self.read_byte_count} bytes while writing {len(self.write_bytes)}.")


def _powerup_offset(item_index: int) -> int:
    powerups_offset = 0x58
    vector_data_offset = 0x4
    powerup_size = 0xc
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


class ConnectionBackend(ConnectionBase):
    patches: Optional[PatchesForVersion] = None
    _games: Dict[RandovaniaGame, GameDescription]

    # Messages
    message_queue: List[str]
    message_cooldown: float = 0.0
    _last_message_size: int = 0

    _checking_for_collected_index: bool = False

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self._games = {}
        self.message_queue = []

    @property
    def name(self) -> str:
        raise NotImplementedError()

    async def update(self, dt: float):
        raise NotImplementedError()

    @property
    def lock_identifier(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def checking_for_collected_index(self):
        return self._checking_for_collected_index

    @checking_for_collected_index.setter
    def checking_for_collected_index(self, value):
        self._checking_for_collected_index = value

    # Game Backend Stuff
    async def _perform_memory_operations(self, ops: List[MemoryOperation]) -> List[Optional[bytes]]:
        raise NotImplementedError()

    @property
    def game(self) -> GameDescription:
        game_enum = self.patches.game
        if game_enum not in self._games:
            self._games[game_enum] = data_reader.decode_data(default_data.read_json_then_binary(game_enum)[1])
        return self._games[game_enum]

    async def _identify_game(self) -> bool:
        if self.patches is not None:
            return True

        for version in dol_patcher.ALL_VERSIONS_PATCHES:
            try:
                # We're reading these build strings separately because combining would go above the maximum size allowed
                # for read operations
                read_result = await self._perform_memory_operations([
                    MemoryOperation(version.build_string_address,
                                    read_byte_count=len(version.build_string))])
                build_string = read_result[0]
            except RuntimeError:
                return False

            if build_string == version.build_string:
                self.patches = version
                self.logger.info(f"_identify_game: identified game as {version.description}")
                return True

        return False

    def _get_player_state_pointer(self) -> int:
        cstate_manager = self.patches.string_display.cstate_manager_global
        return cstate_manager + 0x150c

    async def get_inventory(self) -> Dict[ItemResourceInfo, InventoryItem]:
        player_state_pointer = self._get_player_state_pointer()

        memory_ops = [
            MemoryOperation(
                address=player_state_pointer,
                read_byte_count=8,
                offset=_powerup_offset(item.index),
            )
            for item in self.game.resource_database.item
        ]

        ops_result = await self._perform_memory_operations(memory_ops)

        inventory = {}
        for item, memory_result in zip(self.game.resource_database.item, ops_result):
            inventory[item] = InventoryItem(*struct.unpack(">II", memory_result))

        return inventory

    # Display Message

    def display_message(self, message: str):
        self.logger.info(f"Queueing message '{message}'. "
                         f"Queue has {len(self.message_queue)} elements and "
                         f"current cooldown is {self.message_cooldown}")
        self.message_queue.append(message)

    async def _send_message_from_queue(self, dt: float):
        # If there's no messages, don't bother
        if not self.message_queue:
            return

        has_message_address = self.patches.string_display.cstate_manager_global + 0x2

        # There's already a message pending, stop
        has_message_result = await self._perform_memory_operations([
            MemoryOperation(has_message_address, read_byte_count=1),
        ])

        if has_message_result[0] != b"\x00":
            self.logger.info("_send_message_from_queue: game already has a pending message")
            return

        self.message_cooldown = max(self.message_cooldown - dt, 0.0)

        # There's a cooldown for next message!
        if self.message_cooldown > 0:
            return

        encoded_message = self.message_queue.pop(0).encode("utf-16_be")[:self.patches.string_display.max_message_size]

        # The game doesn't handle very well a string at the same address with same size being
        # displayed multiple times
        if len(encoded_message) == self._last_message_size:
            encoded_message += b'\x00 '

        self._last_message_size = len(encoded_message)
        await self._perform_memory_operations([
            # The message string
            MemoryOperation(self.patches.string_display.message_receiver_string_ref,
                            write_bytes=encoded_message + b"\x00\x00"),

            # Notify game to display message
            MemoryOperation(has_message_address, write_bytes=b"\x01"),
        ])
        self.message_cooldown = 4

        self.logger.info("_send_message_from_queue: sent a message to the game")
