from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import factorio_randovania_mod
import factorio_randovania_mod.schema
import pytest

from randovania.games.factorio.exporter.game_exporter import FactorioGameExporter, FactorioGameExportParams

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("patch_data_name", ["starter_preset"])
def test_export_game(test_files_dir, mocker, patch_data_name: str, tmp_path):
    # Setup
    def validate_schema(factorio_path: Path, patch_data: dict, output_folder: Path):
        factorio_randovania_mod.schema.validate(patch_data)

    mock_patch: MagicMock = mocker.patch("factorio_randovania_mod.create", side_effect=validate_schema)

    json_data = test_files_dir.read_json("patcher_data", "factorio", "factorio", patch_data_name, "world_1.json")

    exporter = FactorioGameExporter()
    export_params = FactorioGameExportParams(
        spoiler_output=None,
        input_path=tmp_path.joinpath("input_path"),
        output_path=tmp_path.joinpath("output", "path"),
    )
    progress_update = MagicMock()

    # Run
    exporter.export_game(json_data, export_params, progress_update)

    # Assert
    mock_patch.assert_called_with(
        factorio_path=tmp_path.joinpath("input_path"),
        patch_data=json_data,
        output_folder=tmp_path.joinpath("output", "path"),
    )
    progress_update.assert_not_called()
