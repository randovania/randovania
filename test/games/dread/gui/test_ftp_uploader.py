from __future__ import annotations

import platform
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock, call

import pytest

from randovania.lib.ftp_uploader import FtpUploader

if TYPE_CHECKING:
    from pytest_localftpserver.servers import PytestLocalFTPServer


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
        ip="localhost",
        port=ftpserver.server_port,
        local_path=tmp_path.joinpath("local"),
        remote_path="/remote",
    )

    # Run
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
