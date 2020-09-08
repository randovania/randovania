import asyncio
import logging
from typing import List

from PySide2.QtCore import QObject
from asyncqt import asyncSlot

from randovania.bitpacking import bitpacking
from randovania.game_connection.connection_backend import ConnectionBase
from randovania.game_description import data_reader
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime import default_data
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.layout.game_patches_serializer import BitPackPickupEntry


class MultiworldClient(QObject):
    latest_message_displayed: int = 0
    _received_messages: List[str]
    _received_pickups: List[PickupEntry]

    def __init__(self, network_client: QtNetworkClient, game_connection: ConnectionBase):
        super().__init__()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.network_client = network_client
        self.game_connection = game_connection
        self._game = data_reader.decode_data(default_data.decode_default_prime2())
        self._received_messages = []
        self._pickups_lock = asyncio.Lock()

    async def start(self):
        self.logger.info("start")

        self.game_connection.LocationCollected.connect(self.on_location_collected)
        self.network_client.GameUpdateNotification.connect(self.on_game_updated)

        await self.refresh_received_pickups()
        async with self._pickups_lock:
            self.latest_message_displayed = len(self._received_messages)
            self.game_connection.set_permanent_pickups(self._received_pickups)

    async def stop(self):
        self.logger.info("stop")

        self.game_connection.LocationCollected.disconnect(self.on_location_collected)
        self.network_client.GameUpdateNotification.disconnect(self.on_game_updated)

        async with self._pickups_lock:
            self.game_connection.set_permanent_pickups([])

    def _decode_pickup(self, data: bytes) -> PickupEntry:
        decoder = bitpacking.BitPackDecoder(data)
        return BitPackPickupEntry.bit_pack_unpack(decoder, "", self._game.resource_database)

    @asyncSlot(int)
    async def on_location_collected(self, location: int):
        # TODO: handle network failure
        self.logger.info(f"on_location_collected: {location}")
        await self.network_client.game_session_collect_pickup(PickupIndex(location))

    async def refresh_received_pickups(self):
        self.logger.info(f"refresh_received_pickups: start")
        async with self._pickups_lock:
            result = await self.network_client.game_session_request_pickups()

            self._received_messages.clear()
            self._received_pickups = []
            self.logger.info(f"refresh_received_pickups: received {len(result)} items")

            for message, data in result:
                self._received_messages.append(message)
                self._received_pickups.append(self._decode_pickup(data))

    @asyncSlot()
    async def on_game_updated(self):
        # TODO: handle network failure
        await self.refresh_received_pickups()

        async with self._pickups_lock:
            self.logger.info(f"on_game_updated: message {self.latest_message_displayed} last displayed")
            while self.latest_message_displayed < len(self._received_messages):
                await self.game_connection.display_message(self._received_messages[self.latest_message_displayed])
                self.latest_message_displayed += 1

            self.game_connection.set_permanent_pickups(self._received_pickups)
