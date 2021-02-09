import copy
import dataclasses
import logging
import struct
from typing import Optional, List, Dict, Tuple

from randovania.dol_patching import assembler
from randovania.game_connection.backend_choice import GameBackendChoice
from randovania.game_connection.connection_base import ConnectionBase, InventoryItem, GameConnectionStatus
from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import CurrentResources, \
    add_resource_gain_to_current_resources
from randovania.game_description.world import World
from randovania.games.game import RandovaniaGame
from randovania.games.prime import dol_patcher, default_data, all_prime_dol_patches
from randovania.games.prime.all_prime_dol_patches import BasePrimeDolVersion


class MemoryOperationException(Exception):
    pass


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
        if (self.write_bytes is not None
                and self.read_byte_count is not None
                and len(self.write_bytes) != self.read_byte_count):
            raise ValueError(f"Attempting to read {self.read_byte_count} bytes while writing {len(self.write_bytes)}.")

    def __str__(self):
        address_text = f"0x{self.address:08x}"
        if self.offset is not None:
            address_text = f"*{address_text} {self.offset:+05x}"

        operation_pretty = []
        if self.read_byte_count is not None:
            operation_pretty.append(f"read {self.read_byte_count} bytes")
        if self.write_bytes is not None:
            operation_pretty.append(f"write {self.write_bytes.hex()}")

        return f"At {address_text}, {' and '.join(operation_pretty)}"


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


def _capacity_for(item: ItemResourceInfo,
                  changed_items: Dict[ItemResourceInfo, InventoryItem],
                  inventory: Dict[ItemResourceInfo, InventoryItem]):
    if item in changed_items:
        return changed_items[item].capacity
    elif item in inventory:
        return inventory[item].capacity
    else:
        return 0


