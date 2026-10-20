from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, ClassVar, TypeGuard

from randovania.game_connection.executor.common_socket_holder import CommonSocketHolder

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter


class BaseSocketExecutor[HolderT: CommonSocketHolder]:
    """
    Common lifecycle for executors that talk to the game over a TCP socket.

    Subclasses provide the handshake and, optionally, background tasks. Everything around it - connecting,
    reporting failures, disconnecting - is shared.
    """

    _port: int
    _socket: HolderT | None = None
    _socket_error: Exception | None = None

    _connect_timeout: ClassVar[float | None] = None
    """When set, opening the connection is wrapped in a `wait_for` with this timeout."""

    _connect_errors: ClassVar[tuple[type[Exception], ...]] = (TimeoutError, OSError, UnicodeError)
    """Exceptions during `connect` that are reported as a failed connection instead of propagating."""

    def __init__(self, ip: str):
        self.logger = logging.getLogger(type(self).__name__)
        self._ip = ip

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def lock_identifier(self) -> str | None:
        return None

    @staticmethod
    def _is_socket_connected(socket: HolderT | None) -> TypeGuard[HolderT]:
        return socket is not None

    def is_connected(self) -> bool:
        return self._is_socket_connected(self._socket)

    async def connect(self) -> str | None:
        if self.is_connected():
            return None

        try:
            self._socket_error = None
            self.logger.debug("Connecting to %s:%d.", self._ip, self._port)
            connection = asyncio.open_connection(self._ip, self._port)
            if self._connect_timeout is not None:
                reader, writer = await asyncio.wait_for(connection, timeout=self._connect_timeout)
            else:
                reader, writer = await connection

            error = await self._perform_handshake(reader, writer)
            if error is not None:
                self._socket = None
                writer.close()
                return error

            self._start_background_tasks()
            self.logger.info("Connected")
            return None

        except self._connect_errors as e:
            # UnicodeError is for some invalid ip addresses
            self._socket = None
            self._socket_error = e
            return self._message_for_connect_error(e)

    def _message_for_connect_error(self, error: Exception) -> str:
        return f"Unable to connect to {self._ip}:{self._port} - ({type(error).__name__}) {error}"

    async def _perform_handshake(self, reader: StreamReader, writer: StreamWriter) -> str | None:
        """
        Negotiates with the game and assigns `self._socket` on success.

        Returns an error message when the handshake fails in a way that isn't exceptional, otherwise None.
        Raising one of `_connect_errors` is also a valid way of reporting a failure.
        """
        raise NotImplementedError

    def _start_background_tasks(self) -> None:
        """Called after a successful handshake, for executors that need long running tasks."""

    def disconnect(self) -> None:
        socket = self._socket
        self._socket = None
        if socket is not None:
            socket.writer.close()
