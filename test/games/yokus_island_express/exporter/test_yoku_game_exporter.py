from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock

import open_yoku_rando.yoku_patcher
import pytest

from randovania.games.yokus_island_express.exporter.game_exporter import YokuGameExporter, YokuGameExportParams

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("patch_data_name", ["starter_preset", "shuffled_trackers_fruit_beacons"])
def test_export_game(test_files_dir, mocker, patch_data_name: str, tmp_path):
    # Setup
    def validate_schema(input_path: Path, configuration: dict, status_update):
        open_yoku_rando.yoku_patcher.validate(configuration)
        status_update(1.0, "Finished")

    mock_patch: MagicMock = mocker.patch("open_yoku_rando.patch_with_status_update", side_effect=validate_schema)

    patch_data = test_files_dir.read_json(
        "patcher_data", "yokus_island_express", "yokus_island_express", patch_data_name, "world_1.json"
    )

    exporter = YokuGameExporter()
    export_params = YokuGameExportParams(
        spoiler_output=None,
        input_path=tmp_path.joinpath("input_path"),
    )
    progress_update = MagicMock()

    # Run
    exporter.export_game(patch_data, export_params, progress_update)

    # Assert
    mock_patch.assert_called_with(
        tmp_path.joinpath("input_path"),
        ANY,
        ANY,
    )
    progress_update.assert_called_once_with("Finished", 1.0)
