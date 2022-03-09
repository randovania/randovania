import json
import os
from unittest.mock import MagicMock, ANY

from randovania.games.prime1.exporter.game_exporter import PrimeGameExporter, PrimeGameExportParams


def test_patch_game(mocker, tmp_path):
    mock_symbols_for_file: MagicMock = mocker.patch("py_randomprime.symbols_for_file", return_value={
        "UpdateHintState__13CStateManagerFf": 0x80044D38,
    })
    mock_patch_iso_raw: MagicMock = mocker.patch("py_randomprime.patch_iso_raw")
    patch_data = {"patch": "data", 'gameConfig': {}, 'hasSpoiler': True, "preferences": {}}
    progress_update = MagicMock()

    exporter = PrimeGameExporter()

    # Run
    exporter.export_game(
        patch_data,
        PrimeGameExportParams(
            None,
            tmp_path.joinpath("input.iso"), tmp_path.joinpath("output.iso"),
            cache_path=tmp_path.joinpath("cache_path"),
        ),
        progress_update
    )

    # Assert
    expected = {
        "patch": "data",
        'gameConfig': {
            "updateHintStateReplacement": [
                148, 33, 255, 204, 124, 8, 2, 166, 144, 1, 0, 56, 191, 193, 0, 44, 124, 127, 27, 120, 136, 159, 0, 2,
                44, 4, 0, 0, 64, 130, 0, 24, 187, 193, 0, 44, 128, 1, 0, 56, 124, 8, 3, 166, 56, 33, 0, 52, 78,
                128, 0, 32, 56, 192, 0, 0, 152, 223, 0, 2, 63, 192, 128, 4, 99, 222, 77, 148, 56, 128, 1, 0, 124, 4,
                247, 172, 44, 4, 0, 0, 56, 132, 255, 224, 64, 130, 255, 244, 124, 0, 4, 172, 76, 0, 1, 44, 187,
                193, 0, 44, 128, 1, 0, 56, 124, 8, 3, 166, 56, 33, 0, 52, 78, 128, 0, 32
            ]
        },
        "preferences": {
            "cacheDir": os.fspath(tmp_path.joinpath("cache_path")),
        },
        "inputIso": os.fspath(tmp_path.joinpath("input.iso")),
        "outputIso": os.fspath(tmp_path.joinpath("output.iso")),
    }
    mock_symbols_for_file.assert_called_once_with(tmp_path.joinpath("input.iso"))
    mock_patch_iso_raw.assert_called_once_with(json.dumps(expected, indent=4, separators=(',', ': ')), ANY)
