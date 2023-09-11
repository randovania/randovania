from __future__ import annotations

import asyncio
import dataclasses
import functools
import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

from randovania.game_connection.builder.connector_builder_option import ConnectorBuilderOption
from randovania.game_description.resources.inventory import Inventory
from randovania.lib.infinite_timer import InfiniteTimer
from randovania.network_common.game_connection_status import GameConnectionStatus

if TYPE_CHECKING:
    import uuid

    from randovania.game_connection.builder.connector_builder import ConnectorBuilder
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.region import Region
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.interface_common.options import Options
    from randovania.interface_common.world_database import WorldDatabase


@dataclasses.dataclass()
class ConnectedGameState:
    id: uuid.UUID
    source: RemoteConnector
    status: GameConnectionStatus
    current_inventory: Inventory = dataclasses.field(default_factory=Inventory.empty)
    collected_indices: set[PickupIndex] = dataclasses.field(default_factory=set)


class GameConnection(QObject):
    BuildersChanged = Signal()
    BuildersUpdated = Signal()
    GameStateUpdated = Signal(ConnectedGameState)

    connection_builders: list[ConnectorBuilder]
    remote_connectors: dict[ConnectorBuilder, RemoteConnector]
    connected_states: dict[RemoteConnector, ConnectedGameState]
    _dt: float = 2.5

    def __init__(self, options: Options, world_database: WorldDatabase):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)
        self._options = options
        self.connection_builders = []
        self.remote_connectors = {}
        self.connected_states = {}
        self.world_database = world_database

        for builder_param in options.connector_builders:
            self.add_connection_builder(builder_param.create_builder())

        self._timer = InfiniteTimer(self._auto_update, self._dt)

    async def start(self):
        self._timer.start()

    async def stop(self):
        for builder, connector in list(self.remote_connectors.items()):
            await connector.force_finish()
            if connector.is_disconnected():
                del self.remote_connectors[builder]
                self.connected_states.pop(connector, None)

        self._timer.stop()

    async def _auto_update(self):
        for builder, connector in list(self.remote_connectors.items()):
            if builder not in self.connection_builders:
                await connector.force_finish()

            if connector.is_disconnected():
                await connector.force_finish()
                del self.remote_connectors[builder]
                self._handle_connector_removed(connector)

        async def try_build_connector(build: ConnectorBuilder):
            c = await build.build_connector()
            if c is not None:
                self.remote_connectors[build] = c
                self._handle_new_connector(c)

        await asyncio.gather(
            *[
                try_build_connector(builder)
                for builder in list(self.connection_builders)
                if builder not in self.remote_connectors
            ]
        )

    def add_connection_builder(self, builder: ConnectorBuilder):
        self.connection_builders.append(builder)
        builder.StatusUpdate.connect(self._on_builder_status_update)
        self._on_builders_changed()

    def remove_connection_builder(self, builder: ConnectorBuilder):
        assert builder in self.connection_builders
        builder.StatusUpdate.disconnect(self._on_builder_status_update)
        self.connection_builders.remove(builder)
        self._on_builders_changed()

    def get_connector_for_builder(self, builder: ConnectorBuilder) -> RemoteConnector | None:
        return self.remote_connectors.get(builder)

    def _on_builders_changed(self):
        with self._options as options:
            options.connector_builders = [
                ConnectorBuilderOption(
                    builder.connector_builder_choice,
                    builder.configuration_params(),
                )
                for builder in self.connection_builders
            ]
        self.BuildersChanged.emit()

    def _on_builder_status_update(self):
        self.BuildersUpdated.emit()

    def _handle_new_connector(self, connector: RemoteConnector):
        connector.PlayerLocationChanged.connect(functools.partial(self._on_player_location_changed, connector))
        connector.PickupIndexCollected.connect(functools.partial(self._on_pickup_index_collected, connector))
        connector.InventoryUpdated.connect(functools.partial(self._on_inventory_updated, connector))
        self.GameStateUpdated.emit(self._ensure_connected_state_exists(connector))

    def _handle_connector_removed(self, connector: RemoteConnector):
        state = self.connected_states.pop(connector, None)
        if state is not None:
            state.status = GameConnectionStatus.Disconnected
            self.GameStateUpdated.emit(state)

    def _ensure_connected_state_exists(self, connector: RemoteConnector) -> ConnectedGameState:
        if connector not in self.connected_states:
            self.connected_states[connector] = ConnectedGameState(
                connector.layout_uuid, connector, GameConnectionStatus.TitleScreen
            )
        return self.connected_states[connector]

    def _on_player_location_changed(self, connector: RemoteConnector, location: tuple[Region | None, Area | None]):
        connected_state = self._ensure_connected_state_exists(connector)
        world, area = location
        if world is None:
            connected_state.status = GameConnectionStatus.TitleScreen
        else:
            connected_state.status = GameConnectionStatus.InGame
        self.GameStateUpdated.emit(connected_state)

    def _on_pickup_index_collected(self, connector: RemoteConnector, index: PickupIndex):
        connected_state = self._ensure_connected_state_exists(connector)
        connected_state.collected_indices.add(index)
        self.GameStateUpdated.emit(connected_state)

    def _on_inventory_updated(self, connector: RemoteConnector, inventory: Inventory):
        connected_state = self._ensure_connected_state_exists(connector)
        connected_state.current_inventory = inventory
        self.GameStateUpdated.emit(connected_state)

    def get_builder_for_connector(self, connector: RemoteConnector) -> ConnectorBuilder:
        for builder, this_connector in self.remote_connectors.items():
            if this_connector == connector:
                return builder
        raise KeyError("Unknown connector")

    def get_backend_choice_for_state(self, state: ConnectedGameState) -> ConnectorBuilderChoice:
        for builder, connector in self.remote_connectors.items():
            if connector == state.source:
                return builder.connector_builder_choice
        raise KeyError("Unknown state")
