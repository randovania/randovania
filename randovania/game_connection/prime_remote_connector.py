import copy
import dataclasses
import logging
import struct
from typing import Optional, List, Dict, Tuple, Set

from randovania.dol_patching import assembler
from randovania.game_connection.connection_base import InventoryItem, Inventory
from randovania.game_connection.memory_operation import MemoryOperationException, MemoryOperation, \
    MemoryOperatorExecutor
from randovania.game_connection.remote_connector import RemoteConnector, RemotePatch
from randovania.game_description import default_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import CurrentResources, \
    add_resource_gain_to_current_resources
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.games.prime import (all_prime_dol_patches)


@dataclasses.dataclass(frozen=True)
class DolRemotePatch(RemotePatch):
    instructions: List[assembler.BaseInstruction]


def format_received_item(item_name: str, player_name: str) -> str:
    special = {
        "Locked Power Bomb Expansion": ("Received Power Bomb Expansion from {provider_name}, "
                                        "but the main Power Bomb is required to use it."),
        "Locked Missile Expansion": ("Received Missile Expansion from {provider_name}, "
                                     "but the Missile Launcher is required to use it."),
        "Locked Seeker Launcher": ("Received Seeker Launcher from {provider_name}, "
                                   "but the Missile Launcher is required to use it."),
    }

    generic = "Received {item_name} from {provider_name}."

    return special.get(item_name, generic).format(item_name=item_name, provider_name=player_name)


def _prime1_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x24
    vector_data_offset = 0x4
    powerup_size = 0x8
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


def _echoes_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x58
    vector_data_offset = 0x4
    powerup_size = 0xc
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


def _corruption_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x50
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


