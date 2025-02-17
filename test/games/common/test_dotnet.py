from unittest.mock import MagicMock

import pytest

from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.patching.patchers.exceptions import UnableToExportError


def test_dotnet_missing(mocker):
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)

    exporter = GameExporter()

    with pytest.raises(UnableToExportError):
        exporter._do_export_game(
            MagicMock(), GameExportParams(spoiler_output=None, input_path=None, output_path=None), MagicMock()
        )


def test_dotnet_non_zero_error_code(mocker):
    dotnet_process = mocker.patch("subprocess.run")
    dotnet_process.returncode = 1

    exporter = GameExporter()

    with pytest.raises(UnableToExportError):
        exporter._do_export_game(
            MagicMock(), GameExportParams(spoiler_output=None, input_path=None, output_path=None), MagicMock()
        )
