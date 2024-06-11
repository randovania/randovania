from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock

import open_samus_returns_rando.samus_returns_patcher
import pytest

from randovania.games.samus_returns.exporter.game_exporter import (
    MSRGameExporter,
    MSRGameExportParams,
    MSRGameVersion,
    MSRModPlatform,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("patch_data_name", ["starter_preset"])
def test_export_game(test_files_dir, mocker, patch_data_name: str, tmp_path):
    # Setup
    def validate_schema(input_path: Path, input_exheader: Path, output_path: Path, configuration: dict, status_update):
        open_samus_returns_rando.samus_returns_patcher.validate(configuration, input_exheader)
        status_update(1.0, "Finished")

    mock_patch: MagicMock = mocker.patch(
        "open_samus_returns_rando.patch_with_status_update", side_effect=validate_schema
    )

    patch_data = test_files_dir.read_json(
        "patcher_data", "samus_returns", "samus_returns", patch_data_name, "world_1.json"
    )

    exporter = MSRGameExporter()
    export_params = MSRGameExportParams(
        spoiler_output=None,
        input_path=tmp_path.joinpath("input_path"),
        input_exheader=None,
        output_path=tmp_path.joinpath("output", "path"),
        target_platform=MSRModPlatform.LUMA,
        target_version=MSRGameVersion.PAL,
        clean_output_path=False,
        post_export=None,
    )
    progress_update = MagicMock()

    # Run
    exporter.export_game(patch_data, export_params, progress_update)

    # Assert
    mock_patch.assert_called_with(
        tmp_path.joinpath("input_path"),
        None,
        tmp_path.joinpath("output", "path"),
        ANY,
        ANY,
    )
    progress_update.assert_called_once_with("Finished", 1.0)
