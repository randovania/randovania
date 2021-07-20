import copy
import logging
from typing import Optional, List, Dict, Tuple

from randovania.game_connection.backend_choice import GameBackendChoice
from randovania.game_connection.connection_base import ConnectionBase, InventoryItem, GameConnectionStatus
from randovania.game_connection.executor.memory_operation import MemoryOperationException, MemoryOperation, \
    MemoryOperatorExecutor
from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.connector.remote_connector import RemoteConnector
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import CurrentResources, \
    add_resource_gain_to_current_resources
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.games.prime import (echoes_dol_versions, prime1_dol_versions,
                                    corruption_dol_versions)


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


def _prime1_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x24
    vector_data_offset = 0x4
    powerup_size = 0x8
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


def _echoes_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x58
    vector_data_offset = 0x4
    powerup_size = 0xc
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


def _corruption_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x50
    vector_data_offset = 0x4
    powerup_size = 0xc
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


def _add_pickup_to_resources(pickup: PickupEntry, inventory: CurrentResources) -> CurrentResources:
    return add_resource_gain_to_current_resources(
        pickup.resource_gain(inventory),
        copy.copy(inventory)
    )


def _capacity_for(item: ItemResourceInfo,
                  changed_items: Dict[ItemResourceInfo, InventoryItem],
                  inventory: Dict[ItemResourceInfo, InventoryItem]):
    if item in changed_items:
        return changed_items[item].capacity
    elif item in inventory:
        return inventory[item].capacity
    else:
        return 0


class ConnectionBackend(ConnectionBase):
    executor: MemoryOperatorExecutor
    connector: Optional[RemoteConnector] = None

    _checking_for_collected_index: bool = False
    _games: Dict[RandovaniaGame, GameDescription]
    _inventory: Dict[ItemResourceInfo, InventoryItem]
    _enabled: bool = True

    # Detected Game
    _world: Optional[World] = None
    _last_world: Optional[World] = None

    # Messages
    message_queue: List[str]
    message_cooldown: float = 0.0
    _last_message_size: int = 0

    # Multiworld
    _permanent_pickups: List[Tuple[str, PickupEntry]]

    def __init__(self, executor: MemoryOperatorExecutor):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)
        self.executor = executor

        self._inventory = {}
        self.message_queue = []
        self._permanent_pickups = []

    @property
    def current_status(self) -> GameConnectionStatus:
        if not self.executor.is_connected():
            return GameConnectionStatus.Disconnected

        if self.connector is None:
            return GameConnectionStatus.UnknownGame

        if self._world is None:
            return GameConnectionStatus.TitleScreen

        elif not self.checking_for_collected_index:
            return GameConnectionStatus.TrackerOnly

        else:
            return GameConnectionStatus.InGame

    @property
    def backend_choice(self) -> GameBackendChoice:
        return self.executor.backend_choice

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def lock_identifier(self) -> Optional[str]:
        return self.executor.lock_identifier

    @property
    def checking_for_collected_index(self):
        return self._checking_for_collected_index

    @checking_for_collected_index.setter
    def checking_for_collected_index(self, value):
        self._checking_for_collected_index = value

    def set_connection_enabled(self, value: bool):
        self._enabled = value
        if not value:
            self.connector = None

    async def _identify_game(self) -> bool:
        if self.connector is not None:
            return True

        all_versions = (
                echoes_dol_versions.ALL_VERSIONS
                + prime1_dol_versions.ALL_VERSIONS
                + corruption_dol_versions.ALL_VERSIONS
        )
        read_first_ops = [
            MemoryOperation(version.build_string_address, read_byte_count=min(len(version.build_string), 4))
            for version in all_versions
        ]
        try:
            first_ops_result = await self.executor.perform_memory_operations(read_first_ops)
        except (RuntimeError, MemoryOperationException) as e:
            self.logger.debug(f"Unable to probe for game version: {e}")
            return False

        possible_connectors = [
            PrimeRemoteConnector(version)
            for version, read_op in zip(all_versions, read_first_ops)
            if first_ops_result.get(read_op) == version.build_string[:4]
        ]

        for connector in possible_connectors:
            try:
                is_version = await connector.is_this_version(self.executor)
            except (RuntimeError, MemoryOperationException) as e:
                return False

            if is_version:
                self.connector = connector
                self.logger.info(f"identified game as {connector.version.description}")
                return True

        return False

    def get_current_inventory(self) -> Dict[ItemResourceInfo, InventoryItem]:
        return self._inventory

    def set_permanent_pickups(self, pickups: List[Tuple[str, PickupEntry]]):
        self._permanent_pickups = pickups

    async def update_current_inventory(self):
        self._inventory = await self.connector.get_inventory(self.executor)

    async def _multiworld_interaction(self):
        locations, patches = await self.connector.known_collected_locations(self.executor)
        for location in locations:
            await self._emit_location_collected(location.index)

        if patches:
            await self.connector.execute_remote_patches(self.executor, patches)
        else:
            patches, has_message = await self.connector.find_missing_remote_pickups(self.executor, self._inventory,
                                                                                    self._permanent_pickups)
            if self.message_cooldown <= 0.0 or not has_message:
                await self.connector.execute_remote_patches(self.executor, patches)
                if has_message:
                    self.message_cooldown = 4.0

    async def _interact_with_game(self, dt):
        has_pending_op, world = await self.connector.current_game_status(self.executor)
        self._world = world
        if world is not None:
            await self.update_current_inventory()
            if not has_pending_op:
                self.message_cooldown = max(self.message_cooldown - dt, 0.0)
                await self._multiworld_interaction()

    async def update(self, dt: float):
        if not self._enabled:
            return

        if not await self.executor.connect():
            return

        if not await self._identify_game():
            return

        try:
            await self._interact_with_game(dt)

        except MemoryOperationException as e:
            self.logger.warning(f"Unable to perform memory operations: {e}")
            self._world = None
