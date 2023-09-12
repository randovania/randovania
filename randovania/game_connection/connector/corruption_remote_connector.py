from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from open_prime_rando.dol_patching import all_prime_dol_patches

from randovania.game_connection.connector.prime_remote_connector import DolRemotePatch, PrimeRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationExecutor
from randovania.game_description.resources.inventory import Inventory, InventoryItem

if TYPE_CHECKING:
    from open_prime_rando.dol_patching.corruption.dol_patches import CorruptionDolVersion

    from randovania.game_connection.connector.remote_connector import PickupEntryWithOwner
    from randovania.game_description.db.region import Region
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo


def format_received_item(item_name: str, player_name: str) -> str:
    special = {
        "Locked Missile Expansion": (
            "Received Missile Expansion from {provider_name}, but the Missile Launcher is required to use it."
        ),
        "Locked Ship Missile Expansion": (
            "Received Ship Missile Expansion from {provider_name}, but the main launcher is required to use it."
        ),
    }

    generic = "Received {item_name} from {provider_name}."

    return special.get(item_name, generic).format(item_name=item_name, provider_name=player_name)


def _corruption_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x50
    vector_data_offset = 0x4
    powerup_size = 0xC
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


class CorruptionRemoteConnector(PrimeRemoteConnector):
    def __init__(self, version: CorruptionDolVersion, executor: MemoryOperationExecutor):
        super().__init__(version, executor)

    def _asset_id_format(self):
        return ">Q"

    @property
    def multiworld_magic_item(self) -> ItemResourceInfo:
        # TODO
        return None

    async def current_game_status(self) -> tuple[bool, Region | None]:
        """
        Fetches the region the player's currently at, or None if they're not in-game.
        :return: bool indicating if there's a pending `execute_remote_patches` operation.
        """

        cstate_manager_global = self.version.cstate_manager_global

        mlvl_offset = 8
        asset_id_size = struct.calcsize(self._asset_id_format())

        # TODO: there's one extra pointer indirection
        cplayer_offset = 40
        player_offset = 0x2184

        memory_ops = [
            MemoryOperation(self.version.game_state_pointer, offset=mlvl_offset, read_byte_count=asset_id_size),
            MemoryOperation(cstate_manager_global + 0x2, read_byte_count=1),
            MemoryOperation(cstate_manager_global + cplayer_offset, offset=player_offset, read_byte_count=4),
        ]
        results = await self.executor.perform_memory_operations(memory_ops)
        player_pointer = results.get(memory_ops[2])
        player_vtable = None
        if player_pointer is not None:
            player_vtable = await self.executor.perform_single_memory_operation(
                MemoryOperation(
                    struct.unpack(">I", player_pointer)[0],
                    read_byte_count=4,
                )
            )

        pending_op_byte = results[memory_ops[1]]
        has_pending_op = pending_op_byte != b"\x00"
        return has_pending_op, self._current_status_world(results.get(memory_ops[0]), player_vtable)

    async def _memory_op_for_items(
        self,
        items: list[ItemResourceInfo],
    ) -> list[MemoryOperation]:
        player_state_pointer = (
            int.from_bytes(
                await self.executor.perform_single_memory_operation(
                    MemoryOperation(
                        address=self.version.game_state_pointer,
                        read_byte_count=4,
                    )
                ),
                "big",
            )
            + 36
        )

        return [
            MemoryOperation(
                address=player_state_pointer,
                offset=_corruption_powerup_offset(item.extra["item_id"]),
                read_byte_count=8,
            )
            for item in items
        ]

    async def _patches_for_pickup(self, provider_name: str, pickup: PickupEntry, inventory: Inventory):
        item_name, resources_to_give = self._resources_to_give_for_pickup(pickup, inventory)

        self.logger.debug(f"Resource changes for {pickup.name} from {provider_name}: {resources_to_give}")
        patches = [
            all_prime_dol_patches.adjust_item_amount_and_capacity_patch(
                self.version.powerup_functions,
                self.version.game,
                item.extra["item_id"],
                delta,
            )
            for item, delta in resources_to_give.as_resource_gain()
        ]
        return patches, format_received_item(item_name, provider_name)

    def _dol_patch_for_hud_message(self, message: str) -> DolRemotePatch:
        raise RuntimeError("Unable to prepare dol patches for hud display in Corruption")

    async def receive_remote_pickups(
        self,
        inventory: Inventory,
        remote_pickups: tuple[PickupEntryWithOwner, ...],
    ) -> bool:
        # Not yet implemented
        return False

    async def execute_remote_patches(self, patches: list[DolRemotePatch]) -> None:
        raise RuntimeError("Unable to execute remote patches in Corruption")

    async def get_inventory(self) -> Inventory:
        item = self.game.resource_database.get_item("SuitType")
        inventory = await super().get_inventory()

        old_state = inventory[item]
        inventory[item] = InventoryItem(
            old_state.amount >= 5,
            old_state.capacity >= 5,
        )

        return inventory
