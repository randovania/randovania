import io
import json
from unittest.mock import MagicMock, patch

import pytest

import randovania
from randovania.game_description import data_reader, data_writer
from randovania.game_description.requirements import RequirementAnd, ResourceRequirement, RequirementTemplate
from randovania.games.prime import default_data


def test_round_trip_full():
    original_data = default_data.decode_default_prime2()

    game = data_reader.decode_data(original_data)
    encoded_data = data_writer.write_game_description(game)

    assert original_data == encoded_data


def test_round_trip_small(test_files_dir):
    # Setup
    with test_files_dir.joinpath("prime_data_as_json.json").open("r") as data_file:
        original_data = json.load(data_file)

    game = data_reader.decode_data(original_data)
    encoded_data = data_writer.write_game_description(game)

    assert original_data == encoded_data


@pytest.mark.skipif(randovania.is_frozen(), reason="frozen executable doesn't have JSON files")
def test_commited_human_readable_description(echoes_game_description):
    buffer = io.StringIO()
    data_writer.write_human_readable_world_list(echoes_game_description, buffer)

    assert default_data.prime2_human_readable_path().read_text("utf-8") == buffer.getvalue()


@patch("randovania.game_description.data_writer.pretty_print_requirement")
def test_pretty_print_requirement_array_one_item(mock_print_requirement: MagicMock):
    mock_print_requirement.return_value = ["a", "b"]

    req = MagicMock()
    array = RequirementAnd([req])

    # Run
    result = list(data_writer.pretty_print_requirement_array(array, 3))

    # Assert
    assert result == ["a", "b"]
    mock_print_requirement.assert_called_once_with(req, 3)


@patch("randovania.game_description.data_writer.pretty_print_requirement")
def test_pretty_print_requirement_array_combinable(mock_print_requirement: MagicMock, echoes_resource_database):
    mock_print_requirement.return_value = ["a", "b"]

    array = RequirementAnd([
        ResourceRequirement(echoes_resource_database.item[0], 1, False),
        RequirementTemplate(echoes_resource_database, "Shoot Sunburst"),
    ])

    # Run
    result = list(data_writer.pretty_print_requirement_array(array, 3))

    # Assert
    assert result == [(3, "Power Beam and Shoot Sunburst")]
    mock_print_requirement.assert_not_called()
