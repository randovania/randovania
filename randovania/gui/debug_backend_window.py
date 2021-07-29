import logging
import random
import struct
from typing import List, Optional, Dict

from PySide2 import QtWidgets, QtCore
from PySide2.QtWidgets import QMainWindow
from qasync import asyncSlot

from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationExecutor
from randovania.game_description import default_database
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world.node import PickupNode
from randovania.games.game import RandovaniaGame
from randovania.games.prime import echoes_dol_versions, all_prime_dol_patches
from randovania.gui.generated.debug_backend_window_ui import Ui_DebugBackendWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.qt_network_client import handle_network_errors
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.network_common.admin_actions import SessionAdminUserAction


class DebugGameBackendChoice:
    @property
    def pretty_text(self):
        return "Debug"


def _echoes_powerup_address(item_index: int) -> int:
    powerups_offset = 0x58
    vector_data_offset = 0x4
    powerup_size = 0xc
    return 0xA00000 + (powerups_offset + vector_data_offset) + (item_index * powerup_size)


class DebugExecutorWindow(MemoryOperationExecutor, Ui_DebugBackendWindow):
    _connected: bool = False
    _timer: QtCore.QTimer
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
        self.gridLayout.addWidget(self.setup_collect_location_combo_button, 0, 0, 1, 2)

        self.collect_location_button.clicked.connect(self._emit_collection)
        self.collect_location_button.setEnabled(False)
        self.collect_randomly_check.stateChanged.connect(self._on_collect_randomly_toggle)
        self._timer = QtCore.QTimer(self.window)
        self._timer.timeout.connect(self._collect_randomly)
        self._timer.setInterval(10000)

        self._used_version = echoes_dol_versions.ALL_VERSIONS[0]
        self._connector = EchoesRemoteConnector(self._used_version)
        self.game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)

        self._game_memory = bytearray(24 * (2 ** 20))
        self._game_memory_initialized = False

    def _on_collect_randomly_toggle(self, value: int):
        if bool(value):
            self._timer.start()
        else:
            self._timer.stop()

    def _collect_randomly(self):
        row = random.randint(0, self.collect_location_combo.count())
        self._collect_location(self.collect_location_combo.itemData(row))

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

    async def _update_inventory_label(self):
        inventory = await self._connector.get_inventory(self)

        s = "<br />".join(
            f"{name} x {quantity.amount}/{quantity.capacity}" for name, quantity in inventory.items()
        )
        self.inventory_label.setText(s)

    def show(self):
        self.window.show()

    def _get_magic_address(self):
        multiworld_magic_item = self.game.resource_database.multiworld_magic_item
        return _echoes_powerup_address(multiworld_magic_item.index)

    def _read_magic(self):
        return self._read_memory_format(">II", self._get_magic_address())

    def _write_magic(self, magic_amount, magic_capacity):
        self._write_memory(self._get_magic_address(), struct.pack(">II", magic_amount, magic_capacity))

    def _emit_collection(self):
        self._collect_location(self.collect_location_combo.currentData())

    def _collect_location(self, location: int):
        new_magic_value = location + 1
        magic_amount, magic_capacity = self._read_magic()
        if magic_amount == 0:
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
                                                        pickup["hud_text"][0].split(", ", 1)[0])
                for pickup in patcher_data["pickups"]
            }

        self.collect_location_combo.clear()
        for index, name in sorted(names.items(), key=lambda t: t[1]):
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

    def _add_power_up(self, registers: Dict[int, int]):
        item_id = registers[4]
        delta = registers[5]
        item = self.game.resource_database.get_item(item_id)
        address = _echoes_powerup_address(item_id)

        amount, capacity = self._read_memory_format(">II", address)
        capacity = max(0, min(capacity + delta, item.max_capacity))
        amount = min(amount, capacity)
        self._write_memory(address, struct.pack(">II", amount, capacity))

    def _incr_pickup(self, registers: Dict[int, int]):
        item_id = registers[4]
        delta = registers[5]
        address = _echoes_powerup_address(item_id)

        amount, capacity = self._read_memory_format(">II", address)
        amount = max(0, min(amount + delta, capacity))
        self._write_memory(address, struct.pack(">I", amount))

    def _decr_pickup(self, registers: Dict[int, int]):
        item_id = registers[4]
        delta = registers[5]
        address = _echoes_powerup_address(item_id)

        amount, capacity = self._read_memory_format(">II", address)
        amount = max(0, min(amount - delta, capacity))
        self._write_memory(address, struct.pack(">I", amount))

    def _display_hud_memo(self, registers):
        string_start = self._used_version.string_display.message_receiver_string_ref
        message_bytes = self._read_memory(string_start, self._used_version.string_display.max_message_size + 2)
        message = message_bytes[:message_bytes.find(b"\x00\x00")].decode("utf-16_be")
        self.messages_list.addItem(message)

    def _handle_remote_execution(self):
        has_message_address = self._used_version.cstate_manager_global + 0x2
        if self._read_memory(has_message_address, 1) == b"\x00":
            return

        self.logger.debug("has code to execute, start parsing ppc")
        registers: Dict[int, int] = {i: 0 for i in range(32)}
        registers[3] = self._used_version.sda2_base

        functions = {
            self._used_version.powerup_functions.add_power_up: self._add_power_up,
            self._used_version.powerup_functions.incr_pickup: self._incr_pickup,
            self._used_version.powerup_functions.decr_pickup: self._decr_pickup,
            self._used_version.string_display.wstring_constructor: lambda reg: None,
            self._used_version.string_display.display_hud_memo: self._display_hud_memo,
        }

        patch_address, _ = all_prime_dol_patches.create_remote_execution_body(self._used_version.string_display, [])
        current_address = patch_address
        while current_address - patch_address < 0x2000:
            instruction = self._read_memory(current_address, 4)
            inst_value = int.from_bytes(instruction, "big")
            header = inst_value >> 26

            def get_signed_16():
                return struct.unpack("h", struct.pack("H", inst_value & 65535))[0]

            if header == 19:
                # subset of branch without address. Consider these blr
                end_address = current_address
                self.logger.debug("blr")
                break

            if header == 14:
                # addi
                output_reg = (inst_value >> 21) & 31
                input_reg = (inst_value >> 16) & 31
                value = get_signed_16()
                if input_reg == 0:
                    self.logger.debug(f"addi r{output_reg}, {value}")
                    registers[output_reg] = value
                else:
                    self.logger.debug(f"addi r{output_reg}, r{input_reg}, {value}")
                    registers[output_reg] = registers[input_reg] + value

            elif header == 15:
                # addis
                output_reg = (inst_value >> 21) & 31
                input_reg = (inst_value >> 16) & 31
                value = inst_value & 65535
                if input_reg == 0:
                    self.logger.debug(f"lis r{output_reg}, {value}")
                    registers[output_reg] = value << 16
                else:
                    self.logger.debug(f"addis r{output_reg}, r{input_reg}, {value}")
                    registers[output_reg] = (registers[input_reg] + value) << 16

            elif header == 18:
                # b and bl (relative branch)
                jump_offset = (inst_value >> 2) & ((2 << 24) - 1)
                link = bool(inst_value & 1)
                address = current_address + (jump_offset * 4)

                if address in functions:
                    function_name = functions[address].__name__
                    functions[address](registers)
                else:
                    function_name = "unknown"

                self.logger.debug(f"b{'l' if link else ''} 0x{address:0x} [{function_name}]")

            elif header == 24:
                # ori
                output_reg = (inst_value >> 21) & 31
                input_reg = (inst_value >> 16) & 31
                value = inst_value & 65535

                self.logger.debug(f"ori r{output_reg}, r{input_reg}, {value}")
                registers[output_reg] = registers[input_reg] | value

            elif header == 36 or header == 38:
                # stw (36) and stb (38)
                input_reg = (inst_value >> 21) & 31
                output_reg = (inst_value >> 16) & 31
                value = get_signed_16()

                if header == 36:
                    inst = 'stw'
                    size = 4
                else:
                    inst = 'stb'
                    size = 1

                self.logger.debug(f"{inst} r{input_reg}, 0x{value:0x} (r{output_reg})")
                # ignore r1, as it's writing to stack
                if output_reg != 1:
                    self._write_memory(registers[output_reg] + value,
                                       registers[input_reg].to_bytes(size, "big"))

            elif header == 32:
                # lwz
                output_reg = (inst_value >> 21) & 31
                input_reg = (inst_value >> 16) & 31
                value = get_signed_16()

                self.logger.debug(f"lwz r{input_reg}, 0x{value:0x} (r{output_reg})")
                ea = value
                if input_reg != 0:
                    ea += registers[input_reg]

                registers[output_reg] = int.from_bytes(self._read_memory(ea, 4), "big")
            else:
                self.logger.debug(f"unsupported instruction: {instruction.hex()}; {header}")

            current_address += 4

        self._write_memory(has_message_address, b"\x00")

    # MemoryOperationExecutor

    @property
    def lock_identifier(self) -> Optional[str]:
        return None

    @property
    def backend_choice(self):
        return DebugGameBackendChoice()

    async def connect(self) -> bool:
        await self._ensure_initialized_game_memory()
        self._handle_remote_execution()
        await self._update_inventory_label()
        self._connected = True
        return True

    async def disconnect(self):
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def perform_memory_operations(self, ops: List[MemoryOperation]) -> Dict[MemoryOperation, bytes]:
        result = {}
        for op in ops:
            op_result = self._memory_operation(op)
            if op_result is not None:
                result[op] = op_result
        return result
