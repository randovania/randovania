from __future__ import annotations

from typing import TYPE_CHECKING

import cryptography.fernet
import pytest
from fastapi.testclient import TestClient
from peewee import SqliteDatabase

from randovania.game.game_enum import RandovaniaGame
from randovania.network_common.configuration import NetworkConfiguration
from randovania.server import database
from randovania.server.configuration import ServerConfiguration

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from randovania.server.server_app import RdvFastAPI


@pytest.fixture
def empty_database():
    old_db = database.db
    try:
        test_db = SqliteDatabase(":memory:")
        database.db = test_db
        with test_db.bind_ctx(database.all_classes):
            test_db.connect(reuse_if_open=True)
            yield test_db
    finally:
        database.db = old_db


@pytest.fixture
def clean_database(empty_database) -> SqliteDatabase:
    empty_database.create_tables(database.all_classes)
    return empty_database


@pytest.fixture
def fernet():
    return cryptography.fernet.Fernet(b"s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=")


@pytest.fixture
def default_game_list(is_dev_version):
    return [g.value for g in RandovaniaGame.sorted_all_games() if g.data.defaults_available_in_game_sessions]


@pytest.fixture(name="db_path")
def db_path_fixture(tmp_path: Path):
    return tmp_path.joinpath("database.db")


@pytest.fixture(name="server_app")
def server_app_fixture(db_path):
    pytest.importorskip("engineio.async_drivers.threading")
    from randovania.server.server_app import ServerApp

    server_config = ServerConfiguration(
        secret_key="key",
        discord_client_secret="5678",
        fernet_key="s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=",
        client_version_checking="ignore",
        database_path=str(db_path),
    )
    configuration = NetworkConfiguration(
        server_address="http://127.0.0.1:5000",
        socketio_path="/socket.io",
        guest_secret="s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=",
        server_config=server_config,
        discord_client_id=1234,
    )

    server = ServerApp(configuration)
    # server.metrics.summary = MagicMock()
    # server.metrics.summary.return_value.side_effect = lambda x: x
    return server


class RdvTestClient(TestClient):
    def __init__(self, app: RdvFastAPI, *args) -> None:
        self.sa = app.sa
        super().__init__(app, *args)


@pytest.fixture(name="test_client")
def test_client_fixture(server_app) -> Generator[RdvTestClient, None, None]:
    with RdvTestClient(server_app.app) as client:
        yield client
