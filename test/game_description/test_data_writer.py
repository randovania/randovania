from __future__ import annotations

import pytest

from randovania.game_description import data_reader, data_writer
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.resources.resource_database import NamedRequirementTemplate
from randovania.games import default_data
from randovania.games.game import RandovaniaGame


@pytest.mark.parametrize("game_enum", RandovaniaGame)
def test_round_trip_full(game_enum: RandovaniaGame):
    original_data = default_data.read_json_then_binary(game_enum)[1]

    game = data_reader.decode_data(original_data)
    encoded_data = data_writer.write_game_description(game)

    assert list(encoded_data.keys()) == list(original_data.keys())
    assert encoded_data == original_data


@pytest.mark.parametrize("small_name", ["prime_data_as_json.json", "prime2_small.json"])
def test_round_trip_small(test_files_dir, small_name):
    # Setup
    original_data = test_files_dir.read_json(small_name)

    game = data_reader.decode_data(original_data)
    encoded_data = data_writer.write_game_description(game)

    # # Uncomment the following to update the file
    # from randovania.lib import json_lib
    # json_lib.write_path(test_files_dir.joinpath(small_name), encoded_data); assert False

    assert encoded_data == original_data


def test_fail_write_used_trick_levels(test_files_dir):
    original_data = test_files_dir.read_json("prime2_small.json")
    game = data_reader.decode_data(original_data)
    game.resource_database.requirement_template["Use Screw Attack (Space Jump)"] = NamedRequirementTemplate(
        "Use Screw Attack (Space Jump)",
        RequirementTemplate("Use Screw Attack (Space Jump)"),
    )

    assert data_writer.write_used_trick_levels(game) is None