class ConnectionBackend(ConnectionBase):
    patches: Optional[BasePrimeDolVersion] = None
    _checking_for_collected_index: bool = False
    _games: Dict[RandovaniaGame, GameDescription]
    _inventory: Dict[ItemResourceInfo, InventoryItem]
    _enabled: bool = True

    # Detected Game
    _world: Optional[World] = None
    _last_world: Optional[World] = None

    # Messages
    message_queue: List[str]
    message_cooldown: float = 0.0
    _last_message_size: int = 0

    # Multiworld
    _permanent_pickups: List[Tuple[str, PickupEntry]]

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)

        self._games = {}
        self._inventory = {}
        self.message_queue = []
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

    def set_connection_enabled(self, value: bool):
        self._enabled = value
        if not value:
            self.patches = None

    # Game Backend Stuff
    async def _perform_memory_operations(self, ops: List[MemoryOperation]) -> Dict[MemoryOperation, bytes]:
        raise NotImplementedError()

    async def _perform_single_memory_operations(self, op: MemoryOperation) -> Optional[bytes]:
        result = await self._perform_memory_operations([op])
        return result.get(op)

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
            except (RuntimeError, MemoryOperationException) as e:
                self.logger.debug(f"unable to load bytes at {version.build_string_address}: {e}")
                return False

            if build_string == version.build_string:
                self.patches = version
                self.logger.info(f"identified game as {version.description}")
                return True

        return False

    async def _fetch_game_status(self):
        cstate_manager_global = self.patches.cstate_manager_global
        self._last_world = self._world

        player_vtable = 0
        try:
            memory_ops = [
                MemoryOperation(self.patches.game_state_pointer, offset=4, read_byte_count=4),
                MemoryOperation(cstate_manager_global + 0x2, read_byte_count=1),
                MemoryOperation(cstate_manager_global + 0x14fc, offset=0, read_byte_count=4),
            ]
            results = await self._perform_memory_operations(memory_ops)

            world_asset_id = results[memory_ops[0]]
            pending_op_byte = results[memory_ops[1]]
            player_vtable_bytes = results[memory_ops[2]]

            self._has_pending_op = pending_op_byte != b"\x00"
            player_vtable = struct.unpack(">I", player_vtable_bytes)[0]
            new_world = self.game.world_list.world_by_asset_id(struct.unpack(">I", world_asset_id)[0])

        except (KeyError, MemoryOperationException) as e:
            self.logger.debug("Failed to update world: %s", e)
            new_world = None

        if new_world != self._last_world:
            self.logger.info(
                f"Detected world as {new_world.name if new_world else 'None'}. "
                f"Player vtable: {hex(player_vtable)}; Expected vtable: {hex(self.patches.cplayer_vtable)}")
            if player_vtable == self.patches.cplayer_vtable or new_world is None:
                self._world = new_world

    def get_current_inventory(self) -> Dict[ItemResourceInfo, InventoryItem]:
        return self._inventory

    async def _get_inventory(self) -> Dict[ItemResourceInfo, InventoryItem]:
        player_state_pointer = self.patches.cstate_manager_global + 0x150c

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
        for item, memory_op in zip(self.game.resource_database.item, memory_ops):
            inv = InventoryItem(*struct.unpack(">II", ops_result[memory_op]))
            if inv.amount > inv.capacity or inv.capacity > item.max_capacity:
                raise MemoryOperationException(f"Received {inv} for {item.long_name}, which is an invalid state.")
            inventory[item] = inv

        return inventory

    # Multiworld
    async def _update_magic_item(self):
        multiworld_magic_item = self.game.resource_database.multiworld_magic_item
        patches = []

        magic_inv = self._inventory[multiworld_magic_item]
        magic_capacity = magic_inv.capacity
        if magic_inv.amount > 0:
            self.logger.info(f"magic item was at {magic_inv.amount}/{magic_capacity}")
            magic_capacity -= magic_inv.amount
            await self._emit_location_collected(magic_inv.amount - 1)
            patches.append(all_prime_dol_patches.adjust_item_amount_and_capacity_patch(self.patches.powerup_functions,
                                                                                       multiworld_magic_item.index,
                                                                                       -magic_inv.amount))

        # Only attempt to give the next item if outside cooldown
        message = None
        if self.message_cooldown <= 0 and magic_capacity < len(self._permanent_pickups):
            item_patches, message = await self._patches_for_pickup(*self._permanent_pickups[magic_capacity])
            self.logger.info(f"{len(self._permanent_pickups)} permanent pickups, magic {magic_capacity}. "
                             f"Next pickup: {message}")

            patches.extend(item_patches)
            patches.append(all_prime_dol_patches.increment_item_capacity_patch(self.patches.powerup_functions,
                                                                               multiworld_magic_item.index))

        if patches:
            await self._execute_remote_patches(patches, message)

    async def _execute_remote_patches(self, patches: List[List[assembler.BaseInstruction]], message: Optional[str]):
        memory_operations = []

        if message is not None:
            self.message_cooldown = 4
            patches.append(all_prime_dol_patches.call_display_hud_patch(self.patches.string_display))
            memory_operations.append(self._write_string_to_game_buffer(message))

        patch_address, patch_bytes = all_prime_dol_patches.create_remote_execution_body(
            self.patches.string_display,
            [instruction for patch in patches for instruction in patch],
        )
        memory_operations.extend([
            MemoryOperation(patch_address, write_bytes=patch_bytes),
            MemoryOperation(self.patches.cstate_manager_global + 0x2, write_bytes=b"\x01"),
        ])
        await self._perform_memory_operations(memory_operations)

    async def _patches_for_pickup(self, provider_name: str, pickup: PickupEntry):
        inventory_resources: CurrentResources = {
            item: inv_item.capacity
            for item, inv_item in self._inventory.items()
        }
        conditional = pickup.conditional_for_resources(inventory_resources)
        if conditional.name is not None:
            item_name = conditional.name
        else:
            item_name = pickup.name

        resources_to_give = {}
        add_resource_gain_to_current_resources(conditional.resources, inventory_resources)
        add_resource_gain_to_current_resources(conditional.resources, resources_to_give)
        add_resource_gain_to_current_resources(pickup.conversion_resource_gain(inventory_resources),
                                               resources_to_give)

        # Ignore item% for received items
        resources_to_give.pop(self.game.resource_database.item_percentage, None)

        patches = [
            all_prime_dol_patches.adjust_item_amount_and_capacity_patch(self.patches.powerup_functions,
                                                                        item.index, delta)
            for item, delta in resources_to_give.items()
        ]
        return patches, f"Received {item_name} from {provider_name}."

    def set_permanent_pickups(self, pickups: List[Tuple[str, PickupEntry]]):
        self._permanent_pickups = pickups

    def _write_string_to_game_buffer(self, message: str) -> MemoryOperation:
        overhead_size = 6  # 2 bytes for an extra char to differentiate sizes
        encoded_message = message.encode("utf-16_be")[:self.patches.string_display.max_message_size - overhead_size]

        # The game doesn't handle very well a string at the same address with same size being
        # displayed multiple times
        if len(encoded_message) == self._last_message_size:
            encoded_message += b'\x00 '
        self._last_message_size = len(encoded_message)

        # Add the null terminator
        encoded_message += b"\x00\x00"
        if len(encoded_message) & 3:
            # Ensure the size is a multiple of 4
            num_to_align = (len(encoded_message) | 3) - len(encoded_message) + 1
            encoded_message += b"\x00" * num_to_align

        return MemoryOperation(self.patches.string_display.message_receiver_string_ref,
                               write_bytes=encoded_message)

    async def update_current_inventory(self):
        self._inventory = await self._get_inventory()

    async def _interact_with_game(self, dt):
        await self._fetch_game_status()
        if self._world is not None:
            try:
                self._inventory = await self._get_inventory()
                if not self._has_pending_op:
                    self.message_cooldown = max(self.message_cooldown - dt, 0.0)
                    await self._update_magic_item()

            except MemoryOperationException as e:
                self.logger.warning(f"Unable to perform memory operations: {e}")
                self._world = None
