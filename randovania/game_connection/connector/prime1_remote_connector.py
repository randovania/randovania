from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from open_prime_rando.dol_patching import all_prime_dol_patches
from open_prime_rando.dol_patching.prime1 import dol_patches

from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.executor.memory_operation import (
    MemoryOperation,
    MemoryOperationException,
    MemoryOperationExecutor,
)
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.games.prime1.patcher import prime_items

if TYPE_CHECKING:
    from open_prime_rando.dol_patching.prime1.dol_patches import Prime1DolVersion

    from randovania.game_connection.connector.prime_remote_connector import PatchInstructions, PickupPatches
    from randovania.game_description.db.region import Region
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo


def format_received_item(item_name: str, player_name: str) -> str:
    special = {
        "Locked Power Bomb Expansion": (
            "Received Power Bomb Expansion from {provider_name}, but the main Power Bomb is required to use it."
        ),
        "Locked Missile Expansion": (
            "Received Missile Expansion from {provider_name}, but the Missile Launcher is required to use it."
        ),
    }

    generic = "Received {item_name} from {provider_name}."

    return special.get(item_name, generic).format(item_name=item_name, provider_name=player_name)


def _prime1_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x24
    vector_data_offset = 0x4
    powerup_size = 0x8
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


class Prime1RemoteConnector(PrimeRemoteConnector):
    version: Prime1DolVersion

    def __init__(self, version: Prime1DolVersion, executor: MemoryOperationExecutor):
        super().__init__(version, executor)

    def _asset_id_format(self) -> str:
        return ">I"

    @property
    def multiworld_magic_item(self) -> ItemResourceInfo:
        return self.game.resource_database.get_item(prime_items.MULTIWORLD_ITEM)

    async def get_inventory(self) -> Inventory:
        """Fetches the inventory represented by the given game memory."""

        memory_ops = await self._memory_op_for_items(
            [
                item
                for item in self.game.resource_database.item
                if not item.extra.get("exclude_from_remote_connector")
            ]
        )
        ops_result = await self.executor.perform_memory_operations(memory_ops)

        inventory = {}
        for item, memory_op in zip(self.game.resource_database.item, memory_ops):
            inv = InventoryItem(*struct.unpack(">II", ops_result[memory_op]))
            if (inv.amount > inv.capacity or inv.capacity > item.max_capacity) and (item != self.multiworld_magic_item):
                raise MemoryOperationException(f"Received {inv} for {item.long_name}, which is an invalid state.")
            inventory[item] = inv

        for item in self.game.resource_database.item:
            if item.extra.get("unk2_bitmask_value"):
                unknown2 = inventory.get(self.game.resource_database.get_item("Unknown2"))
                if unknown2:
                    item_value = (unknown2.capacity & item.extra["unk2_bitmask_value"]) >= 1
                    new_item = InventoryItem(item_value, item_value)
                    inventory[item] = new_item

        return Inventory(inventory)

    async def current_game_status(self) -> tuple[bool, Region | None]:
        """
        Fetches the region the player's currently at, or None if they're not in-game.
        :return: bool indicating if there's a pending `execute_remote_patches` operation.
        """

        cstate_manager_global = self.version.cstate_manager_global

        asset_id_size = struct.calcsize(self._asset_id_format())
        mlvl_offset = 0x84
        cplayer_offset = 0x84C

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
        op = await self.executor.perform_single_memory_operation(
            MemoryOperation(
                address=self.version.cstate_manager_global + 0x8B8,
                read_byte_count=4,
            )
        )
        assert op is not None
        player_state_pointer = int.from_bytes(op, "big")

        return [
            MemoryOperation(
                address=player_state_pointer,
                offset=_prime1_powerup_offset(item.extra["item_id"]),
                read_byte_count=8,
            )
            for item in items
        ]

    async def _patches_for_pickup(self, provider_name: str, pickup: PickupEntry, inventory: Inventory) -> PickupPatches:
        item_name, resources_to_give = self._resources_to_give_for_pickup(pickup, inventory)

        self.logger.debug(f"Resource changes for {pickup.name} from {provider_name}: {resources_to_give}")

        patches: list[PatchInstructions] = []

        for item, delta in resources_to_give.as_resource_gain():
            if delta == 0:
                continue

            if item.extra.get("unk2_bitmask_value"):
                patches.append(
                    all_prime_dol_patches.adjust_item_amount_and_capacity_patch(
                        self.version.powerup_functions,
                        self.version.game,
                        self.game.resource_database.get_item("Unknown2").extra["item_id"],
                        (item.extra["item_id"] - 1000),
                    )
                )

            if item.short_name not in prime_items.ARTIFACT_ITEMS:
                if item.extra.get("max_increase", None) == 0:
                    patches.append(
                        all_prime_dol_patches.adjust_item_amount_patch(
                            self.version.powerup_functions,
                            self.version.game,
                            item.extra["refill_id"] if item.extra.get("is_refill", None) else item.extra["item_id"],
                            delta,
                        )
                    )
                else:
                    patches.append(
                        all_prime_dol_patches.adjust_item_amount_and_capacity_patch(
                            self.version.powerup_functions,
                            self.version.game,
                            item.extra["item_id"],
                            delta,
                        )
                    )
            else:
                if item.extra["item_id"] > 29:
                    layer_id = item.extra["item_id"] - 28
                else:
                    layer_id = 23  # Truth layer

                patches.append(
                    all_prime_dol_patches.increment_item_capacity_patch(
                        self.version.powerup_functions, self.version.game, item.extra["item_id"], delta
                    )
                )
                patches.append(dol_patches.set_artifact_layer_active_patch(self.version, layer_id, delta > 0))

        return patches, format_received_item(item_name, provider_name)

    def _write_string_to_game_buffer(self, message: str) -> MemoryOperation:
        return super()._write_string_to_game_buffer("&just=center;" + message)
