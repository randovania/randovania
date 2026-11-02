from __future__ import annotations

import asyncio
import dataclasses
from typing import ClassVar, override

from randovania.game_connection.executor.common_socket_holder import RequestNumberSocketHolder
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals
from randovania.game_connection.executor.socket_executor import BaseSocketExecutor


@dataclasses.dataclass(frozen=True)
class SignalPackets:
    """Which packet type each kind of event arrives in, for one game's protocol."""

    new_inventory: int
    collected_indices: int
    received_pickups: int
    game_state: int
    log_message: int


class SignalSocketExecutor[HolderT: RequestNumberSocketHolder](BaseSocketExecutor[HolderT]):
    """
    A socket executor that reports game events to a connector via signals, driven by a read loop.
    """

    _read_errors: ClassVar[tuple[type[Exception], ...]] = (TimeoutError, OSError, AttributeError)
    """Exceptions during the read loop that mean the connection is gone."""

    _protocol_exception: ClassVar[type[Exception]]
    """Raised when the game breaks its end of the protocol."""

    _length_prefix_size: ClassVar[int] = 4
    """How many bytes the game uses for the little-endian length prefix of a payload."""

    _signal_packets: ClassVar[SignalPackets]

    @override
    def __init__(self, ip: str):
        super().__init__(ip)
        self.signals = ExecutorToConnectorSignals()

    @override
    def disconnect(self) -> None:
        super().disconnect()
        self.signals.connection_lost.emit()

    @override
    def _start_background_tasks(self) -> None:
        self._read_loop_task = asyncio.get_event_loop().create_task(self.read_loop())

    async def read_loop(self) -> None:
        while self.is_connected():
            try:
                await self._read_response()
            except self._read_errors as e:
                self.logger.warning(
                    f"Connection lost. Unable to send packet to {self._ip}:{self._port}: {e} ({type(e)})"
                )
                self.disconnect()

    async def _read_response(self) -> bytes | None:
        if self._socket is None:
            return None
        packet_type: bytes = await asyncio.wait_for(self._socket.reader.read(1), None)
        if len(packet_type) == 0:
            raise OSError("missing packet type")
        if packet_type == b"\x00":
            return None
        return await self._parse_packet(packet_type[0])

    async def _parse_packet(self, packet_type: int) -> bytes | None:
        raise NotImplementedError

    async def _check_header(self) -> None:
        """Confirms the game echoed back the request number we're expecting, then advances it."""
        if self._socket is None:
            return None
        received_number: bytes = await asyncio.wait_for(self._socket.reader.read(1), None)
        if received_number[0] != self._socket.request_number:
            num_as_string = received_number.decode("ascii")
            raise self._protocol_exception(f"Expected response {self._socket.request_number}, got {num_as_string}")
        self._socket.request_number = (self._socket.request_number + 1) % 256

    async def _read_length_prefixed(self) -> bytes:
        """Reads a little-endian length prefix, then that many bytes of payload."""
        assert self._socket is not None
        header = await asyncio.wait_for(self._socket.reader.read(self._length_prefix_size), timeout=15)
        length = int.from_bytes(header, "little")
        return await asyncio.wait_for(self._socket.reader.read(length), timeout=15)

    def _emit_signal_for_packet(self, packet_type: int, response: bytes) -> None:
        """Reports a payload to the connector, based on which packet it arrived in."""
        packets = self._signal_packets
        if packet_type == packets.new_inventory:
            self.signals.new_inventory.emit(response.decode("utf-8"))
        elif packet_type == packets.collected_indices:
            self.signals.new_collected_locations.emit(response)
        elif packet_type == packets.received_pickups:
            self.signals.new_received_pickups.emit(response.decode("utf-8"))
        elif packet_type == packets.game_state:
            self.signals.new_player_location.emit(response.decode("utf-8"))
        elif packet_type == packets.log_message:
            self.logger.debug(response.decode("utf-8"))
