from __future__ import annotations

import itertools
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock, call, patch

import pytest

from randovania.cli import database
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.games.game import RandovaniaGame

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area


@pytest.mark.parametrize("expected_resource", [0, 1, 2])
@patch("randovania.cli.database._list_paths_with_resource", autospec=True)
@patch("randovania.cli.database.load_game_description", autospec=True)
def test_list_paths_with_resource_logic(mock_load_game_description: MagicMock,
                                        mock_list_paths_with_resource: MagicMock,
                                        expected_resource: int
                                        ):
    # Setup
    args = MagicMock()
    game = mock_load_game_description.return_value

    resource_a = SimpleResourceInfo(0, "Long Name A", "A", ResourceType.ITEM)
    resource_b = SimpleResourceInfo(1, "Long Name B", "B", ResourceType.ITEM)
    resource_c = SimpleResourceInfo(2, "Long Name C", "C", ResourceType.ITEM)
    resources = [resource_a, resource_b, resource_c]

    game.resource_database = [
        [resource_a],
        [resource_b],
        [resource_c],
    ]

    resource = resources[expected_resource]
    args.resource = resource.long_name

    # Run
    database.list_paths_with_resource_logic(args)

    # Assert
    mock_load_game_description.assert_called_once_with(args)
    mock_list_paths_with_resource.assert_called_once_with(
        game,
        args.print_only_area,
        resource,
        None
    )


def test_write_game_descriptions(mocker):
    from randovania.game_description import data_writer, pretty_print
    mock_write_human_readable_game: MagicMock = mocker.patch.object(pretty_print, "write_human_readable_game")
    mock_write_game_description: MagicMock = mocker.patch.object(data_writer, "write_game_description")
    mock_write_as_split_files: MagicMock = mocker.patch.object(data_writer, "write_as_split_files")

    gds = {
        g: MagicMock()
        for g in [RandovaniaGame.BLANK, RandovaniaGame.METROID_PRIME_ECHOES]
    }

    # Run
    database.write_game_descriptions(gds)

    # Assert
    mock_write_game_description.assert_has_calls([call(g) for g in gds.values()])
    mock_write_human_readable_game.assert_has_calls([
        call(gd, g.data_path.joinpath("json_data")) for g, gd in gds.items()
    ])
    mock_write_as_split_files.assert_has_calls([
        call(mock_write_game_description.return_value, g.data_path.joinpath("json_data")) for g in gds.keys()
    ])


@pytest.mark.parametrize("check", [False, True])
def test_refresh_game_description_logic(check, mocker):
    # Setup
    args = MagicMock()
    args.integrity_check = check

    from randovania.game_description import default_database, integrity_check

    mock_find_database_errors = mocker.patch.object(integrity_check, "find_database_errors",
                                                    return_value=["An error"])

    mock_game_description_for: MagicMock = mocker.patch.object(default_database, "game_description_for")
    mock_write_game_descriptions: MagicMock = mocker.patch.object(database, "write_game_descriptions")

    # Run
    database.refresh_game_description_logic(args)

    # Assert
    if check:
        mock_find_database_errors.assert_has_calls([
            call(mock_game_description_for.return_value) for _ in RandovaniaGame
        ])
        mock_write_game_descriptions.assert_not_called()
    else:
        mock_find_database_errors.assert_not_called()
        mock_write_game_descriptions.assert_called_once_with({
            g: mock_game_description_for.return_value for g in RandovaniaGame
        })


def test_refresh_pickup_database_logic(mocker):
    # Setup
    args = MagicMock()

    from randovania.game_description import default_database

    mock_write_pickup_database_for_game = mocker.patch.object(default_database, "write_pickup_database_for_game")

    # Run
    database.refresh_pickup_database_logic(args)

    # Assert
    mock_write_pickup_database_for_game.assert_has_calls([call(ANY, ANY) for _ in RandovaniaGame])


@pytest.mark.parametrize("single_image", [False, True])
@pytest.mark.parametrize("include_pickups", [False, True])
def test_render_region_graph_logic(mocker, single_image, include_pickups, blank_game_description):
    gd = blank_game_description
    args = MagicMock()
    args.single_image = single_image
    args.json_database = None
    args.game = gd.game.value
    args.include_pickups = include_pickups
    args.include_teleporters = True

    import graphviz
    mock_digraph: MagicMock = mocker.patch.object(graphviz, "Digraph")

    # Run
    database.render_region_graph_logic(args)

    # Assert
    if single_image:
        mock_digraph.assert_called_once_with(
            name=gd.game.short_name,
            comment=gd.game.long_name
        )
    else:
        mock_digraph.assert_called_once_with(
            name="Intro",
        )

    def calls_for(region, area: Area):
        yield call(
            f"{region.name}-{area.name}", area.name,
            color=ANY,
            fillcolor=ANY,
            style="filled",
            fontcolor="#ffffff",
            shape=ANY,
            penwidth="3.0",
        )
        if include_pickups:
            for node in area.nodes:
                if isinstance(node, PickupNode):
                    yield call(str(node.pickup_index), ANY, shape="house")

    area_node = list(itertools.chain.from_iterable(
        calls_for(region, area)
        for region in gd.region_list.regions
        for area in region.areas
    ))

    dot = mock_digraph.return_value
    dot.node.assert_has_calls(area_node)
    dot.render.assert_called_once_with(format="png", view=True, cleanup=True)
