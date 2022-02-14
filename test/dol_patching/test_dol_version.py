from unittest.mock import MagicMock

import pytest

from randovania.dol_patching import dol_version
from randovania.games.game import RandovaniaGame

test_versions = [
    dol_version.DolVersion(
        game=RandovaniaGame.METROID_PRIME_ECHOES,
        description="Gamecube NTSC",
        build_string_address=0x803ac3b0,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32",
        sda2_base=0x804223c0,
        sda13_base=0x8041fd80,
    ),
    dol_version.DolVersion(
        game=RandovaniaGame.METROID_PRIME_ECHOES,
        description="Gamecube PAL",
        build_string_address=0x803ad710,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.035 10/27/2004 19:48:17",
        sda2_base=0x804223c0,
        sda13_base=0x80421060,
    ),
]


@pytest.mark.parametrize("version", test_versions)
def test_read_binary_version(version):
    dol_file = MagicMock()
    dol_file.read.return_value = version.build_string

    # Run
    result = dol_version.find_version_for_dol(dol_file, test_versions)

    # Assert
    dol_file.set_editable.assert_called_once_with(False)
    assert result == version
