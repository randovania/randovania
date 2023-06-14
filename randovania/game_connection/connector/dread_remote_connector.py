import json
import logging
import uuid

from randovania.game_connection.connector.remote_connector import PlayerLocationEvent, RemoteConnector
from randovania.game_connection.executor.dread_executor import DreadExecutor
from randovania.game_description import default_database
from randovania.game_description.resources.item_resource_info import InventoryItem
from randovania.game_description.db.region import Region
from randovania.games.game import RandovaniaGame

class DreadRemoteConnector(RemoteConnector):
    _game_enum: RandovaniaGame = RandovaniaGame.METROID_DREAD

    def __init__(self, executor: DreadExecutor):
        super().__init__()
        self._layout_uuid = uuid.UUID(executor.layout_uuid_str)
        self.logger = logging.getLogger(type(self).__name__)
        self.executor = executor
        self.game = default_database.game_description_for(RandovaniaGame.METROID_DREAD)

        self.reset_values()

        self.executor.signals.new_inventory.connect(self.new_inventory_received)
        self.executor.signals.new_player_location.connect(self.new_player_location_received)
        self.executor.signals.connection_lost.connect(self.connection_lost)

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._game_enum

    # TODO: we could fetch and add the game version here
    def description(self):
        return f"{self.game_enum.long_name}"

    async def current_game_status(self) -> tuple[bool, Region | None]:
        return (self.in_cooldown, self.current_region)

    def connection_lost(self):
        self.logger.info("Finishing connector")
        # TODO: Finished signal is never used. Remove it everywhere?
        self.Finished.emit()

    async def force_finish(self):
        self.executor.disconnect()

    def is_disconnected(self) -> bool:
        return not self.executor.is_connected()

    # reset all values on init, disconnect or after switching back to main menu
    def reset_values(self):
        self.remote_pickups = tuple()
        self.last_inventory = {}
        self.in_cooldown = True
        self.received_pickups = -1
        self.inventory_index = -1
        self.current_region = None

    def new_player_location_received(self, state_or_region: str):
        if state_or_region == "MAINMENU":
            self.reset_values()
            self.current_region = None
        else:
            self.current_region = next((region for region in self.game.region_list.regions
                                       if region.extra["scenario_id"] == state_or_region),
                                        None)
        self.PlayerLocationChanged.emit(PlayerLocationEvent(self.current_region, None))

    def new_inventory_received(self, json_string: str):
        try:
            inventory_json = json.loads(json_string)
            self.inventory_index = inventory_json["index"]
            inventory_ints: list[int] = inventory_json["inventory"]
        except Exception as e:
            self.logger.error(f"Unknown response: {json_string} (got {e})")
            return {}

        items = [r for r in self.game.resource_database.item if "item_id" in r.extra]

        inventory = {
            item: InventoryItem(quantity, quantity)
            for item, quantity in zip(items, inventory_ints)
        }
        self.last_inventory = inventory
        self.InventoryUpdated.emit(inventory)

