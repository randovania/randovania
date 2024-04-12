from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import randovania
from randovania.game_description import default_database, pretty_print
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.games.game import RandovaniaGame


@pytest.mark.skipif(randovania.is_frozen(), reason="frozen executable doesn't have JSON files")
@pytest.mark.parametrize("game", RandovaniaGame)
def test_committed_human_readable_description(game: RandovaniaGame, tmp_path):
    pretty_print.write_human_readable_game(default_database.game_description_for(game), tmp_path)
    new_files = {f.name: f.read_text("utf-8") for f in tmp_path.glob("*.txt")}

    existing_files = {f.name: f.read_text("utf-8") for f in game.data_path.joinpath("logic_database").glob("*.txt")}

    assert new_files == existing_files


@patch("randovania.game_description.pretty_print.pretty_format_requirement")
def test_pretty_print_requirement_array_one_item(mock_print_requirement: MagicMock):
    mock_print_requirement.return_value = ["a", "b"]

    req = MagicMock()
    db = MagicMock()
    array = RequirementAnd([req])

    # Run
    result = list(pretty_print.pretty_print_requirement_array(array, db, 3))

    # Assert
    assert result == ["a", "b"]
    mock_print_requirement.assert_called_once_with(req, db, 3)


@patch("randovania.game_description.pretty_print.pretty_print_requirement")
def test_pretty_print_requirement_array_combinable(mock_print_requirement: MagicMock, echoes_resource_database):
    mock_print_requirement.return_value = ["a", "b"]

    array = RequirementAnd(
        [
            ResourceRequirement.simple(echoes_resource_database.item[0]),
            RequirementTemplate("Shoot Sunburst"),
        ]
    )

    # Run
    result = list(pretty_print.pretty_print_requirement_array(array, echoes_resource_database, 3))

    # Assert
    assert result == [(3, "Power Beam and Shoot Sunburst")]
    mock_print_requirement.assert_not_called()


@pytest.mark.parametrize("has_comment", [False, True])
def test_pretty_print_requirement_array_one_row_and_nested_array(echoes_resource_database, has_comment: bool):
    req = RequirementAnd(
        [
            ResourceRequirement.simple(echoes_resource_database.item[0]),
            RequirementOr(
                [
                    ResourceRequirement.simple(echoes_resource_database.item[1]),
                    RequirementAnd(
                        [
                            ResourceRequirement.simple(echoes_resource_database.item[2]),
                            ResourceRequirement.simple(echoes_resource_database.item[3]),
                        ]
                    ),
                ]
            ),
        ],
        comment="Root comment" if has_comment else None,
    )

    # Run
    result = list(pretty_print.pretty_format_requirement(req, echoes_resource_database))
    lines = "\n".join("      {}{}".format("    " * level, text) for level, text in result)
    lines = f"\n{lines}\n"

    # Assert
    if has_comment:
        assert (
            lines
            == """
      All of the following:
          # Root comment
          Power Beam
          Any of the following:
              Dark Beam
              Annihilator Beam and Light Beam
"""
        )
    else:
        assert (
            lines
            == """
      All of the following:
          Power Beam
          Any of the following:
              Dark Beam
              Annihilator Beam and Light Beam
"""
        )
