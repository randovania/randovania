from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock

import mars_patcher
import pytest

from randovania.games.zero_mission.exporter.game_exporter import MZMGameExporter, MZMGameExportParams

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "patch_data_name",
    ["starter_preset"],
)
def test_export_game(test_files_dir, mocker, patch_data_name: str, tmp_path):
    # Setup
    def validate_schema(input_path: Path, output_path: Path, configuration: dict, status_update):
        mars_patcher.patcher.validate_patch_data_zm(configuration)
        status_update("Finished", 1.0)

    mock_patch: MagicMock = mocker.patch("mars_patcher.patcher.patch", side_effect=validate_schema)

    patch_data = test_files_dir.read_json(
        "patcher_data", "zero_mission", "zero_mission", patch_data_name, "world_1.json"
    )

    exporter = MZMGameExporter()
    export_params = MZMGameExportParams(
        spoiler_output=None,
        input_path=tmp_path.joinpath("input_path"),
        output_path=tmp_path.joinpath("output", "path"),
    )
    progress_update = MagicMock()

    # Run
    exporter.export_game(patch_data, export_params, progress_update)

    # Assert
    mock_patch.assert_called_with(
        os.fspath(tmp_path.joinpath("input_path")),
        os.fspath(tmp_path.joinpath("output", "path")),
        ANY,
        ANY,
    )
    progress_update.assert_called_once_with("Finished", 1.0)
