import logging
import uuid

from qasync import asyncSlot

from randovania.exporter.pickup_exporter import _conditional_resources_for_pickup
from randovania.game_connection.connector.remote_connector import (
    PickupEntryWithOwner,
    PlayerLocationEvent,
    RemoteConnector,
)
from randovania.game_connection.executor.am2r_executor import AM2RExecutor
from randovania.game_description import default_database
from randovania.game_description.db.region import Region
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.game import RandovaniaGame


def format_received_item(item_name: str, player_name: str) -> str:
    special = {}
    generic = "Received {item_name} from {provider_name}."
    return special.get(item_name, generic).format(item_name=item_name, provider_name=player_name)


def resources_to_give_for_pickup(
    db: ResourceDatabase,
    pickup: PickupEntry,
    inventory: Inventory,
) -> tuple[str, list[list[dict]]]:
    inventory_resources = ResourceCollection.with_database(db)
    inventory_resources.add_resource_gain([(item, inv_item.capacity) for item, inv_item in inventory.items()])
    conditional = pickup.conditional_for_resources(inventory_resources)
    if conditional.name is not None:
        item_name = conditional.name
    else:
        item_name = pickup.name

    conditional_resources = _conditional_resources_for_pickup(pickup)
    # Commented out, because get_resources_for_details is dread specific
    # resources = get_resources_for_details(pickup, conditional_resources, False)
    resources = conditional_resources

    return item_name, resources


class AM2RRemoteConnector(RemoteConnector):
    _game_enum: RandovaniaGame = RandovaniaGame.AM2R

    def __init__(self, executor: AM2RExecutor):
        super().__init__()
        self._layout_uuid = uuid.UUID(executor.layout_uuid_str)
        self.logger = logging.getLogger(type(self).__name__)
        self.executor = executor
        self.game = default_database.game_description_for(RandovaniaGame.AM2R)

        self.reset_values()

        self.executor.signals.new_inventory.connect(self.new_inventory_received)
        self.executor.signals.new_collected_locations.connect(self.new_collected_locations_received)
        self.executor.signals.new_player_location.connect(self.new_player_location_received)
        self.executor.signals.new_received_pickups.connect(self.new_received_pickups_received)
        self.executor.signals.connection_lost.connect(self.connection_lost)

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._game_enum

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
        self.remote_pickups = ()
        self.last_inventory = Inventory.empty()
        self.in_cooldown = True
        self.received_pickups = None
        self.current_region = None

    def new_player_location_received(self, state_or_region: str):
        # Skip title screen and pause screen
        if state_or_region == "rm_transition" or state_or_region == "rm_subscreen":
            return
        elif not state_or_region.startswith("rm_a") or len(state_or_region) < 5:
            self.reset_values()
            self.current_region = None
        else:
            area_number = state_or_region[4]
            self.current_region = next(
                (
                    region
                    for region in self.game.region_list.regions
                    if str(region.extra["internal_number"]) == area_number
                ),
                None,
            )
        self.PlayerLocationChanged.emit(PlayerLocationEvent(self.current_region, None))

    def new_collected_locations_received(self, new_indices: str):
        locations = set()
        start_of_indices = "locations:"

        if not new_indices.startswith(start_of_indices):
            self.logger.warning("Unknown response: %s", new_indices)
            return

        for index in new_indices[len(start_of_indices) :].split(","):
            if not index.isdigit():
                continue
            locations.add(PickupIndex(int(index)))

        for location in locations:
            print("Collected: " + str(location))
            self.PickupIndexCollected.emit(location)

    def new_inventory_received(self, new_inventory: str):
        locations = {}
        start_of_inventory = "items:"

        if not new_inventory.startswith(start_of_inventory):
            self.logger.warning("Unknown response: %s", new_inventory)
            return

        for position in new_inventory[len(start_of_inventory) :].split(","):
            print(bytes(position, "utf-8"))
            if "|" not in position:
                continue
            (item_name, quantity) = position.split("|")
            if not quantity.isdigit():
                continue

            item_name_replacement = {
                "Missile Expansion": "Missiles",
                "Super Missile Expansion": "Super Missiles",
                "Power Bomb Expansion": "Power Bombs",
            }

            progressives = {
                "Progressive Jump": ("Hi-Jump Boots", "Space Jump"),
                "Progressive Suit": ("Varia Suit", "Gravity Suit"),
            }

            if item_name in item_name_replacement:
                item_name = item_name_replacement[item_name]

            if item_name in progressives:
                if len([i for i, q in locations.items() if i.long_name == progressives[item_name][0]]) > 0:
                    item_name = progressives[item_name][1]
                elif len([i for i, q in locations.items() if i.long_name == progressives[item_name][1]]) > 0:
                    item_name = progressives[item_name][1]
                else:
                    item_name = progressives[item_name][0]

            item_list = [i for i in self.game.resource_database.item if i.long_name == item_name]
            item = item_list[0]
            print(item)
            if item in locations:
                locations[item] += int(quantity)
            else:
                locations[item] = int(quantity)

        inventory = Inventory({item: InventoryItem(quantity, quantity) for item, quantity in locations.items()})
        self.last_inventory = inventory
        self.InventoryUpdated.emit(inventory)

    @asyncSlot()
    async def new_received_pickups_received(self, new_received_pickups: str):
        new_recv_as_int = int(new_received_pickups)
        self.logger.debug("Received Pickups: %s", new_received_pickups)
        if self.current_region is not None:
            print(self.current_region)
            self.in_cooldown = False
        self.received_pickups = new_recv_as_int
        await self.receive_remote_pickups()

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]):
        self.remote_pickups = remote_pickups
        await self.receive_remote_pickups()

    # TODO: these functions have to be implemented still!
    async def receive_remote_pickups(self) -> None:
        remote_pickups = self.remote_pickups

        # in that case we never received the numbers (at least 0) from the game
        if self.received_pickups is None:
            return

        num_pickups = self.received_pickups

        if num_pickups >= len(remote_pickups) or self.in_cooldown:
            return

        self.in_cooldown = True

        provider_name, pickup = remote_pickups[num_pickups]
        name, model = pickup.name, pickup.model.name  # TODO: what about progessive items??? Also drops are broken
        quantity = next(pickup.conditional_resources).resources[0][1]

        # item_name, items_list = resources_to_give_for_pickup(self.game.resource_database, pickup, inventory)

        self.logger.debug("Resource changes for %s from %s", pickup.name, provider_name)
        await self.executor.send_pickup_info(provider_name, name, model, quantity)

        # from open_dread_rando.lua_util import lua_convert
        # progression_as_lua = lua_convert(items_list, True)
        # message = format_received_item(item_name, provider_name)

        # self.logger.info("%d permanent pickups, magic %d. Next pickup: %s",
        #                  len(remote_pickups), num_pickups, message)

        # main_item_id = items_list[0][0]["item_id"]
        # from open_dread_rando.lua_editor import LuaEditor
        # parent = LuaEditor.get_parent_for(None, main_item_id)

        # f"RL.ReceivePickup({repr(message)},{parent},{repr(progression_as_lua)},{num_pickups},{self.inventory_index})"

    async def display_arbitrary_message(self, message: str):
        escaped_message = message.replace("#", "\\#")  # In GameMaker, '#' is a newline.
        await self.executor.display_message(escaped_message)
