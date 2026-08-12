from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock

import open_prime_hunters_rando.prime_hunters_patcher
import pytest

from randovania.games.prime_hunters.exporter.game_exporter import HuntersGameExporter, HuntersGameExportParams

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "patch_data_name",
    [
        "starter_preset",
        "shuffled_force_fields",
        "starting_items_and_energy_with_nothings",
        "two_way_unchecked_portal_shuffle",
        "shuffled_extra_locations_and_skip_planet_intros",
        "no_shuffled_octoliths",
    ],
)
def test_export_game(test_files_dir, mocker, patch_data_name: str, tmp_path):
    # Setup
    def validate_schema(
        input_path: Path, output_path: Path, configuration: dict, export_parsed_files: bool, status_update
    ):
        open_prime_hunters_rando.prime_hunters_patcher.validate(configuration)
        status_update(1.0, "Finished")

    mock_patch: MagicMock = mocker.patch(
        "open_prime_hunters_rando.patch_with_status_update", side_effect=validate_schema
    )

    patch_data = test_files_dir.read_json(
        "patcher_data", "prime_hunters", "prime_hunters", patch_data_name, "world_1.json"
    )

    exporter = HuntersGameExporter()
    export_params = HuntersGameExportParams(
        spoiler_output=None,
        input_path=tmp_path.joinpath("input_file.nds"),
        output_path=tmp_path.joinpath("output", "path"),
    )
    progress_update = MagicMock()

    # Run
    exporter.export_game(patch_data, export_params, progress_update)

    # Assert
    mock_patch.assert_called_with(
        tmp_path.joinpath("input_file.nds"),
        tmp_path.joinpath("output", "path"),
        ANY,
        False,
        ANY,
    )
    progress_update.assert_called_once_with("Finished", 1.0)
