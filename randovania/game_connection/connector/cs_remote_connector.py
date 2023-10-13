import logging
import struct

from caver.patcher import wrap_msg_text

from randovania.game_connection.connector.remote_connector import (
    PickupEntryWithOwner,
    PlayerLocationEvent,
    RemoteConnector,
)
from randovania.game_connection.executor.cs_executor import CSExecutor, GameState, TSCError
from randovania.game_description import default_database
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.games.cave_story.exporter.patch_data_factory import NOTHING_ITEM_SCRIPT
from randovania.games.game import RandovaniaGame
from randovania.lib.infinite_timer import InfiniteTimer

ITEM_SENT_FLAG = 7410
ITEM_RECEIVED_FLAG = 7411


class CSRemoteConnector(RemoteConnector):
    game_state: GameState
    last_inventory: Inventory
    remote_pickups: tuple[PickupEntryWithOwner, ...]
    current_map: PlayerLocationEvent

    _dt: float = 1.0

    def __init__(self, executor: CSExecutor) -> None:
        super().__init__()
        self._layout_uuid = executor.server_info.uuid
        self.logger = logging.getLogger(type(self).__name__)
        self.executor = executor
        self.game = default_database.game_description_for(RandovaniaGame.CAVE_STORY)
        self.pickup_db = default_database.pickup_database_for_game(RandovaniaGame.CAVE_STORY)

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
        return f"{self.game_enum.long_name}: {self.executor.server_info.platform.capitalize()}"

    def is_disconnected(self) -> bool:
        return not self.executor.is_connected()

    async def _disconnect(self):
        self.logger.info("Finishing connector")
        self.reset()
        self._timer.stop()
        self.executor.disconnect()
        self.Finished.emit()

    async def force_finish(self):
        if self.executor.is_connected():
            await self.executor.request_disconnect()
        await self._disconnect()

    async def update(self):
        if self.is_disconnected():
            await self._disconnect()
            return

        try:
            self.game_state = await self.executor.get_game_state()
            if self.game_state.can_read_profile:
                profile_uuid = await self.executor.get_profile_uuid()
                if profile_uuid != self.layout_uuid:
                    self.logger.warn("Loaded save with mismatched UUID")
                    return

            await self._update_location()
            await self._update_collected_indices()
            await self._update_inventory()

            await self._receive_items()

        except TSCError:
            await self._disconnect()

    async def _update_location(self):
        new_map = self.current_map

        if not self.game_state.can_read_profile:
            new_map = PlayerLocationEvent(None, None)
        else:
            map_name = await self.executor.get_map_name()
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
        self.game.region_list.ensure_has_node_cache()
        indices = sorted(self.game.region_list._pickup_index_to_node)
        flag_nums = [7300 + pickup_index.index for pickup_index in indices]
        flags = await self.executor.get_flags(flag_nums)

        for index, collected in zip(indices, flags):
            if collected:
                self.PickupIndexCollected.emit(index)

    async def _update_inventory(self):
        new_inventory = await self.get_inventory()
        if new_inventory != self.last_inventory:
            self.last_inventory = new_inventory
            self.InventoryUpdated.emit(new_inventory)

    async def get_inventory(self) -> Inventory:
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
        life = await self.executor.read_memory(0, 2, base_offset="current_hp")
        life += await self.executor.read_memory(0, 2, base_offset="max_hp")
        hp, max_hp = struct.unpack("<2h", life)
        inventory[get_item("lifeCapsule")] = InventoryItem(hp, max_hp)

        return Inventory(inventory)

    async def _receive_items(self):
        if not len(self.remote_pickups):
            return

        num_pickups = await self.executor.get_received_items()
        if num_pickups >= len(self.remote_pickups):
            return

        if await self.executor.get_flag(ITEM_RECEIVED_FLAG):
            await self.executor.set_received_items(num_pickups + 1)
            await self.executor.set_flag(ITEM_RECEIVED_FLAG, False)
            await self.executor.set_flag(ITEM_SENT_FLAG, False)
            return

        if await self.executor.get_flag(ITEM_SENT_FLAG):
            return

        await self.executor.set_flag(ITEM_SENT_FLAG, True)
        provider_name, pickup = self.remote_pickups[num_pickups]

        message = f"Received item from ={provider_name}=!"
        message = wrap_msg_text(message, False)
        pickup_script = self.pickup_db.get_pickup_with_name(pickup.name).extra.get("script", NOTHING_ITEM_SCRIPT)
        script = f"<MSG<TUR{message}<FL+{ITEM_RECEIVED_FLAG}{pickup_script}"
        await self.executor.exec_script(script)

    def start_updates(self):
        self._timer.start()

    async def display_arbitrary_message(self, message: str):
        text = wrap_msg_text(message, False, max_text_boxes=None)
        script = f"<MSG{text}<WAI0500<END"
        await self.executor.exec_script(script)

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]):
        self.remote_pickups = remote_pickups
