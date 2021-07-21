import struct
from typing import Optional, List, Tuple

from randovania.game_connection.connection_base import Inventory
from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationExecutor
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world.world import World
from randovania.games.prime import (all_prime_dol_patches)
from randovania.games.prime.echoes_dol_patches import EchoesDolVersion


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


def _echoes_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x58
    vector_data_offset = 0x4
    powerup_size = 0xc
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


class EchoesRemoteConnector(PrimeRemoteConnector):
    def __init__(self, version: EchoesDolVersion):
        super().__init__(version)

    def _asset_id_format(self):
        return ">I"

    async def current_game_status(self, executor: MemoryOperationExecutor) -> Tuple[bool, Optional[World]]:
        """
        Fetches the world the player's currently at, or None if they're not in-game.
        :param executor:
        :return: bool indicating if there's a pending `execute_remote_patches` operation.
        """

        cstate_manager_global = self.version.cstate_manager_global

        asset_id_size = struct.calcsize(self._asset_id_format())
        mlvl_offset = 4
        cplayer_offset = 0x14fc

        memory_ops = [
            MemoryOperation(self.version.game_state_pointer, offset=mlvl_offset, read_byte_count=asset_id_size),
            MemoryOperation(cstate_manager_global + 0x2, read_byte_count=1),
            MemoryOperation(cstate_manager_global + cplayer_offset, offset=0, read_byte_count=4),
        ]
        results = await executor.perform_memory_operations(memory_ops)

        pending_op_byte = results[memory_ops[1]]
        has_pending_op = pending_op_byte != b"\x00"
        return has_pending_op, self._current_status_world(results.get(memory_ops[0]),
                                                          results.get(memory_ops[2]))

    async def _memory_op_for_items(self, executor: MemoryOperationExecutor, items: List[ItemResourceInfo],
                                   ) -> List[MemoryOperation]:

        player_state_pointer = self.version.cstate_manager_global + 0x150c
        return [
            MemoryOperation(
                address=player_state_pointer,
                offset=_echoes_powerup_offset(item.index),
                read_byte_count=8,
            )
            for item in items
        ]

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