class PrimeRemoteConnector(RemoteConnector):
    version: all_prime_dol_patches.BasePrimeDolVersion
    game: GameDescription
    _last_message_size: int = 0

    def __init__(self, version: all_prime_dol_patches.BasePrimeDolVersion):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)

        self.version = version
        self.game = default_database.game_description_for(version.game)

    async def is_this_version(self, executor: MemoryOperatorExecutor) -> bool:
        """Returns True if the accessible memory matches the version of this connector."""
        operation = MemoryOperation(self.version.build_string_address, read_byte_count=len(self.version.build_string))
        build_string = await executor.perform_single_memory_operation(operation)
        return build_string == self.version.build_string

    async def current_game_status(self, executor: MemoryOperatorExecutor) -> Tuple[bool, Optional[World]]:
        """
        Fetches the world the player's currently at, or None if they're not in-game.
        :param executor:
        :return: bool indicating if there's a pending `execute_remote_patches` operation.
        """

        cstate_manager_global = self.version.cstate_manager_global

        player_offset = 0
        asset_id_size = 4
        asset_id_format = ">I"

        if self.version.game == RandovaniaGame.METROID_PRIME:
            mlvl_offset = 0x84
            cplayer_offset = 0x84c

        elif self.version.game == RandovaniaGame.METROID_PRIME_ECHOES:
            mlvl_offset = 4
            cplayer_offset = 0x14fc

        elif self.version.game == RandovaniaGame.METROID_PRIME_CORRUPTION:
            mlvl_offset = 8
            asset_id_size = 8
            asset_id_format = ">Q"

            cplayer_offset = 40
            player_offset = 0x2184
        else:
            raise ValueError(f"Unknown game: {self.version.game}")

        memory_ops = [
            MemoryOperation(self.version.game_state_pointer, offset=mlvl_offset, read_byte_count=asset_id_size),
            MemoryOperation(cstate_manager_global + 0x2, read_byte_count=1),
            MemoryOperation(cstate_manager_global + cplayer_offset, offset=player_offset, read_byte_count=4),
        ]
        results = await executor.perform_memory_operations(memory_ops)

        world_asset_id = results[memory_ops[0]]
        pending_op_byte = results[memory_ops[1]]
        player_vtable_bytes = results[memory_ops[2]]

        has_pending_op = pending_op_byte != b"\x00"

        if self.version.game == RandovaniaGame.METROID_PRIME_CORRUPTION:
            # TODO: Corruption has an extra indirection
            player_vtable = self.version.cplayer_vtable
        else:
            player_vtable = struct.unpack(">I", player_vtable_bytes)[0]

        try:
            new_world = self.game.world_list.world_by_asset_id(struct.unpack(asset_id_format, world_asset_id)[0])
        except KeyError:
            new_world = None

        if player_vtable != self.version.cplayer_vtable:
            new_world = None

        return has_pending_op, new_world

    async def _memory_op_for_items(self, executor: MemoryOperatorExecutor, items: List[ItemResourceInfo],
                                   ) -> List[MemoryOperation]:
        if self.version.game == RandovaniaGame.METROID_PRIME:
            offset_func = _prime1_powerup_offset
            player_state_pointer = int.from_bytes(await executor.perform_single_memory_operation(MemoryOperation(
                address=self.version.cstate_manager_global + 0x8b8,
                read_byte_count=4,
            )), "big")

        elif self.version.game == RandovaniaGame.METROID_PRIME_ECHOES:
            offset_func = _echoes_powerup_offset
            player_state_pointer = self.version.cstate_manager_global + 0x150c

        elif self.version.game == RandovaniaGame.METROID_PRIME_CORRUPTION:
            offset_func = _corruption_powerup_offset
            player_state_pointer = int.from_bytes(await executor.perform_single_memory_operation(MemoryOperation(
                address=self.version.game_state_pointer,
                read_byte_count=4,
            )), "big") + 36
        else:
            raise ValueError(f"Unknown game: {self.version.game}")

        return [
            MemoryOperation(
                address=player_state_pointer,
                offset=offset_func(item.index),
                read_byte_count=8,
            )
            for item in items
        ]

    async def get_inventory(self, executor: MemoryOperatorExecutor) -> Inventory:
        """Fetches the inventory represented by the given game memory."""

        memory_ops = await self._memory_op_for_items(executor, [
            item
            for item in self.game.resource_database.item
            if item.index < 1000
        ])
        ops_result = await executor.perform_memory_operations(memory_ops)

        inventory = {}
        for item, memory_op in zip(self.game.resource_database.item, memory_ops):
            inv = InventoryItem(*struct.unpack(">II", ops_result[memory_op]))
            if (inv.amount > inv.capacity or inv.capacity > item.max_capacity) and (
                    item != self.game.resource_database.multiworld_magic_item):
                raise MemoryOperationException(f"Received {inv} for {item.long_name}, which is an invalid state.")
            inventory[item] = inv

        return inventory

    async def known_collected_locations(self, executor: MemoryOperatorExecutor,
                                        ) -> Tuple[Set[PickupIndex], List[DolRemotePatch]]:
        """Fetches pickup indices that have been collected.
        The list may return less than all collected locations, depending on implementation details.
        This function also returns a list of remote patches that must be performed via `execute_remote_patches`.
        """
        multiworld_magic_item = self.game.resource_database.multiworld_magic_item
        if multiworld_magic_item is None:
            return set(), []

        memory_ops = await self._memory_op_for_items(executor, [multiworld_magic_item])
        op_result = await executor.perform_single_memory_operation(*memory_ops)

        magic_inv = InventoryItem(*struct.unpack(">II", op_result))
        if magic_inv.amount > 0:
            self.logger.info(f"magic item was at {magic_inv.amount}/{magic_inv.capacity}")
            locations = {PickupIndex(magic_inv.amount - 1)}
            patches = [DolRemotePatch([], all_prime_dol_patches.adjust_item_amount_and_capacity_patch(
                self.version.powerup_functions,
                self.game.game,
                multiworld_magic_item.index,
                -magic_inv.amount,
            ))]
            return locations, patches
        else:
            return set(), []

    async def find_missing_remote_pickups(self, executor: MemoryOperatorExecutor, inventory: Inventory,
                                          remote_pickups: List[Tuple[str, PickupEntry]],
                                          ) -> Tuple[List[RemotePatch], bool]:
        """
        Determines if any of the remote_pickups needs to be written to executor.
        :param executor:
        :param inventory: The player's inventory, as given by `get_inventory`.
        :param remote_pickups: Ordered list of pickups sent from other players, with the name of the player.
        :return: List of patches to give one missing pickup. A bool indicating that a message will be displayed.
        """
        multiworld_magic_item = self.game.resource_database.multiworld_magic_item
        magic_inv = inventory.get(multiworld_magic_item)
        if magic_inv is None or magic_inv.amount > 0 or magic_inv.capacity >= len(remote_pickups):
            return [], False

        item_patches, message = await self._patches_for_pickup(*remote_pickups[magic_inv.capacity])
        self.logger.info(f"{len(remote_pickups)} permanent pickups, magic {magic_inv.capacity}. "
                         f"Next pickup: {message}")

        patches = [DolRemotePatch([], item_patch) for item_patch in item_patches]
        patches.append(DolRemotePatch([], all_prime_dol_patches.increment_item_capacity_patch(
            self.version.powerup_functions,
            self.game.game,
            multiworld_magic_item.index,
        )))
        patches.append(DolRemotePatch(
            [self._write_string_to_game_buffer(message)],
            all_prime_dol_patches.call_display_hud_patch(self.version.string_display),
        ))

        return patches, True

    async def execute_remote_patches(self, executor: MemoryOperatorExecutor, patches: List[DolRemotePatch]) -> None:
        """
        Executes a given set of patches on the given memory operator. Should only be called if the bool returned by
        `current_game_status` is False, but validation of this fact is implementation-dependant.
        :param executor:
        :param patches: List of patches to execute
        :return:
        """
        memory_operations = []
        for patch in patches:
            memory_operations.extend(patch.memory_operations)

        patch_address, patch_bytes = all_prime_dol_patches.create_remote_execution_body(
            self.version.string_display,
            [instruction
             for patch in patches
             for instruction in patch.instructions],
        )
        memory_operations.extend([
            MemoryOperation(patch_address, write_bytes=patch_bytes),
            MemoryOperation(self.version.cstate_manager_global + 0x2, write_bytes=b"\x01"),
        ])
        self.logger.debug(f"Performing {len(memory_operations)} ops with {len(patches)} patches")
        await executor.perform_memory_operations(memory_operations)

    def _resources_to_give_for_pickup(self, pickup: PickupEntry, inventory: Inventory):
        inventory_resources: CurrentResources = {
            item: inv_item.capacity
            for item, inv_item in inventory.items()
        }
        conditional = pickup.conditional_for_resources(inventory_resources)
        if conditional.name is not None:
            item_name = conditional.name
        else:
            item_name = pickup.name

        resources_to_give = {}

        if pickup.respects_lock and not pickup.unlocks_resource and (
                pickup.resource_lock is not None and inventory_resources.get(pickup.resource_lock.locked_by, 0) == 0):
            pickup_resources = list(pickup.resource_lock.convert_gain(conditional.resources))
            item_name = f"Locked {item_name}"
        else:
            pickup_resources = conditional.resources

        add_resource_gain_to_current_resources(pickup_resources, inventory_resources)
        add_resource_gain_to_current_resources(pickup_resources, resources_to_give)
        add_resource_gain_to_current_resources(pickup.conversion_resource_gain(inventory_resources),
                                               resources_to_give)

        # Ignore item% for received items
        if self.game.resource_database.item_percentage is not None:
            resources_to_give.pop(self.game.resource_database.item_percentage, None)

        return item_name, resources_to_give

    async def _patches_for_pickup(self, provider_name: str, pickup: PickupEntry, inventory: Inventory):
        item_name, resources_to_give = self._resources_to_give_for_pickup(pickup, inventory)

        self.logger.debug(f"Resource changes for {pickup.name} from {provider_name}: {resources_to_give}")
        patches = [
            all_prime_dol_patches.adjust_item_amount_and_capacity_patch(
                self.version.powerup_functions, self.game.game,
                item.index, delta,
            )
            for item, delta in resources_to_give.items()
        ]
        return patches, format_received_item(item_name, provider_name)

    def _write_string_to_game_buffer(self, message: str) -> MemoryOperation:
        if self.version.game == RandovaniaGame.METROID_PRIME:
            message = "&just=center;" + message

        overhead_size = 6  # 2 bytes for an extra char to differentiate sizes
        encoded_message = message.encode("utf-16_be")[:self.version.string_display.max_message_size - overhead_size]

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

        return MemoryOperation(self.version.string_display.message_receiver_string_ref,
                               write_bytes=encoded_message)
