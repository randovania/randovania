from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from open_prime_rando.dol_patching import all_prime_dol_patches

from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationExecutor
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.games.prime2.patcher import echoes_items

if TYPE_CHECKING:
    from open_prime_rando.dol_patching.echoes.dol_patches import EchoesDolVersion

    from randovania.game_description.db.region import Region
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection


def format_received_item(item_name: str, player_name: str) -> str:
    special = {
        "Locked Power Bomb Expansion": (
            "Received Power Bomb Expansion from {provider_name}, but the main Power Bomb is required to use it."
        ),
        "Locked Missile Expansion": (
            "Received Missile Expansion from {provider_name}, but the Missile Launcher is required to use it."
        ),
        "Locked Seeker Launcher": (
            "Received Seeker Launcher from {provider_name}, but the Missile Launcher is required to use it."
        ),
    }

    generic = "Received {item_name} from {provider_name}."

    return special.get(item_name, generic).format(item_name=item_name, provider_name=player_name)


def _echoes_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x58
    vector_data_offset = 0x4
    powerup_size = 0xC
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


class EchoesRemoteConnector(PrimeRemoteConnector):
    def __init__(self, version: EchoesDolVersion, executor: MemoryOperationExecutor):
        super().__init__(version, executor)

    def _asset_id_format(self):
        return ">I"

    @property
    def multiworld_magic_item(self) -> ItemResourceInfo:
        return self.game.resource_database.get_item(echoes_items.MULTIWORLD_ITEM)

    async def current_game_status(self) -> tuple[bool, Region | None]:
        """
        Fetches the region the player's currently at, or None if they're not in-game.
        :return: bool indicating if there's a pending `execute_remote_patches` operation.
        """

        cstate_manager_global = self.version.cstate_manager_global

        asset_id_size = struct.calcsize(self._asset_id_format())
        mlvl_offset = 4
        cplayer_offset = 0x14FC

        memory_ops = [
            MemoryOperation(self.version.game_state_pointer, offset=mlvl_offset, read_byte_count=asset_id_size),
            MemoryOperation(cstate_manager_global + 0x2, read_byte_count=1),
            MemoryOperation(cstate_manager_global + cplayer_offset, offset=0, read_byte_count=4),
        ]
        results = await self.executor.perform_memory_operations(memory_ops)

        pending_op_byte = results[memory_ops[1]]
        has_pending_op = pending_op_byte != b"\x00"
        return has_pending_op, self._current_status_world(results.get(memory_ops[0]), results.get(memory_ops[2]))

    async def _memory_op_for_items(
        self,
        items: list[ItemResourceInfo],
    ) -> list[MemoryOperation]:
        player_state_pointer = self.version.cstate_manager_global + 0x150C
        return [
            MemoryOperation(
                address=player_state_pointer,
                offset=_echoes_powerup_offset(item.extra["item_id"]),
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

    def _resources_to_give_for_pickup(
        self,
        pickup: PickupEntry,
        inventory: Inventory,
    ) -> tuple[str, ResourceCollection]:
        item_name, resources_to_give = super()._resources_to_give_for_pickup(pickup, inventory)

        # Ignore item% for received items
        resources_to_give.remove_resource(self.game.resource_database.get_item("Percent"))

        return item_name, resources_to_give

    async def get_inventory(self) -> Inventory:
        inventory = await super().get_inventory()

        # mapWorldInfoAreas: 0x8c0
        # mapWorldInfoAreas.areas: + 0x4
        # mapWorldInfoAreas.areas.data: +0xc

        # multiple passes are required, as 128 bytes is too much at once for Nintendont
        PASSES = 2
        arr_raws = [
            await self.executor.perform_single_memory_operation(
                MemoryOperation(
                    address=self.version.cstate_manager_global + 0x8C0 + 0x4 + 0xC,
                    read_byte_count=4 * (32 // PASSES),
                    offset=i * 4 * (32 // PASSES),
                )
            )
            for i in range(PASSES)
        ]
        arr = struct.unpack(">32L", b"".join(arr_raws))

        count = 0

        for i in range(1024):
            f0 = arr[i // 32]
            f4 = 1 << (i % 32)
            if f4 & f0 != 0:
                count += 1

        inventory[self.game.resource_database.get_item("ObjectCount")] = InventoryItem(count, 1024)

        return inventory
