import logging

from randovania.game_connection.connector.remote_connector_v2 import RemoteConnectorV2
from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.connection_base import ConnectionBase, GameConnectionStatus, Inventory
from randovania.game_connection.memory_executor_choice import ConnectionBuilderChoice
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame

PermanentPickups = tuple[tuple[str, PickupEntry], ...]

class ConnectionBackend(ConnectionBase):
    connector: RemoteConnectorV2 | None = None
    connector_builder: ConnectorBuilder | None = None

    _checking_for_collected_index: bool = False
    _inventory: Inventory
    _enabled: bool = True

    # Detected Game
    _world: World | None = None
    _last_world: World | None = None

    # Multiworld
    _expected_game: RandovaniaGame | None
    _permanent_pickups: PermanentPickups

    def __init__(self, connector_builder: ConnectorBuilder):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)
        self.connector_builder = connector_builder

        self._inventory = {}
        self._expected_game = None
        self._permanent_pickups = tuple()

    @property
    def current_status(self) -> GameConnectionStatus:
        if self.connector_builder is None or self.connector is None:
            return GameConnectionStatus.UnknownGame

        if not self.connector.executor.is_connected():
            return GameConnectionStatus.Disconnected

        if self._expected_game is not None and self._expected_game != self.connector.game_enum:
            return GameConnectionStatus.WrongGame

        if self._world is None:
            return GameConnectionStatus.TitleScreen

        elif not self.checking_for_collected_index:
            return GameConnectionStatus.TrackerOnly

        else:
            return GameConnectionStatus.InGame

    def _notify_status(self):
        raise NotImplementedError()

    @property
    def connector_builder_choice(self) -> ConnectionBuilderChoice:
        return self.connector_builder.connector_builder_choice

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def lock_identifier(self) -> str | None:
        return self.connector.executor.lock_identifier if self.connector is not None else None

    @property
    def checking_for_collected_index(self):
        return self._checking_for_collected_index

    @checking_for_collected_index.setter
    def checking_for_collected_index(self, value: bool):
        self._checking_for_collected_index = value

    def set_connection_enabled(self, value: bool):
        self._enabled = value
        if not value:
            self.connector = None


    def get_current_inventory(self) -> Inventory:
        return self._inventory

    async def set_connector_builder(self, connector_builder: ConnectorBuilder):
        if self.connector is not None:
            await self.connector.executor.disconnect()
        self.connector_builder = connector_builder
        self.connector = await connector_builder.build_connector()
        self._notify_status()

    @property
    def expected_game(self):
        return self._expected_game

    def set_expected_game(self, game: RandovaniaGame | None):
        self._expected_game = game

    def set_permanent_pickups(self, pickups: PermanentPickups):
        self.logger.info("num permanent pickups: %d", len(pickups))
        self._permanent_pickups = pickups

    async def update_current_inventory(self):
        self._inventory = await self.connector.get_inventory()

    async def _multiworld_interaction(self):
        if self._expected_game is None:
            return

        locations = await self.connector.known_collected_locations()
        if len(locations) != 0:
            for location in locations:
                await self._emit_location_collected(self.connector.game_enum, location)
        else:
            await self.connector.receive_remote_pickups(
                self._inventory, self._permanent_pickups
            )

    async def _interact_with_game(self, dt: float):
        has_pending_op, world = await self.connector.current_game_status()
        self._world = world
        if world is not None:
            await self.update_current_inventory()
            if not has_pending_op:
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

        # check if we have a connector_builder and a connector
        if self.connector_builder is None:
            return
        elif self.connector is None:
            self.connector = await self.connector_builder.build_connector()

        # connector can still be none e.g. dolphin can not hook
        if self.connector is None:
            return

        if not await self.connector_builder.executor.connect():
            return

        try:
            if self.connector is not None and not self._is_unexpected_game():
                await self._interact_with_game(dt)

        # could be a little more precise but other games could return network related errors
        except Exception as e:
            self.logger.warning(f"Exception: {e}")
            self._world = None
            if self.connector is not None:
                await self.connector.executor.disconnect()

