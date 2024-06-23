from __future__ import annotations

import dataclasses
import logging
import struct
import uuid
from typing import TYPE_CHECKING

from open_prime_rando.dol_patching import all_prime_dol_patches
from retro_data_structures.game_check import Game as RDSGame

from randovania.game_connection.connector.remote_connector import (
    PickupEntryWithOwner,
    PlayerLocationEvent,
    RemoteConnector,
)
from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_connection.executor.memory_operation import (
    MemoryOperation,
    MemoryOperationException,
    MemoryOperationExecutor,
)
from randovania.game_description import default_database
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import INVALID_UUID
from randovania.lib.infinite_timer import InfiniteTimer

if TYPE_CHECKING:
    from ppc_asm import assembler

    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo


@dataclasses.dataclass(frozen=True)
class DolRemotePatch:
    memory_operations: list[MemoryOperation]
    instructions: list[assembler.BaseInstruction]


_RDS_TO_RDV_GAME = {
    RDSGame.PRIME: RandovaniaGame.METROID_PRIME,
    RDSGame.ECHOES: RandovaniaGame.METROID_PRIME_ECHOES,
    RDSGame.CORRUPTION: RandovaniaGame.METROID_PRIME_CORRUPTION,
}


class PrimeRemoteConnector(RemoteConnector):
    version: all_prime_dol_patches.BasePrimeDolVersion
    game: GameDescription
    _last_message_size: int = 0
    _last_emitted_region: Region | None = None
    executor: MemoryOperationExecutor
    remote_pickups: tuple[PickupEntryWithOwner, ...]
    message_cooldown: float = 0.0
    last_inventory: Inventory = {}
    _dt: float = 2.5

    def __init__(self, version: all_prime_dol_patches.BasePrimeDolVersion, executor: MemoryOperationExecutor):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)

        self.executor = executor
        self.version = version
        self.game = default_database.game_description_for(_RDS_TO_RDV_GAME[version.game])
        self.remote_pickups = ()
        self.pending_messages = []

        self._timer = InfiniteTimer(self.update, self._dt)

    @property
    def game_enum(self) -> RandovaniaGame:
        return self.game.game

    def description(self):
        return f"{self.game_enum.long_name}: {self.version.description}"

    async def check_for_world_uid(self) -> bool:
        """Returns True if the accessible memory matches the version of this connector."""
        operation = MemoryOperation(self.version.build_string_address, read_byte_count=len(self.version.build_string))
        build_string = await self.executor.perform_single_memory_operation(operation)
        world_uid = build_string[6 : 6 + 16]
        expected = bytearray(self.version.build_string)
        expected[6 : 6 + 16] = world_uid
        if build_string == expected:
            if build_string == self.version.build_string:
                # Game exported with old version, act as if it's invalid uuid
                self._layout_uuid = INVALID_UUID
            else:
                self._layout_uuid = uuid.UUID(bytes=world_uid)
            return True
        else:
            return False

    def _asset_id_format(self):
        """struct.unpack format string for decoding an asset id"""
        raise NotImplementedError

    def world_by_asset_id(self, asset_id: int) -> Region | None:
        for region in self.game.region_list.regions:
            if region.extra["asset_id"] == asset_id:
                return region

    def _current_status_world(self, world_asset_id: bytes | None, vtable_bytes: bytes | None) -> Region | None:
        """
        Helper for `current_game_status`. Calculates the current World based on raw world_asset_id and vtable pointer.
        :param world_asset_id: Bytes for the current world asset id. Might be None.
        :param vtable_bytes: Bytes for a CPlayer vtable pointer. Might be None.
        :return:
        """

        if world_asset_id is None:
            return None

        if self.version.cplayer_vtable is not None:
            if vtable_bytes is None:
                return None

            player_vtable = struct.unpack(">I", vtable_bytes)[0]
            if player_vtable != self.version.cplayer_vtable:
                return None

        asset_id = struct.unpack(self._asset_id_format(), world_asset_id)[0]
        return self.world_by_asset_id(asset_id)

    async def current_game_status(self) -> tuple[bool, Region | None]:
        raise NotImplementedError

    async def _memory_op_for_items(
        self,
        items: list[ItemResourceInfo],
    ) -> list[MemoryOperation]:
        raise NotImplementedError

    @property
    def multiworld_magic_item(self) -> ItemResourceInfo:
        raise NotImplementedError

    async def get_inventory(self) -> Inventory:
        """Fetches the inventory represented by the given game memory."""

        memory_ops = await self._memory_op_for_items(
            [item for item in self.game.resource_database.item if item.extra["item_id"] < 1000]
        )
        ops_result = await self.executor.perform_memory_operations(memory_ops)

        inventory = {}
        for item, memory_op in zip(self.game.resource_database.item, memory_ops):
            inv = InventoryItem(*struct.unpack(">II", ops_result[memory_op]))
            if (inv.amount > inv.capacity or inv.capacity > item.max_capacity) and (item != self.multiworld_magic_item):
                raise MemoryOperationException(f"Received {inv} for {item.long_name}, which is an invalid state.")
            inventory[item] = inv

        return Inventory(inventory)

    async def known_collected_locations(self) -> set[PickupIndex]:
        """Fetches pickup indices that have been collected.
        The list may return less than all collected locations, depending on implementation details.
        This function also returns a list of remote patches that must be performed via `execute_remote_patches`.
        """
        multiworld_magic_item = self.multiworld_magic_item
        if multiworld_magic_item is None:
            return set()

        memory_ops = await self._memory_op_for_items([multiworld_magic_item])
        op_result = await self.executor.perform_single_memory_operation(*memory_ops)

        magic_inv = InventoryItem(*struct.unpack(">II", op_result))
        if magic_inv.amount > 0:
            self.logger.info(f"magic item was at {magic_inv.amount}/{magic_inv.capacity}")
            locations = {PickupIndex(magic_inv.amount - 1)}
            patches = [
                DolRemotePatch(
                    [],
                    all_prime_dol_patches.adjust_item_amount_and_capacity_patch(
                        self.version.powerup_functions,
                        self.version.game,
                        multiworld_magic_item.extra["item_id"],
                        -magic_inv.amount,
                    ),
                )
            ]
            await self.execute_remote_patches(patches)
            return locations
        else:
            return set()

    async def receive_remote_pickups(
        self,
        inventory: Inventory,
        remote_pickups: tuple[PickupEntryWithOwner, ...],
    ) -> bool:
        """Returns true if an operation was sent."""

        in_cooldown = self.message_cooldown > 0.0
        multiworld_magic_item = self.multiworld_magic_item
        magic_inv = inventory.get(multiworld_magic_item)
        if magic_inv is None or magic_inv.amount > 0 or magic_inv.capacity >= len(remote_pickups) or in_cooldown:
            return False

        provider_name, pickup = remote_pickups[magic_inv.capacity]
        item_patches, message = await self._patches_for_pickup(provider_name, pickup, inventory)
        self.logger.info(f"{len(remote_pickups)} permanent pickups, magic {magic_inv.capacity}. Next pickup: {message}")

        patches = [DolRemotePatch([], item_patch) for item_patch in item_patches]
        patches.append(
            DolRemotePatch(
                [],
                all_prime_dol_patches.increment_item_capacity_patch(
                    self.version.powerup_functions,
                    self.version.game,
                    multiworld_magic_item.extra["item_id"],
                ),
            )
        )
        patches.append(self._dol_patch_for_hud_message(message))

        await self.execute_remote_patches(patches)
        self.message_cooldown = 4.0
        return True

    async def execute_remote_patches(self, patches: list[DolRemotePatch]) -> None:
        """
        Executes a given set of patches on the given memory operator. Should only be called if the bool returned by
        `current_game_status` is False, but validation of this fact is implementation-dependant.
        :param patches: List of patches to execute
        :return:
        """
        memory_operations = []
        for patch in patches:
            memory_operations.extend(patch.memory_operations)

        patch_address, patch_bytes = all_prime_dol_patches.create_remote_execution_body(
            self.version.game,
            self.version.string_display,
            [instruction for patch in patches for instruction in patch.instructions],
        )
        memory_operations.extend(
            [
                MemoryOperation(patch_address, write_bytes=patch_bytes),
                MemoryOperation(self.version.cstate_manager_global + 0x2, write_bytes=b"\x01"),
            ]
        )
        self.logger.debug(f"Performing {len(memory_operations)} ops with {len(patches)} patches")
        await self.executor.perform_memory_operations(memory_operations)

    def _resources_to_give_for_pickup(
        self,
        pickup: PickupEntry,
        inventory: Inventory,
    ) -> tuple[str, ResourceCollection]:
        inventory_resources = ResourceCollection.with_database(self.game.resource_database)
        inventory_resources.add_resource_gain(inventory.as_resource_gain())
        conditional = pickup.conditional_for_resources(inventory_resources)
        if conditional.name is not None:
            item_name = conditional.name
        else:
            item_name = pickup.name

        resources_to_give = ResourceCollection.with_database(self.game.resource_database)

        if (
            pickup.respects_lock
            and not pickup.unlocks_resource
            and (pickup.resource_lock is not None and inventory_resources[pickup.resource_lock.locked_by] == 0)
        ):
            pickup_resources = list(pickup.resource_lock.convert_gain(conditional.resources))
            item_name = f"Locked {item_name}"
        else:
            pickup_resources = conditional.resources

        inventory_resources.add_resource_gain(pickup_resources)
        resources_to_give.add_resource_gain(pickup_resources)
        resources_to_give.add_resource_gain(pickup.conversion_resource_gain(inventory_resources))

        return item_name, resources_to_give

    async def _patches_for_pickup(
        self, provider_name: str, pickup: PickupEntry, inventory: Inventory
    ) -> tuple[list[list[assembler.BaseInstruction]], str]:
        raise NotImplementedError

    def _write_string_to_game_buffer(self, message: str) -> MemoryOperation:
        overhead_size = 6  # 2 bytes for an extra char to differentiate sizes
        encoded_message = message.encode("utf-16_be")[: self.version.string_display.max_message_size - overhead_size]

        # The game doesn't handle very well a string at the same address with same size being
        # displayed multiple times
        if len(encoded_message) == self._last_message_size:
            encoded_message += b"\x00 "
        self._last_message_size = len(encoded_message)

        # Add the null terminator
        encoded_message += b"\x00\x00"
        if len(encoded_message) & 3:
            # Ensure the size is a multiple of 4
            num_to_align = (len(encoded_message) | 3) - len(encoded_message) + 1
            encoded_message += b"\x00" * num_to_align

        return MemoryOperation(self.version.string_display.message_receiver_string_ref, write_bytes=encoded_message)

    def _dol_patch_for_hud_message(self, message: str) -> DolRemotePatch:
        return DolRemotePatch(
            [self._write_string_to_game_buffer(message)],
            all_prime_dol_patches.call_display_hud_patch(self.version.string_display),
        )

    async def update(self):
        try:
            if isinstance(self.executor, DolphinExecutor):
                current_uid = self._layout_uuid
                if not await self.check_for_world_uid() or current_uid != self._layout_uuid:
                    self.logger.warning("Dolphin changed games too quickly")
                    self.executor.disconnect()
                    return

            has_pending_op, region = await self.current_game_status()
            if region != self._last_emitted_region:
                self.logger.debug("Region changed from last emitted %s", region)
                self.PlayerLocationChanged.emit(PlayerLocationEvent(region, None))
            self._last_emitted_region = region

            if region is not None:
                await self.update_current_inventory()
                if not has_pending_op:
                    self.message_cooldown = max(self.message_cooldown - self._dt, 0.0)
                    has_pending_op = await self._multiworld_interaction()
                    if not has_pending_op:
                        await self._send_next_pending_message()

        except MemoryOperationException as e:
            # A memory operation failing is expected only when the socket is lost or dolphin is closed
            # It should automatically disconnect the executor, so fail loudly if that's not the case
            if self.executor.is_connected():
                self.executor.disconnect()
                self.logger.debug("Disconnecting due to an exception: %s", str(e))

        finally:
            if self.is_disconnected():
                self.logger.info("Finishing connector")
                self._timer.stop()

    async def update_current_inventory(self):
        new_inventory = await self.get_inventory()
        if new_inventory != self.last_inventory:
            self.InventoryUpdated.emit(new_inventory)
            self.last_inventory = new_inventory

    async def _multiworld_interaction(self) -> bool:
        """Returns true if an operation was sent."""
        locations = await self.known_collected_locations()
        if len(locations) != 0:
            for location in locations:
                self.PickupIndexCollected.emit(location)
            return True
        else:
            return await self.receive_remote_pickups(self.last_inventory, self.remote_pickups)

    async def _send_next_pending_message(self):
        if not self.pending_messages or self.message_cooldown > 0.0:
            return False

        message = self.pending_messages.pop(0)
        await self.execute_remote_patches([self._dol_patch_for_hud_message(message)])
        self.message_cooldown = 4.0
        return True

    async def display_arbitrary_message(self, message: str):
        self.pending_messages.append(message)

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]):
        """
        Sets the list of remote pickups that must be sent to the game.
        :param remote_pickups: Ordered list of pickups sent from other players, with the name of the player.
        """
        self.remote_pickups = remote_pickups

    async def force_finish(self):
        self._timer.stop()
        self.executor.disconnect()

    def is_disconnected(self) -> bool:
        return not self.executor.is_connected()

    def start_updates(self):
        self._timer.start()
