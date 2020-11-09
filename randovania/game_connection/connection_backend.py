import copy
import dataclasses
import logging
import struct
from typing import Optional, List, Dict

from randovania.game_connection.backend_choice import GameBackendChoice
from randovania.game_connection.connection_base import ConnectionBase, InventoryItem, GameConnectionStatus
from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import CurrentResources, add_resource_gain_to_current_resources
from randovania.games.game import RandovaniaGame
from randovania.games.prime import dol_patcher, default_data
from randovania.games.prime.dol_patcher import PatchesForVersion


@dataclasses.dataclass(frozen=True)
class MemoryOperation:
    address: int
    offset: Optional[int] = None
    read_byte_count: Optional[int] = None
    write_bytes: Optional[bytes] = None

    @property
    def byte_count(self) -> int:
        if self.read_byte_count is not None:
            return self.read_byte_count
        if self.write_bytes is not None:
            return len(self.write_bytes)
        return 0

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


def _add_pickup_to_resources(pickup: PickupEntry, inventory: CurrentResources) -> CurrentResources:
    return add_resource_gain_to_current_resources(
        pickup.resource_gain(inventory),
        copy.copy(inventory)
    )


class ConnectionBackend(ConnectionBase):
    patches: Optional[PatchesForVersion] = None
    _checking_for_collected_index: bool = False
    _games: Dict[RandovaniaGame, GameDescription]
    _inventory: Dict[ItemResourceInfo, InventoryItem]

    # Messages
    message_queue: List[str]
    message_cooldown: float = 0.0
    _last_message_size: int = 0

    # Multiworld
    _pickups_to_give: List[PickupEntry]
    _permanent_pickups: List[PickupEntry]

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self._games = {}
        self._inventory = {}
        self.message_queue = []
        self._pickups_to_give = []
        self._permanent_pickups = []

    @property
    def current_status(self) -> GameConnectionStatus:
        raise NotImplementedError()

    @property
    def backend_choice(self) -> GameBackendChoice:
        raise NotImplementedError()

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

    async def _perform_single_memory_operations(self, op: MemoryOperation) -> Optional[bytes]:
        result = await self._perform_memory_operations([op])
        return result[0]

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
                operation = MemoryOperation(version.build_string_address, read_byte_count=len(version.build_string))
                build_string = await self._perform_single_memory_operations(operation)
            except RuntimeError:
                return False

            if build_string == version.build_string:
                self.patches = version
                self.logger.info(f"_identify_game: identified game as {version.description}")
                return True

        return False

    async def _update_current_world(self):
        world_asset_id = await self._perform_single_memory_operations(
            MemoryOperation(self.patches.game_state_pointer,
                            offset=4,
                            read_byte_count=4)
        )
        try:
            if world_asset_id is None:
                raise KeyError()
            self._world = self.game.world_list.world_by_asset_id(struct.unpack(">I", world_asset_id)[0])
        except KeyError:
            self._world = None

    def _get_player_state_pointer(self) -> int:
        cstate_manager = self.patches.string_display.cstate_manager_global
        return cstate_manager + 0x150c

    def get_current_inventory(self) -> Dict[ItemResourceInfo, InventoryItem]:
        return self._inventory

    async def _get_inventory(self) -> Dict[ItemResourceInfo, InventoryItem]:
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

    async def _update_inventory(self, new_inventory: Dict[ItemResourceInfo, InventoryItem]):
        player_state_pointer = self._get_player_state_pointer()
        current_inventory = self.get_current_inventory()

        changed_items = {item for item in self.game.resource_database.item
                         if new_inventory[item] != current_inventory[item]}
        if not changed_items:
            return

        memory_ops = [
            MemoryOperation(
                address=player_state_pointer,
                write_bytes=struct.pack(">II", *new_inventory[item]),
                read_byte_count=8,
                offset=_powerup_offset(item.index),
            )
            for item in self.game.resource_database.item
            if item in changed_items
        ]

        # Suit Model
        dark_suit = self.game.resource_database.get_item(13)
        light_suit = self.game.resource_database.get_item(14)
        if dark_suit in changed_items or light_suit in changed_items:
            if new_inventory[light_suit].capacity > 0:
                new_suit = 2
            elif new_inventory[dark_suit].capacity > 0:
                new_suit = 1
            else:
                new_suit = 0
            memory_ops.append(MemoryOperation(
                address=player_state_pointer,
                write_bytes=struct.pack(">I", new_suit),
                offset=84,
            ))

        energy_tank = self.game.resource_database.energy_tank
        if energy_tank in changed_items:
            health_data = await self._perform_memory_operations([
                MemoryOperation(player_state_pointer, read_byte_count=4, offset=20),
                MemoryOperation(self.patches.health_capacity.base_health_capacity, read_byte_count=4),
                MemoryOperation(self.patches.health_capacity.energy_tank_capacity, read_byte_count=4),
            ])
            current_health, base_health_capacity, energy_tank_capacity = struct.unpack(">fff", b"".join(health_data))
            new_health = new_inventory[energy_tank].amount * energy_tank_capacity + base_health_capacity
            if new_inventory[energy_tank] < current_inventory[energy_tank]:
                new_health = min(new_health, current_health)

            memory_ops.append(MemoryOperation(
                address=player_state_pointer,
                write_bytes=struct.pack(">f", new_health),
                offset=20,
            ))

        # FIXME: check if the value read is what we expected, and then re-writes if needed
        result = await self._perform_memory_operations(memory_ops)
        self._inventory = new_inventory

    # Multiworld
    async def _check_for_collected_index(self):
        multiworld_magic_item = self.game.resource_database.multiworld_magic_item
        item_percentage = self.game.resource_database.item_percentage

        current_inventory = self.get_current_inventory()
        new_inventory = copy.copy(current_inventory)

        magic_inv = current_inventory[multiworld_magic_item]
        magic_capacity = magic_inv.capacity

        if magic_inv.amount > 0:
            self.logger.info(f"_check_for_collected_index: magic item was at {magic_inv.amount}/{magic_capacity}")
            magic_capacity -= magic_inv.amount
            new_inventory[multiworld_magic_item] = InventoryItem(0, magic_inv.capacity - magic_inv.amount)
            await self._emit_location_collected(magic_inv.amount - 1)

        if self._pickups_to_give or magic_capacity < len(self._permanent_pickups):
            self.logger.info(f"_check_for_collected_index: {len(self._pickups_to_give)} pickups to give, "
                             f"{len(self._permanent_pickups)} permanent pickups, magic {magic_capacity}")

            inventory_resources: CurrentResources = {
                item: inv_item.capacity
                for item, inv_item in current_inventory.items()
            }

            while self._pickups_to_give:
                inventory_resources = _add_pickup_to_resources(self._pickups_to_give.pop(), inventory_resources)

            for pickup in self._permanent_pickups[magic_capacity:]:
                inventory_resources = _add_pickup_to_resources(pickup, inventory_resources)

            for item, new_capacity in inventory_resources.items():
                if item == item_percentage:
                    continue
                old = new_inventory[item]
                delta = new_capacity - old.capacity
                new_amount = old.amount
                if delta > 0:
                    new_amount += delta
                new_inventory[item] = InventoryItem(min(new_amount, new_capacity, item.max_capacity),
                                                    min(new_capacity, item.max_capacity))

            new_inventory[multiworld_magic_item] = InventoryItem(0, len(self._permanent_pickups))

        await self._update_inventory(new_inventory)

    def send_pickup(self, pickup: PickupEntry):
        self._pickups_to_give.append(pickup)

    def set_permanent_pickups(self, pickups: List[PickupEntry]):
        self._permanent_pickups = pickups

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
        has_message = await self._perform_single_memory_operations(MemoryOperation(has_message_address,
                                                                                   read_byte_count=1))

        if has_message != b"\x00":
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
