import logging
import struct
from typing import List, Optional, Dict

from PySide2 import QtWidgets
from PySide2.QtWidgets import QMainWindow
from qasync import asyncSlot

from randovania.game_connection.connection_backend import _echoes_powerup_offset
from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationExecutor
from randovania.game_description import default_database
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world.node import PickupNode
from randovania.games.game import RandovaniaGame
from randovania.games.prime import echoes_dol_versions
from randovania.gui.generated.debug_backend_window_ui import Ui_DebugBackendWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.qt_network_client import handle_network_errors
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.network_common.admin_actions import SessionAdminUserAction


class DebugGameBackendChoice:
    @property
    def pretty_text(self):
        return "Debug"


class DebugBackendWindow(MemoryOperationExecutor, Ui_DebugBackendWindow):
    _connected: bool = False
    pickups: List[PickupEntry]

    def __init__(self):
        super().__init__()
        self.logger.setLevel(logging.DEBUG)
        self.window = QMainWindow()
        self.setupUi(self.window)
        common_qt_lib.set_default_window_icon(self.window)

        self.pickups = []

        self.collect_location_combo.setVisible(False)
        self.setup_collect_location_combo_button = QtWidgets.QPushButton(self.window)
        self.setup_collect_location_combo_button.setText("Load list of locations")
        self.setup_collect_location_combo_button.clicked.connect(self._setup_locations_combo)
        self.gridLayout.addWidget(self.setup_collect_location_combo_button, 1, 0, 1, 1)

        self.collect_location_button.clicked.connect(self._emit_collection)
        self.collect_location_button.setEnabled(False)

        self._used_version = echoes_dol_versions.ALL_VERSIONS[0]
        self.game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)

        self._game_memory = bytearray(24 * (2 ** 20))
        self._game_memory_initialized = False

    async def _ensure_initialized_game_memory(self):
        if self._game_memory_initialized:
            return

        world = self.game.world_list.worlds[0]

        await self.perform_memory_operations([
            # Build String
            MemoryOperation(self._used_version.build_string_address, write_bytes=self._used_version.build_string),

            # current CWorld
            MemoryOperation(self._used_version.game_state_pointer, offset=4,
                            write_bytes=world.world_asset_id.to_bytes(4, "big")),

            # CPlayer VTable
            MemoryOperation(self._used_version.cstate_manager_global + 0x14fc, offset=0,
                            write_bytes=self._used_version.cplayer_vtable.to_bytes(4, "big")),

            # CPlayerState
            MemoryOperation(self._used_version.cstate_manager_global + 0x150c,
                            write_bytes=0xA00000.to_bytes(4, "big")),
        ])

        self._game_memory_initialized = True

    def _read_memory(self, address: int, count: int):
        address &= ~0x80000000
        return self._game_memory[address:address + count]

    def _read_memory_format(self, format_string: str, address: int):
        return struct.unpack_from(format_string, self._game_memory, address & ~0x80000000)

    def _write_memory(self, address: int, data: bytes):
        address &= ~0x80000000
        self._game_memory[address:address + len(data)] = data
        self.logger.info(f"Wrote {data.hex()} to {hex(address)}")

    @property
    def lock_identifier(self) -> Optional[str]:
        return None

    @property
    def backend_choice(self):
        return DebugGameBackendChoice()

    async def connect(self) -> bool:
        await self._ensure_initialized_game_memory()
        self._read_message_from_game()
        await self._update_inventory_label()
        self._connected = True
        return True

    async def disconnect(self):
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def _update_inventory_label(self):
        connector = PrimeRemoteConnector(self._used_version)
        inventory = await connector.get_inventory(self)

        s = "<br />".join(
            f"{name} x {quantity.amount}/{quantity.capacity}" for name, quantity in inventory.items()
        )
        self.inventory_label.setText(s)

    def show(self):
        self.window.show()

    def _get_magic_address(self):
        multiworld_magic_item = self.game.resource_database.multiworld_magic_item
        magic_address = 0xA00000 + _echoes_powerup_offset(multiworld_magic_item.index)
        return magic_address

    def _read_magic(self):
        return self._read_memory_format(">II", self._get_magic_address())

    def _write_magic(self, magic_amount, magic_capacity):
        self._write_memory(self._get_magic_address(), struct.pack(">II", magic_amount, magic_capacity))

    def _emit_collection(self):
        new_magic_value = self.collect_location_combo.currentData() + 1
        magic_amount, magic_capacity = self._read_magic()
        magic_amount += new_magic_value
        magic_capacity += new_magic_value
        self._write_magic(magic_amount, magic_capacity)

    @asyncSlot()
    @handle_network_errors
    async def _setup_locations_combo(self):
        network_client = common_qt_lib.get_network_client()
        game_session = network_client.current_game_session
        user = network_client.current_user

        game = self.game
        index_to_name = {
            node.pickup_index.index: game.world_list.area_name(area)
            for world, area, node in game.world_list.all_worlds_areas_nodes
            if isinstance(node, PickupNode)
        }

        if game_session is None:
            names = index_to_name
        else:
            patcher_data = await network_client.session_admin_player(user.id,
                                                                     SessionAdminUserAction.CREATE_PATCHER_FILE,
                                                                     BaseCosmeticPatches().as_json)
            names = {
                pickup["pickup_index"]: "{}: {}".format(index_to_name[pickup["pickup_index"]],
                                                        pickup["hud_text"][0])
                for pickup in patcher_data["pickups"]
            }

        self.collect_location_combo.clear()
        for index, name in sorted(names.items()):
            self.collect_location_combo.addItem(name, index)

        self.collect_location_button.setEnabled(True)
        self.collect_location_combo.setVisible(True)
        self.setup_collect_location_combo_button.deleteLater()

    def clear(self):
        self.messages_list.clear()
        self.pickups.clear()

    def _memory_operation(self, op: MemoryOperation) -> Optional[bytes]:
        op.validate_byte_sizes()

        address = op.address
        if op.offset is not None:
            address = self._read_memory_format(">I", address)[0]
            address += op.offset

        result = None
        if op.read_byte_count is not None:
            result = self._read_memory(address, op.read_byte_count)
        if op.write_bytes is not None:
            self._write_memory(address, op.write_bytes)
        return result

    async def perform_memory_operations(self, ops: List[MemoryOperation]) -> Dict[MemoryOperation, bytes]:
        result = {}
        for op in ops:
            op_result = self._memory_operation(op)
            if op_result is not None:
                result[op] = op_result
        return result

    def _read_message_from_game(self):
        has_message_address = self._used_version.cstate_manager_global + 0x2
        if self._read_memory(has_message_address, 1) == b"\x00":
            return

        string_start = self._used_version.string_display.message_receiver_string_ref
        message_bytes = self._read_memory(string_start, self._used_version.string_display.max_message_size + 2)
        message = message_bytes[:message_bytes.find(b"\x00\x00")].decode("utf-16_be")

        self.messages_list.addItem(message)
        self._write_memory(has_message_address, b"\x00")
