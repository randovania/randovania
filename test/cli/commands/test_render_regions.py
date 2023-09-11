import itertools
from unittest.mock import ANY, MagicMock, call

import pytest

import randovania
from randovania.cli.commands import render_regions
from randovania.game_description.db.area import Area
from randovania.game_description.db.pickup_node import PickupNode


@pytest.mark.skipif(randovania.is_frozen(), reason="graphviz not included in executable")
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
    render_regions.render_region_graph_logic(args)

    # Assert
    if single_image:
        mock_digraph.assert_called_once_with(name=gd.game.short_name, comment=gd.game.long_name)
    else:
        mock_digraph.assert_called_once_with(
            name="Intro",
        )

    def calls_for(region, area: Area):
        yield call(
            f"{region.name}-{area.name}",
            area.name,
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

    area_node = list(
        itertools.chain.from_iterable(
            calls_for(region, area) for region in gd.region_list.regions for area in region.areas
        )
    )

    dot = mock_digraph.return_value
    dot.node.assert_has_calls(area_node)
    dot.render.assert_called_once_with(format="png", view=True, cleanup=True)
