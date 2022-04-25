from pathlib import Path
from unittest.mock import MagicMock, call, ANY

from randovania.games.dread.gui.dialog.ftp_uploader import FtpUploader


def test_upload(ftpserver, tmp_path):
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
    progress_update.assert_has_calls([
        call('Uploaded /remote/a.txt', ANY),
        call('Uploaded /remote/b.txt', ANY),
        call('Uploaded /remote/bar', ANY),
    ], any_order=True)
