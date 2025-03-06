from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from randovania.games.factorio.exporter.game_exporter import FactorioGameExporter, FactorioGameExportParams


@pytest.mark.parametrize("patch_data_name", ["starter_preset"])
def test_export_game(test_files_dir, mocker, patch_data_name: str, tmp_path):
    # Setup
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
    assert len(list(output_path.glob("randovania-assets_*.zip"))) == 1
