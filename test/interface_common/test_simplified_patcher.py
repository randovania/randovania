from pathlib import Path
from unittest.mock import MagicMock

import pytest

from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.layout.permalink import Permalink


@pytest.mark.parametrize("games_path_exist", [False, True])
@pytest.mark.parametrize("backup_path_exist", [False, True])
def test_delete_files_location(tmpdir,
                               games_path_exist: bool,
                               backup_path_exist: bool,
                               ):
    # Setup
    data_dir = Path(str(tmpdir.join("user_data_dir")))
    options = Options(data_dir)

    game_files = tmpdir.join("user_data_dir", "extracted_game")
    if games_path_exist:
        game_files.ensure_dir()
        game_files.join("random.txt").write_text("yay", "utf-8")

    backup_files = tmpdir.join("user_data_dir", "backup")
    if backup_path_exist:
        backup_files.ensure_dir()
        backup_files.join("random.txt").write_text("yay", "utf-8")

    # Run
    simplified_patcher.delete_files_location(options)

    # Assert
    assert not game_files.exists()
    assert not backup_files.exists()


def test_generate_layout(mocker):
    # Setup
    options: Options = MagicMock()
    permalink: Permalink = MagicMock()
    progress_update = MagicMock()

    mock_generate_layout = mocker.patch("randovania.interface_common.echoes.generate_description", autospec=True)
    mock_constant_percentage_callback = mocker.patch(
        "randovania.interface_common.simplified_patcher.ConstantPercentageCallback",
        autospec=False,  # TODO: pytest-qt bug
    )

    # Run
    simplified_patcher.generate_layout(options, permalink, progress_update)

    # Assert
    mock_constant_percentage_callback.assert_called_once_with(progress_update, -1)
    mock_generate_layout.assert_called_once_with(
        permalink=permalink,
        status_update=mock_constant_percentage_callback.return_value,
        validate_after_generation=options.advanced_validate_seed_after,
        timeout_during_generation=options.advanced_timeout_during_generation,
        attempts=None,
    )
