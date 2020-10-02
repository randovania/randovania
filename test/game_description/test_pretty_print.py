import io
from unittest.mock import patch, MagicMock

import pytest

import randovania
from randovania.game_description import pretty_print
from randovania.game_description.requirements import RequirementAnd, ResourceRequirement, RequirementTemplate


@pytest.mark.skipif(randovania.is_frozen(), reason="frozen executable doesn't have JSON files")
def test_commited_human_readable_description(echoes_game_description):
    buffer = io.StringIO()
    pretty_print.write_human_readable_world_list(echoes_game_description, buffer)

    assert randovania.get_data_path().joinpath("json_data", "prime2.txt").read_text("utf-8") == buffer.getvalue()


@patch("randovania.game_description.pretty_print.pretty_print_requirement")
def test_pretty_print_requirement_array_one_item(mock_print_requirement: MagicMock):
    mock_print_requirement.return_value = ["a", "b"]

    req = MagicMock()
    array = RequirementAnd([req])

    # Run
    result = list(pretty_print.pretty_print_requirement_array(array, 3))

    # Assert
    assert result == ["a", "b"]
    mock_print_requirement.assert_called_once_with(req, 3)


@patch("randovania.game_description.pretty_print.pretty_print_requirement")
def test_pretty_print_requirement_array_combinable(mock_print_requirement: MagicMock, echoes_resource_database):
    mock_print_requirement.return_value = ["a", "b"]

    array = RequirementAnd([
        ResourceRequirement(echoes_resource_database.item[0], 1, False),
        RequirementTemplate(echoes_resource_database, "Shoot Sunburst"),
    ])

    # Run
    result = list(pretty_print.pretty_print_requirement_array(array, 3))

    # Assert
    assert result == [(3, "Power Beam and Shoot Sunburst")]
    mock_print_requirement.assert_not_called()