from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import aiohttp
import pytest
import pytest_mock
from aiohttp import web
from aiohttp.test_utils import TestServer

from randovania.games.factorio.exporter.game_exporter import (
    FactorioGameExporter,
    FactorioGameExportParams,
    download_file,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

# bigger than the 8192 chunk size, so the chunked reading is actually exercised
_FILE_CONTENT = bytes(range(256)) * 100


@pytest.fixture
async def file_server() -> AsyncIterator[TestServer]:
    async def get_file(request: web.Request) -> web.StreamResponse:
        return web.Response(body=_FILE_CONTENT)

    async def get_missing(request: web.Request) -> web.StreamResponse:
        raise web.HTTPNotFound

    app = web.Application()
    app.router.add_get("/mod.zip", get_file)
    app.router.add_get("/missing.zip", get_missing)

    server = TestServer(app)
    await server.start_server()
    yield server
    await server.close()


async def test_download_file(file_server: TestServer, tmp_path: Path) -> None:
    path = tmp_path.joinpath("mod.zip")

    await download_file(str(file_server.make_url("/mod.zip")), path)

    assert path.read_bytes() == _FILE_CONTENT


async def test_download_file_error(file_server: TestServer, tmp_path: Path) -> None:
    path = tmp_path.joinpath("mod.zip")

    with pytest.raises(aiohttp.ClientResponseError, match="Not Found"):
        await download_file(str(file_server.make_url("/missing.zip")), path)

    assert not path.exists()


@pytest.mark.parametrize("patch_data_name", ["starter_preset"])
def test_export_game(test_files_dir, mocker: pytest_mock.MockerFixture, patch_data_name: str, tmp_path):
    # Setup
    mock_download_file = mocker.patch("randovania.games.factorio.exporter.game_exporter.download_file")

    json_data = test_files_dir.read_json("patcher_data", "factorio", "factorio", patch_data_name, "world_1.json")
    output_path = tmp_path.joinpath("output", "path")

    exporter = FactorioGameExporter()
    export_params = FactorioGameExportParams(
        spoiler_output=None,
        output_path=output_path,
    )
    progress_update = MagicMock()

    # Run
    exporter.export_game(json_data, export_params, progress_update)

    # Assert
    progress_update.assert_not_called()
    assert output_path.joinpath("mod-settings.dat").is_file()
    assert len(list(output_path.glob("randovania_*.zip"))) == 1
    mock_download_file.assert_awaited_once()
