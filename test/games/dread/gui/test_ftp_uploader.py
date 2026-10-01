from __future__ import annotations

import platform
import socket
import time
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock, call

import pytest

from randovania.lib.ftp_uploader import FtpUploader

if TYPE_CHECKING:
    from pytest_localftpserver.servers import PytestLocalFTPServer


def _wait_until_listening(port: int, timeout: float = 5.0) -> None:
    """Waits until the ftp server accepts connections.

    The ftpserver fixture binds its socket in the main thread, but only calls listen() later,
    from the thread that serves the requests. Connecting in between fails with
    ConnectionRefusedError, so poll the port instead of assuming the server is already up.
    """
    deadline = time.monotonic() + timeout
    while True:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                return
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.1)


@pytest.mark.skipif(platform.system() == "Darwin", reason="ftpserver fails on macOS")
def test_upload(ftpserver: PytestLocalFTPServer, tmp_path):
    progress_update = MagicMock()

    server_home = Path(ftpserver.server_home)
    server_home.joinpath("neighbor").mkdir()
    server_home.joinpath("neighbor", "f.txt").write_text("1234")
    server_home.joinpath("remote").mkdir()
    server_home.joinpath("remote", "old.txt").write_text("1234")
    server_home.joinpath("remote", "foo").mkdir()

    tmp_path.joinpath("local").mkdir()
    tmp_path.joinpath("local", "a.txt").write_text("1234")
    tmp_path.joinpath("local", "b.txt").write_text("1234")
    tmp_path.joinpath("local", "bar").mkdir()

    ftp = FtpUploader(
        auth=(ftpserver.username, ftpserver.password),
        ip="127.0.0.1",
        port=ftpserver.server_port,
        local_path=tmp_path.joinpath("local"),
        remote_path="/remote",
    )

    # Run
    _wait_until_listening(ftpserver.server_port)
    ftp(progress_update)

    # Assert
    assert sorted(server_home.rglob("*")) == [
        server_home.joinpath("neighbor"),
        server_home.joinpath("neighbor", "f.txt"),
        server_home.joinpath("remote"),
        server_home.joinpath("remote", "a.txt"),
        server_home.joinpath("remote", "b.txt"),
        server_home.joinpath("remote", "bar"),
    ]
    progress_update.assert_has_calls(
        [
            call("Uploaded /remote/a.txt", ANY),
            call("Uploaded /remote/b.txt", ANY),
            call("Uploaded /remote/bar", ANY),
        ],
        any_order=True,
    )
