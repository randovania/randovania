import json
import pickle
from pathlib import Path

import pytest

from randovania.layout.layout_description import LayoutDescription, CURRENT_DESCRIPTION_SCHEMA_VERSION
from randovania.layout.base.trick_level import LayoutTrickLevel


@pytest.mark.parametrize("value", LayoutTrickLevel)
def test_pickle_trick_level(value: LayoutTrickLevel):
    assert pickle.loads(pickle.dumps(value)) == value


def test_load_multiworld(test_files_dir):
    file_path = Path(test_files_dir).joinpath("log_files", "multiworld.rdvgame")

    with file_path.open("r") as open_file:
        input_data = json.load(open_file)

    # Run
    result = LayoutDescription.from_json_dict(input_data)
    input_data["schema_version"] = CURRENT_DESCRIPTION_SCHEMA_VERSION

    # Assert
    as_json = result.as_json
    del input_data["info"]
    del as_json["info"]

    assert as_json == input_data
