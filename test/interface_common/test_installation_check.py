import platform
from unittest.mock import MagicMock

import pytest

import randovania
from randovania.interface_common import installation_check
from randovania.lib import json_lib


@pytest.mark.skipif(
    not (platform.system() == "Windows" and randovania.is_frozen()), reason="only works in frozen Windows"
)
def test_find_bad_installation():
    progress_update = MagicMock()
    hash_list: dict[str, str] = json_lib.read_path(randovania.get_data_path().joinpath("frozen_file_list.json"))

    result = installation_check.find_bad_installation(hash_list, progress_update)

    assert result == ([], [], set())
