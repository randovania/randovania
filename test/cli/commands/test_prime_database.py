from unittest.mock import MagicMock, patch

import pytest

from randovania.cli import prime_database
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


@pytest.mark.parametrize("expected_resource", [0, 1, 2])
@patch("randovania.cli.prime_database._list_paths_with_resource", autospec=True)
@patch("randovania.cli.prime_database.load_game_description", autospec=True)
def test_list_paths_with_resource_logic(mock_load_game_description: MagicMock,
                                        mock_list_paths_with_resource: MagicMock,
                                        expected_resource: int
                                        ):
    # Setup
    args = MagicMock()
    game = mock_load_game_description.return_value

    resource_a = SimpleResourceInfo(0, "Long Name A", "A", ResourceType.ITEM)
    resource_b = SimpleResourceInfo(0, "Long Name B", "B", ResourceType.ITEM)
    resource_c = SimpleResourceInfo(0, "Long Name C", "C", ResourceType.ITEM)
    resources = [resource_a, resource_b, resource_c]

    game.resource_database = [
        [resource_a],
        [resource_b],
        [resource_c],
    ]

    resource = resources[expected_resource]
    args.resource = resource.long_name

    # Run
    prime_database.list_paths_with_resource_logic(args)

    # Assert
    mock_load_game_description.assert_called_once_with(args)
    mock_list_paths_with_resource.assert_called_once_with(
        game,
        args.print_only_area,
        resource,
        None
    )
