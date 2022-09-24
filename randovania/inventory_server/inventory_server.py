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

class InventoryServerStatus(enum.Enum):
    STOPPED = "Stopped"
    STARTING = "Starting..."
    RUNNING = "Running"
    STOPPING = "Stopping..."
    ERROR = "ERROR: "

class InventoryServer:

    _logger: logging.Logger
    _thread: threading.Thread
    _game_connection: GameConnection
    _options: Options
    _status: InventoryServerStatus
    _status_change_callbacks: list = []
    _error: Exception | None = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def __init__(self, game_connection: GameConnection, options: Options):
        self._game_connection = game_connection
        self._options = options
        self._set_status(InventoryServerStatus.STOPPED)
        self._setup_logging()
        self._autostart_server()
    
    def _set_status(self, status: InventoryServerStatus, error: Exception | None = None):
        self._error = error
        self._status = status
        self._call_status_change_callbacks()
    
    def _call_status_change_callbacks(self):
        for callback in self._status_change_callbacks:
            callback(self._status)
    
    def _setup_logging(self):
        self._logger = logging.getLogger(type(self).__name__)

    def _autostart_server(self):
        if self._options.inventory_server_autostart:
            self.start()
            self._logger.info("Inventory server autostarted, running on port " + str(self._options.inventory_server_port))

    def start(self):
        self._set_status(InventoryServerStatus.STARTING)
        self._thread = threading.Thread(target=asyncio.run, args=(self._run_websocket_server(),), daemon=True)
        self._thread.start()
    
    async def _run_websocket_server(self):
        try:
            async with websockets.serve(self._respond_to_ws_message, "localhost", int(self._options.inventory_server_port)) as ws:
                self._ws = ws
                self._set_status(InventoryServerStatus.RUNNING)
                await ws.wait_closed()
        except Exception as e:
            self._set_status(InventoryServerStatus.ERROR, e)
    
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
        self._set_status(InventoryServerStatus.STOPPING)
        self._ws.close()
        threading.Thread(target=asyncio.run, args=(self._send_message_to_close_server(),), daemon=True).start()
    
    async def _send_message_to_close_server(self):
        try:
            async with websockets.connect("ws://localhost:" + str(self._options.inventory_server_port)) as websocket:
                await websocket.send("")
        except Exception as e:
            self._set_status(InventoryServerStatus.STOPPED)

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
    
    def add_status_change_callback(self, callback):
        self._status_change_callbacks.append(callback)
        callback(self._status)
    
    def get_status(self):
        return self._status

    def get_error(self):
        return self._error

