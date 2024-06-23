import logging
import uuid
from collections import defaultdict
from typing import TYPE_CHECKING

from qasync import asyncSlot

from randovania.game_connection.connector.remote_connector import (
    PickupEntryWithOwner,
    PlayerLocationEvent,
    RemoteConnector,
)
from randovania.game_connection.executor.am2r_executor import AM2RExecutor
from randovania.game_description import default_database
from randovania.game_description.db.region import Region
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.am2r.pickup_database import progressive_items
from randovania.games.game import RandovaniaGame

if TYPE_CHECKING:
    from randovania.game_description.pickup.pickup_entry import PickupEntry


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

    def description(self) -> str:
        return f"{self.game_enum.long_name}"

    async def current_game_status(self) -> tuple[bool, Region | None]:
        return (self.in_cooldown, self.current_region)

    def connection_lost(self) -> None:
        self.logger.info("Finishing connector")

    async def force_finish(self) -> None:
        self.executor.disconnect()

    def is_disconnected(self) -> bool:
        return not self.executor.is_connected()

    # Reset all values on init, disconnect or after switching back to main menu
    def reset_values(self) -> None:
        self.remote_pickups: tuple[tuple[str, PickupEntry], ...] = ()
        self.last_inventory = Inventory.empty()
        self.in_cooldown = True
        self.received_pickups: int | None = None
        self.current_region: Region | None = None

    def new_player_location_received(self, state_or_region: str) -> None:
        """
        __Location implementation detail:__
        All rooms in am2r have a sort of rule they follow to, with `rm_aXYZZ`, where X is a number denoting the area,
        Y is an identifier for a subarea, and ZZ is a number. I.e `rm_a3b03` is the third room in breeding grounds
        for A3. All regions in RDV also have data on which internal number they map to
        Thus, the client just sends their internal room name if a room is changed, and on the RDV side, we check the
        region number and update it.
        :param state_or_region: Internal room name of the game.
        """

        # Dont update on pause screens/transitions
        ignore_rooms = ("rm_transition", "rm_subscreen", "rm_loading", "itemroom")
        if state_or_region in ignore_rooms:
            return

        # Reset if we're on title screen or other unknown screens
        if not state_or_region.startswith("rm_a") or len(state_or_region) < 5:
            self.reset_values()
            self.current_region = None
            self.PlayerLocationChanged.emit(PlayerLocationEvent(self.current_region, None))
            return

        # Normal rooms with our rm_aXYZZ format
        area_number = state_or_region[4]
        self.current_region = next(
            (region for region in self.game.region_list.regions if str(region.extra["internal_number"]) == area_number),
            None,
        )
        self.PlayerLocationChanged.emit(PlayerLocationEvent(self.current_region, None))

    def new_collected_locations_received(self, new_indices: str) -> None:
        """
        __Collected locations implementation detail:__
        The game keeps track of which locations it collected, in a big string, with the format `locations:XX,YY,ZZ...`,
        where XX/YY/ZZ are the pickup indices. The pickup indices match between game and DB.
        Also, this string is saved to the save file.
        The game sends that string to RDV, where we then loop through it, and mark every index as collected.

        :param new_indices: A string from the game with the format `locations:XX,YY,ZZ...`.
        """
        if self.current_region is None:
            return

        locations = set()
        start_of_indices = "locations:"

        if not new_indices.startswith(start_of_indices):
            self.logger.warning("Unknown response: %s", new_indices)
            return

        for index in new_indices[len(start_of_indices) :].split(","):
            if not index.isdigit():
                self.logger.warning("Response should contain a digit, but instead contains '%s'", index)
                continue
            locations.add(PickupIndex(int(index)))

        for location in locations:
            self.PickupIndexCollected.emit(location)

    def new_inventory_received(self, new_inventory: str) -> None:
        """
        __New inventory implementation detail:__
        The game keeps track of which items it collected in a big string with the format
        `items:XA|XB,YA|YB,ZA|ZB...`, where XA/YA/ZA are the item names and XB/YB/ZB is the quantity of that item.
        This string is also saved to the save file. The item names *mostly* match up with the RDV item names,
        except for ammo and progressives.
        The game sends that string to RDV, where we then loop through it. We adjust the item name for ammo and
        progressives accordingly, and stuff it into an item|quantity dict.
        If the item exists in that dict, we increase its quantity, if not, we add it. Then, based on that dict, we
        update the inventory.

        Regarding ammo and progressives: for some reason, we need here the name of the ammo, and not the name of the
        expansions. I.e. for `Missile Expansions`, we need `Missiles`. So there's a lookup dict here to adjust for them.

        :param new_inventory: A string from the game with the format `items:XA|XB,YA|YB,ZA|ZB...`.
        """
        if self.current_region is None:
            return

        inventory_dict = defaultdict(int)
        start_of_inventory = "items:"

        if not new_inventory.startswith(start_of_inventory):
            self.logger.warning("Unknown response: %s", new_inventory)
            return

        for position in new_inventory[len(start_of_inventory) :].split(","):
            if not position:
                continue
            if "|" not in position:
                self.logger.warning("Response should contain a '|', but it doesn't")
                continue
            (item_name, quantity) = position.split("|", 1)
            if not quantity.isdigit():
                self.logger.warning("Response should contain a digit, but instead contains '%s'", position)
                continue

            # Ammo is sent twice by the game: once as actual ammo, once as expansion. Let's ignore the expansions.
            item_name_replacement = {
                "Missile Tank": "Nothing",
                "Super Missile Tank": "Nothing",
                "Power Bomb Tank": "Nothing",
                # These names were used in older versions. To not break compatibility, we're keeping them here.
                "Missile Expansion": "Nothing",
                "Super Missile Expansion": "Nothing",
                "Power Bomb Expansion": "Nothing",
            }

            # If our item name is in the lookup dict, we replace it. If it isn't, we keep it as is
            item_name = item_name_replacement.get(item_name, item_name)
            inventory_dict[item_name] += int(quantity)

        # The game sends the name of the progressive items, not the underlying items.
        # Since progressives are not resources in the DB, we need to handle them correctly and give the actual items.
        progressives = progressive_items.tuples()

        for progressive_name, actual_items in progressives:
            quantity = inventory_dict.pop(progressive_name, 0)
            for index in range(quantity):
                if index >= len(actual_items):
                    break
                inventory_dict[actual_items[index]] += 1

        inventory = Inventory(
            {
                self.game.resource_database.get_item_by_name(name): InventoryItem(quantity, quantity)
                for name, quantity in inventory_dict.items()
            }
        )
        self.last_inventory = inventory
        self.InventoryUpdated.emit(inventory)

    @asyncSlot()
    async def new_received_pickups_received(self, new_received_pickups: str) -> None:
        """
        The game periodically sends a packet, to tell RDV how many pickups it has received. If the game is in a valid
        region, and the game has fewer pickups than what the server has, then we resend the game the missing items.
        :param new_received_pickups: A number as a string on how many pickups the game has received.
        :return:
        """
        new_recv_as_int = int(new_received_pickups)
        self.logger.debug("Received Pickups: %s", new_received_pickups)
        if self.current_region is not None:
            self.in_cooldown = False
        self.received_pickups = new_recv_as_int
        await self.receive_remote_pickups()

    async def set_remote_pickups(self, remote_pickups: tuple[PickupEntryWithOwner, ...]) -> None:
        self.remote_pickups = remote_pickups
        await self.receive_remote_pickups()

    async def receive_remote_pickups(self) -> None:
        """
        If game is missing pickups, send them to it.
        """
        remote_pickups = self.remote_pickups

        # In this case, the game never communicated with us properly with how many items it had.
        if self.received_pickups is None:
            return

        # Early exit, if we can't send anything to the game, or if we don't need to send it items.
        num_pickups = self.received_pickups
        if num_pickups >= len(remote_pickups) or self.in_cooldown:
            return

        # Mark as cooldown, and send provider, item name, model name and quantity to game
        self.in_cooldown = True
        provider_name, pickup = remote_pickups[num_pickups]
        name, model = pickup.name, pickup.model.name
        # For some reason, the resources here are sorted differently to the patch data factory.
        # There we want the first entry, here we want the last.
        quantity = next(pickup.conditional_resources).resources[-1][1]

        self.logger.debug("Resource changes for %s from %s", pickup.name, provider_name)
        await self.executor.send_pickup_info(provider_name, name, model, quantity, num_pickups + 1)

    async def display_arbitrary_message(self, message: str) -> None:
        escaped_message = message.replace("#", "\\#")  # In GameMaker, '#' is a newline.
        await self.executor.display_message(escaped_message)
