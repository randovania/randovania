from __future__ import annotations

import multiprocessing
from concurrent.futures import Future
from contextlib import contextmanager
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock

import planets_yapr.wrapper  # type: ignore[import-untyped]
import pytest

from randovania.games.planets_zebeth.exporter.game_exporter import (
    PlanetsZebethGameExporter,
    PlanetsZebethGameExportParams,
    _run_patcher,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from multiprocessing.connection import Connection
    from pathlib import Path


@pytest.mark.parametrize("patch_data_name", ["starter_preset", "starter_preset_shuffle_keys"])
def test_do_export_game(test_files_dir, mocker, patch_data_name: str, tmp_path):
    # Setup
    def exec_mock_function(max_workers=None, mp_context=None, initializer=None, initargs=(), max_tasks_per_child=None):
        return None

    def submit_mock_function(
        function: Callable, patch_data: dict, export_params: PlanetsZebethGameExportParams, pipe: Connection
    ):
        pipe.send(("Finished", 1.0))
        return Future()

    mocker.patch("concurrent.futures.ProcessPoolExecutor.__init__", side_effect=exec_mock_function)
    submit = mocker.patch("concurrent.futures.ProcessPoolExecutor.submit", side_effect=submit_mock_function)
    mocker.patch("concurrent.futures.ProcessPoolExecutor.shutdown")

    done_callback = mocker.patch("concurrent.futures.Future.add_done_callback")
    done = mocker.patch("concurrent.futures.Future.done", side_effect=[False, True])
    result = mocker.patch("concurrent.futures.Future.result")

    patch_data = test_files_dir.read_json(
        "patcher_data", "planets_zebeth", "planets_zebeth", patch_data_name, "world_1.json"
    )

    exporter = PlanetsZebethGameExporter()
    export_params = PlanetsZebethGameExportParams(
        spoiler_output=None,
        input_path=tmp_path.joinpath("input_path"),
        output_path=tmp_path.joinpath("output", "path"),
    )
    progress_update = MagicMock()
    randovania_meta = MagicMock()

    # Run
    exporter._do_export_game(patch_data, export_params, progress_update, randovania_meta)

    # Assert
    submit.assert_called_with(ANY, patch_data, export_params, ANY)

    done_callback.assert_called_once()
    assert done.call_count == 2
    result.assert_called_once()


@pytest.mark.parametrize("patch_data_name", ["starter_preset", "starter_preset_shuffle_keys"])
def test_run_patcher(test_files_dir, mocker, patch_data_name: str, tmp_path):
    # Setup
    def finished_status(input_path: Path, output_path: Path, configuration: dict, status_update):
        status_update("Finished", 1.0)

    def mocked_version():
        return "X.Y.Z"

    @contextmanager
    def mocked_load_wrapper():
        yield planets_yapr.wrapper.Wrapper(None)

    patch_game: MagicMock = mocker.patch("planets_yapr.wrapper.Wrapper.patch_game", side_effect=finished_status)
    mocker.patch("planets_yapr.wrapper.Wrapper.get_csharp_version", side_effect=mocked_version)
    mocker.patch("planets_yapr.load_wrapper", side_effect=mocked_load_wrapper)

    receiving_pipe, output_pipe = multiprocessing.Pipe(True)
    patch_data = test_files_dir.read_json(
        "patcher_data", "planets_zebeth", "planets_zebeth", patch_data_name, "world_1.json"
    )

    export_params = PlanetsZebethGameExportParams(
        spoiler_output=None,
        input_path=tmp_path.joinpath("input_path"),
        output_path=tmp_path.joinpath("output", "path"),
    )

    # Run
    _run_patcher(patch_data, export_params, output_pipe)

    # Assert
    patch_game.assert_called_with(
        tmp_path.joinpath("input_path"),
        tmp_path.joinpath("output", "path"),
        patch_data,
        ANY,
    )
    assert receiving_pipe.poll()
