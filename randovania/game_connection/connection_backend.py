import logging
from typing import Optional, List, Tuple

from randovania.game_connection.connection_base import ConnectionBase, GameConnectionStatus, Inventory
from randovania.game_connection.connector.corruption_remote_connector import CorruptionRemoteConnector
from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
from randovania.game_connection.connector.prime1_remote_connector import Prime1RemoteConnector
from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.connector.remote_connector import RemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperationException, MemoryOperation, \
    MemoryOperationExecutor
from randovania.game_connection.memory_executor_choice import MemoryExecutorChoice
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.games.prime import (echoes_dol_versions, prime1_dol_versions,
                                    corruption_dol_versions)

PermanentPickups = Tuple[Tuple[str, PickupEntry], ...]


class ConnectionBackend(ConnectionBase):
    executor: MemoryOperationExecutor
    connector: Optional[RemoteConnector] = None

    _checking_for_collected_index: bool = False
    _inventory: Inventory
    _enabled: bool = True

    # Detected Game
    _world: Optional[World] = None
    _last_world: Optional[World] = None

    # Messages
    message_cooldown: float = 0.0

    # Multiworld
    _expected_game: Optional[RandovaniaGame]
    _permanent_pickups: PermanentPickups

    def __init__(self, executor: MemoryOperationExecutor):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)
        self.executor = executor

        self._inventory = {}
        self._expected_game = None
        self._permanent_pickups = tuple()

    @property
    def current_status(self) -> GameConnectionStatus:
        if not self.executor.is_connected():
            return GameConnectionStatus.Disconnected

        if self.connector is None:
            return GameConnectionStatus.UnknownGame

        if self._expected_game is not None and self._expected_game != self.connector.game_enum:
            return GameConnectionStatus.WrongGame

        if self._world is None:
            return GameConnectionStatus.TitleScreen

        elif not self.checking_for_collected_index:
            return GameConnectionStatus.TrackerOnly

        else:
            return GameConnectionStatus.InGame

    @property
    def backend_choice(self) -> MemoryExecutorChoice:
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

    async def _identify_game(self) -> Optional[RemoteConnector]:
        all_connectors: List[PrimeRemoteConnector] = [
            Prime1RemoteConnector(version)
            for version in prime1_dol_versions.ALL_VERSIONS
        ]
        all_connectors.extend([
            EchoesRemoteConnector(version)
            for version in echoes_dol_versions.ALL_VERSIONS
        ])
        all_connectors.extend([
            CorruptionRemoteConnector(version)
            for version in corruption_dol_versions.ALL_VERSIONS
        ])
        read_first_ops = [
            MemoryOperation(connectors.version.build_string_address,
                            read_byte_count=min(len(connectors.version.build_string), 4))
            for connectors in all_connectors
        ]
        try:
            first_ops_result = await self.executor.perform_memory_operations(read_first_ops)
        except (RuntimeError, MemoryOperationException) as e:
            self.logger.debug(f"Unable to probe for game version: {e}")
            return None

        possible_connectors = [
            connectors
            for connectors, read_op in zip(all_connectors, read_first_ops)
            if first_ops_result.get(read_op) == connectors.version.build_string[:4]
        ]

        for connector in possible_connectors:
            try:
                is_version = await connector.is_this_version(self.executor)
            except (RuntimeError, MemoryOperationException) as e:
                return None

            if is_version:
                self.logger.info(f"identified game as {connector.game_enum.long_name}: {connector.version.description}")
                return connector

    def get_current_inventory(self) -> Inventory:
        return self._inventory

    def set_expected_game(self, game: Optional[RandovaniaGame]):
        self._expected_game = game

    def set_permanent_pickups(self, pickups: PermanentPickups):
        self._permanent_pickups = pickups

    async def update_current_inventory(self):
        self._inventory = await self.connector.get_inventory(self.executor)

    async def _multiworld_interaction(self):
        if self._expected_game is None:
            return

        locations, patches = await self.connector.known_collected_locations(self.executor)
        for location in locations:
            await self._emit_location_collected(self.connector.game_enum, location)

        if patches:
            await self.connector.execute_remote_patches(self.executor, patches)
        else:
            patches, has_message = await self.connector.find_missing_remote_pickups(
                self.executor, self._inventory, self._permanent_pickups, self.message_cooldown > 0.0,
            )
            if patches and (self.message_cooldown <= 0.0 or not has_message):
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

    def _is_unexpected_game(self):
        """
        If has an expected game, True if connected game isn't that.
        Otherwise, False.
        :return:
        """
        if self._expected_game is not None:
            return self._expected_game != self.connector.game_enum
        return False

    async def update(self, dt: float):
        if not self._enabled:
            return

        if not await self.executor.connect():
            return

        if self.connector is None or self._is_unexpected_game() or self._world is None:
            self.connector = await self._identify_game()

        try:
            if self.connector is not None and not self._is_unexpected_game():
                await self._interact_with_game(dt)

        except MemoryOperationException as e:
            self.logger.warning(f"Unable to perform memory operations: {e}")
            self._world = None
