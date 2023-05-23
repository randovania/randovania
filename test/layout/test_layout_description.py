import contextlib
import copy
import pickle

import pytest

from randovania.layout import description_migration
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.layout_description import LayoutDescription, InvalidLayoutDescription


@pytest.mark.parametrize("value", LayoutTrickLevel)
def test_pickle_trick_level(value: LayoutTrickLevel):
    assert pickle.loads(pickle.dumps(value)) == value


@pytest.fixture()
def multiworld_rdvgame(test_files_dir):
    return test_files_dir.read_json("log_files", "multiworld.rdvgame")


def test_load_multiworld(multiworld_rdvgame):
    input_data = copy.deepcopy(multiworld_rdvgame)

    # Run
    result = LayoutDescription.from_json_dict(input_data)
    input_data["schema_version"] = description_migration.CURRENT_VERSION

    # Assert
    as_json = result.as_json()
    del input_data["info"]
    del as_json["info"]

    assert as_json == input_data


@pytest.mark.parametrize("reason", ["ok", "bad_secret", "bad_info"])
def test_round_trip_no_spoiler(obfuscator_test_secret, multiworld_rdvgame, reason):
    input_data = copy.deepcopy(multiworld_rdvgame)
    input_data = description_migration.convert_to_current_version(input_data)
    input_data["info"]["has_spoiler"] = False
    layout = LayoutDescription.from_json_dict(input_data)

    # Encode
    encoded = layout.as_json()
    assert set(encoded.keys()) & {"game_modifications", "item_order"} == set()

    expectation = pytest.raises(InvalidLayoutDescription)
    if reason == "bad_secret":
        encoded["secret"] = "bad"
    elif reason == "bad_info":
        encoded["info"]["has_spoiler"] = True
    else:
        expectation = contextlib.nullcontext()

    with expectation:
        result = LayoutDescription.from_json_dict(encoded)
        assert result == layout


def test_no_spoiler_encode(obfuscator_no_secret, multiworld_rdvgame):
    input_data = copy.deepcopy(multiworld_rdvgame)
    input_data = description_migration.convert_to_current_version(input_data)
    input_data["info"]["has_spoiler"] = False
    layout = LayoutDescription.from_json_dict(input_data)

    # Encode
    encoded = layout.as_json()

    assert set(encoded.keys()) & {"game_modifications", "item_order", "secret"} == set()
