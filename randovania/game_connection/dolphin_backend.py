import copy
from typing import List, Optional, Dict

import dolphin_memory_engine

from randovania.game_connection.connection_backend import ConnectionBackend, MemoryOperation
from randovania.game_connection.connection_base import ConnectionStatus
from randovania.game_description.default_database import default_prime2_game_description
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import CurrentResources, add_resource_gain_to_current_resources
from randovania.game_description.world import World


def _powerup_address(player_state_address: int, item_index: int) -> int:
    powerups_offset = 0x58
    vector_data_offset = 0x4
    powerup_size = 0xc
    return player_state_address + (powerups_offset + vector_data_offset) + (item_index * powerup_size)


def _add_pickup_to_resources(pickup: PickupEntry, inventory: CurrentResources) -> CurrentResources:
    return add_resource_gain_to_current_resources(
        pickup.resource_gain(inventory),
        copy.copy(inventory)
    )


class DolphinBackend(ConnectionBackend):
    _world: Optional[World] = None
    _multiworld_magic_item: int = 74
    _pickups_to_give: List[PickupEntry]
    _permanent_pickups: List[PickupEntry]

    def __init__(self):
        super().__init__()

        self.dolphin = dolphin_memory_engine

        self._pickups_to_give = []
        self._permanent_pickups = []

    @property
    def _percentage_item(self) -> ItemResourceInfo:
        return self.game.resource_database.item_percentage

    @property
    def lock_identifier(self) -> Optional[str]:
        return "randovania-dolphin-backend"

    # Game Backend Stuff
    def _memory_operation(self, op: MemoryOperation) -> Optional[bytes]:
        op.validate_byte_sizes()

        address = op.address
        if op.offset is not None:
            try:
                address = self.dolphin.follow_pointers(address, [op.offset])
            except RuntimeError:
                return None

        result = None
        if op.read_byte_count is not None:
            result = self.dolphin.read_bytes(address, op.read_byte_count)
        if op.write_bytes is not None:
            self.dolphin.write_bytes(address, op.write_bytes)
        return result

    async def _perform_memory_operations(self, ops: List[MemoryOperation]) -> List[Optional[bytes]]:
        return [
            self._memory_operation(op)
            for op in ops
        ]

    def _ensure_hooked(self) -> bool:
        if not self.dolphin.is_hooked():
            self.patches = None
            self.dolphin.hook()

        return not self.dolphin.is_hooked()

    def _test_still_hooked(self):
        try:
            if len(self.dolphin.read_bytes(0x0, 4)) != 4:
                raise RuntimeError("Dolphin hook didn't read the correct byte count")
        except RuntimeError:
            self.dolphin.un_hook()

    def _update_current_world(self):
        try:
            world_asset_id = self.dolphin.follow_pointers(self.patches.string_display.cstate_manager_global + 0x1604,
                                                          [0x8])
        except RuntimeError:
            world_asset_id = None

        if world_asset_id is None:
            self._world = None
            self._test_still_hooked()
        else:
            try:
                self._world = self.game.world_list.world_by_asset_id(self.dolphin.read_word(world_asset_id))
            except KeyError:
                self._world = None

    async def update(self, dt: float):
        if self._ensure_hooked():
            return

        if not await self._identify_game():
            self._test_still_hooked()
            return

        await self._send_message_from_queue(dt)

        self._update_current_world()
        if self._world is not None:
            self._inventory = await self._get_inventory()
            if self.checking_for_collected_index:
                await self._check_for_collected_index()

    @property
    def name(self) -> str:
        return "Dolphin"

    @property
    def current_status(self) -> ConnectionStatus:
        if not self.dolphin.is_hooked():
            return ConnectionStatus.Disconnected

        if self.patches is None:
            return ConnectionStatus.WrongGame

        if self._world is None:
            return ConnectionStatus.TitleScreen
        elif not self.checking_for_collected_index:
            return ConnectionStatus.TrackerOnly
        else:
            return ConnectionStatus.InGame

    async def _get_player_state_address(self) -> Optional[int]:
        try:
            cstate_manager = self.patches.string_display.cstate_manager_global
            player_states = cstate_manager + 0x150c

            return self.dolphin.follow_pointers(player_states, [0])
        except RuntimeError:
            return None

    def _name_for_item(self, item: int) -> str:
        return self.game.resource_database.get_item(item).long_name

    async def _raw_set_item_capacity(self, item: int, capacity: int, player_state_address: int):
        quantity_address = _powerup_address(player_state_address, item)
        capacity_address = quantity_address + 0x4

        current_capacity = self.dolphin.read_word(capacity_address)
        capacity_delta = capacity - current_capacity

        if capacity_delta != 0:
            self.logger.debug(f"set capacity for {self._name_for_item(item)} to {capacity}")
            self.dolphin.write_word(capacity_address, capacity)

        if capacity_delta > 0:
            self.dolphin.write_word(quantity_address, self.dolphin.read_word(quantity_address) + capacity_delta)

            if item == 13:  # Dark Suit
                self.dolphin.write_word(player_state_address + 84, 1)
            elif item == 14:  # Light Suit
                self.dolphin.write_word(player_state_address + 84, 2)
            elif item == self.game.resource_database.energy_tank.index:
                base_health_capacity = self.dolphin.read_word(self.patches.health_capacity.base_health_capacity)
                energy_tank_capacity = self.dolphin.read_word(self.patches.health_capacity.energy_tank_capacity)
                self.dolphin.write_float(player_state_address + 20,
                                         capacity * energy_tank_capacity + base_health_capacity)

    async def _check_for_collected_index(self):
        player_state_address = await self._get_player_state_address()
        quantity_address = _powerup_address(player_state_address, self._multiworld_magic_item)
        capacity_address = quantity_address + 0x4

        magic_quantity = self.dolphin.read_word(quantity_address)
        magic_capacity = self.dolphin.read_word(capacity_address)

        if magic_quantity > 0:
            self.logger.info(f"_check_for_collected_index: magic item was at {magic_quantity}/{magic_capacity}")
            magic_capacity -= magic_quantity

            self.dolphin.write_word(quantity_address, 0)
            self.dolphin.write_word(capacity_address, magic_capacity)
            await self._emit_location_collected(magic_quantity - 1)

        if self._pickups_to_give or magic_capacity < len(self._permanent_pickups):
            self.logger.info(f"_check_for_collected_index: {len(self._pickups_to_give)} pickups to give, "
                             f"{len(self._permanent_pickups)} permanent pickups, magic {magic_capacity}")

            inventory = self.get_current_inventory()
            inventory_resources: CurrentResources = {
                item: inv_item.capacity
                for item, inv_item in inventory.items()
            }

            while self._pickups_to_give:
                inventory_resources = _add_pickup_to_resources(self._pickups_to_give.pop(), inventory_resources)

            for pickup in self._permanent_pickups[magic_capacity:]:
                inventory_resources = _add_pickup_to_resources(pickup, inventory_resources)

            for item, capacity in inventory_resources.items():
                if item != self._percentage_item:
                    await self._raw_set_item_capacity(item.index, min(capacity, item.max_capacity),
                                                      player_state_address)

            self.dolphin.write_word(capacity_address, len(self._permanent_pickups))

    def send_pickup(self, pickup: PickupEntry):
        self._pickups_to_give.append(pickup)

    def set_permanent_pickups(self, pickups: List[PickupEntry]):
        self._permanent_pickups = pickups
