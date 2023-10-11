import logging
import struct

from caver.patcher import wrap_msg_text

from randovania.game_connection.connector.remote_connector import (
    PickupEntryWithOwner,
    PlayerLocationEvent,
    RemoteConnector,
)
from randovania.game_connection.executor.cs_executor import CSExecutor, GameState
from randovania.game_description import default_database
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.games.game import RandovaniaGame
from randovania.lib.infinite_timer import InfiniteTimer

ITEM_RECEIVED_FLAG = 7200


class CSRemoteConnector(RemoteConnector):
    game_state: GameState
    last_inventory: Inventory
    remote_pickups: tuple[PickupEntryWithOwner, ...]
    current_map: PlayerLocationEvent

    _dt: float = 2.5

    def __init__(self, executor: CSExecutor) -> None:
        super().__init__()
        self._layout_uuid = executor.server_info.uuid
        self.logger = logging.getLogger(type(self).__name__)
        self.executor = executor
        self.game = default_database.game_description_for(RandovaniaGame.CAVE_STORY)

        self.reset()

        self._timer = InfiniteTimer(self.update, self._dt)

    def reset(self):
        self.game_state = GameState.NONE
        self.last_inventory = Inventory.empty()
        self.remote_pickups = ()
        self.current_map = PlayerLocationEvent(None, None)

    @property
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.CAVE_STORY

    def description(self) -> str:
        return "%s: %s (API v%s)".format()

    def is_disconnected(self) -> bool:
        return not self.executor.is_connected()

    async def _disconnect(self):
        self.logger.info("Finishing connector")
        self.reset()
        self._timer.stop()
        if self.executor.is_connected():
            await self.executor.request_disconnect()
        self.Finished.emit()

    async def force_finish(self):
        await self._disconnect()

    async def update(self):
        self.game_state = await self.executor.get_game_state()
        if self.game_state.can_read_profile:
            profile_uuid = await self.executor.get_profile_uuid()
            if profile_uuid != self.layout_uuid:
                self.logger.warn("Loaded save with mismatched UUID")
                return

        await self._update_location()
        await self._update_collected_indices()
        await self._update_inventory()

        if self.is_disconnected():
            await self._disconnect()

    async def _update_location(self):
        new_map = self.current_map

        if not self.game_state.can_read_profile:
            new_map = PlayerLocationEvent(None, None)
        else:
            map_name_address = self.executor.server_info.offsets.get("map_name", 0x4937D0)
            map_name_raw = await self.executor.read_memory(map_name_address, 32)
            map_name = map_name_raw.decode("cp1252").rstrip("\0")

            area = next((area for area in self.game.region_list.all_areas if area.extra["map_name"] == map_name), None)

            if area is not None:
                new_map = PlayerLocationEvent(
                    self.game.region_list.region_with_area(area),
                    area,
                )

        if new_map != self.current_map:
            self.current_map = new_map
            self.PlayerLocationChanged.emit(self.current_map)

    async def _update_collected_indices(self):
        indices = sorted(self.game.region_list._pickup_index_to_node)
        flag_nums = [7300 + pickup_index.index for pickup_index in indices]
        flags = await self.executor.get_flags(flag_nums)

        for index, collected in zip(indices, flags):
            if collected:
                self.PickupIndexCollected.emit(index)

    async def _update_inventory(self):
        inventory = {}
        item_db = self.game.resource_database.item

        def get_item(name: str):
            return next(item for item in item_db if item.short_name == name)

        # Normal items
        normal_items = [item for item in item_db if "flag" in item.extra]
        flag_nums = [item.extra["flag"] for item in normal_items]
        flags = await self.executor.get_flags(flag_nums)

        for item, flag in zip(normal_items, flags):
            if flag:
                inv = InventoryItem(1, 1)
            else:
                inv = InventoryItem(0, 0)
            inventory[item] = inv

        # Puppies
        puppy_flags = await self.executor.get_flags(range(5001, 5006))
        puppies = get_item("puppies")
        puppy_count = sum(1 for pup in puppy_flags if pup)
        inventory[puppies] = InventoryItem(puppy_count, puppy_count)

        # Missile ammo
        weapons = await self.executor.get_weapons()
        missile_ammo = get_item("missile")
        missiles = next((weapon for weapon in weapons if weapon.weapon_id in (5, 10)), None)
        if missiles is not None:
            inventory[missile_ammo] = InventoryItem(missiles.ammo, missiles.capacity)
        else:
            inventory[missile_ammo] = InventoryItem(0, 0)

        # Life
        life = await self.executor.read_memory(148, 6, base_offset="mychar")
        hp, _, max_hp = struct.unpack("<3h", life)
        inventory[get_item("lifeCapsule")] = InventoryItem(hp, max_hp)

    def start_updates(self):
        self._timer.start()

    async def display_arbitrary_message(self, message: str):
        text = wrap_msg_text(message, False, None)
        script = f"<MSG{text}<WAI0500<END"
        await self.executor.exec_script(script)

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]):
        self.remote_pickups = remote_pickups
