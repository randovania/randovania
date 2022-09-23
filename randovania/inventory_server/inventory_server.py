import asyncio
import threading
import websockets
import logging
import json
import enum
from PySide6 import QtWidgets
from randovania.game_connection.game_connection import GameConnection
from randovania.game_connection.connection_base import Inventory, GameConnectionStatus
from randovania.interface_common.options import Options

class InventoryServer:

    _logger: logging.Logger
    _thread: threading.Thread
    _game_connection: GameConnection
    _options: Options
    _is_running: bool

    @property
    def is_running(self) -> bool:
        return self._is_running

    def __init__(self, game_connection: GameConnection, options: Options):
        self._game_connection = game_connection
        self._options = options
        self._is_running = False
        self._setup_logging()
        self._autostart_server()
    
    def _setup_logging(self):
        self._logger = logging.getLogger(type(self).__name__)

    def _autostart_server(self):
        if self._options.inventory_server_autostart:
            self.start()
            self._logger.info("Inventory server autostarted, running on port " + str(self._options.inventory_server_port))

    def start(self):
        self._thread = threading.Thread(target=asyncio.run, args=(self._run_websocket_server(),), daemon=True)
        self._is_running = True
        self._thread.start()
    
    async def _run_websocket_server(self):
       async with websockets.serve(self._respond_to_ws_message, "localhost", int(self._options.inventory_server_port)) as ws:
           self._ws = ws
           await ws.wait_closed()
    
    async def _respond_to_ws_message(self, websocket):
        async for message in websocket:
            await self._send_inventory_message(websocket)
    
    async def _send_inventory_message(self, websocket):
        raw_message = self._get_raw_inventory_message()
        message = json.dumps(raw_message)
        await websocket.send(message)

    def _get_raw_inventory_message(self):
        return {
            "status": self._get_raw_status(),
            "status_pretty": self._get_raw_status_pretty(),
            "inventory": self._get_raw_inventory(),
        }

    def _get_raw_status(self):
        return self._game_connection.current_status.value

    def _get_raw_status_pretty(self):
        return self._game_connection.pretty_current_status

    def _get_raw_inventory(self):
        ret = {}
        for k, v in self._game_connection.get_current_inventory().items():
            ret[k.short_name] = {"amount": v.amount, "capacity": v.capacity}
        return ret

    def stop(self):
        self._is_running = False
        self._ws.close()
        threading.Thread(target=asyncio.run, args=(self._send_message_to_close_server(),), daemon=True).start()
    
    async def _send_message_to_close_server(self):
        async with websockets.connect("ws://localhost:" + str(self._options.inventory_server_port)) as websocket:
            await websocket.send("")

    def set_autostart(self, value: bool):
        with self._options as options:
            options.inventory_server_autostart = value

    def get_autostart(self):
        return self._options.inventory_server_autostart

    def set_port(self, value: int):
        with self._options as options:
            self._options.inventory_server_port = value

    def get_port(self):
        return self._options.inventory_server_port

