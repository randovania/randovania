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
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.prime1.patcher import prime_items

if TYPE_CHECKING:
    from open_prime_rando.dol_patching.prime1.dol_patches import Prime1DolVersion

    from randovania.game_connection.connector.prime_remote_connector import PatchInstructions, PickupPatches
    from randovania.game_description.db.region import Region
    from randovania.game_description.pickup.pickup_entry import PickupEntry


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


class Prime1RemoteConnector(PrimeRemoteConnector):
    version: Prime1DolVersion

    def __init__(self, version: Prime1DolVersion, executor: MemoryOperationExecutor):
        super().__init__(version, executor)

    @property
    def total_item_length(self) -> int:
        return 41

    @property
    def powerup_size(self) -> int:
        return 0x8

    def powerup_offset(self, item_index: int) -> int:
        powerups_offset = 0x24
        vector_data_offset = 0x4
        return (powerups_offset + vector_data_offset) + (item_index * self.powerup_size)

    def _asset_id_format(self) -> str:
        return ">I"

    @property
    def multiworld_magic_item(self) -> ItemResourceInfo:
        return self.game.get_resource_database_view().get_item(prime_items.MULTIWORLD_ITEM)

    async def current_game_status(self) -> tuple[bool, Region | None]:
        """
        Fetches the region the player's currently at, or None if they're not in-game.
        :return: bool indicating if there's a pending `execute_remote_patches` operation.
        """

        cstate_manager_global = self.version.cstate_manager_global

        asset_id_size = struct.calcsize(self._asset_id_format())
        mlvl_offset = 0x84
        cplayer_offset = 0x84C

        # Both of these can be a nullpointer. The first one while the game is booting up, the second at
        # title screen/elevators. In both cases we can just say that they're in an invalid World / can't be acted on.
        world_status_ops = [
            MemoryOperation(self.version.game_state_pointer, offset=mlvl_offset, read_byte_count=asset_id_size),
            MemoryOperation(cstate_manager_global + cplayer_offset, offset=0, read_byte_count=4),
        ]
        try:
            world_status_results = await self.executor.perform_memory_operations(world_status_ops)
            world_asset_id, cplayer_vtable = world_status_results.values()
        except MemoryOperationException:
            return True, None

        pending_byte_op = MemoryOperation(cstate_manager_global + self._pending_op_offset, read_byte_count=1)
        pending_byte_result = await self.executor.perform_single_memory_operation(pending_byte_op)
        has_pending_op = pending_byte_result != b"\x00"

        current_world = self._current_status_world(world_asset_id, cplayer_vtable)
        return has_pending_op, current_world

    async def _get_cplayer_state_pointer(self) -> int:
        # CPlayerState a ref counted pointer within CStatemanager:
        # https://github.com/PrimeDecomp/prime/blob/main/include/MetroidPrime/CStateManager.hpp#L395
        cplayer_state_offset = 0x8B8

        op = await self.executor.perform_single_memory_operation(
            MemoryOperation(
                address=self.version.cstate_manager_global + cplayer_state_offset,
                read_byte_count=4,
            )
        )
        assert op is not None
        player_state_pointer = int.from_bytes(op, "big")
        return player_state_pointer

    async def _patches_for_pickup(self, provider_name: str, pickup: PickupEntry, inventory: Inventory) -> PickupPatches:
        item_name, resources_to_give = self._resources_to_give_for_pickup(pickup, inventory)

        self.logger.debug(f"Resource changes for {pickup.name} from {provider_name}: {resources_to_give}")

        patches: list[PatchInstructions] = []

        for item, delta in resources_to_give.as_resource_gain():
            if delta == 0:
                continue

            assert isinstance(item, ItemResourceInfo)

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

    def at_end_of_game(self) -> bool:
        return self._last_emitted_region is not None and self._last_emitted_region.name == "End of Game"
