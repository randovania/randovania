from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node import NodeContext
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.resources.resource_collection import ResourceCollection

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_info import ResourceInfo


@pytest.fixture(params=[False, True])
def hint_node(request, blank_game_description):
    has_translator = request.param
    translator = blank_game_description.resource_database.get_item("BlueKey")

    node = blank_game_description.region_list.node_by_identifier(
        NodeIdentifier.create(
            "Intro",
            "Hint Room",
            "Hint with Translator" if has_translator else "Hint no Translator",
        )
    )
    assert isinstance(node, HintNode)

    return has_translator, translator, node


def test_hint_node_should_collect(hint_node, empty_patches):
    # Setup
    db = empty_patches.game.resource_database
    has_translator, translator, node = hint_node
    node_provider = MagicMock()

    def ctx(*args: ResourceInfo):
        resources = ResourceCollection.from_dict(db, dict.fromkeys(args, 1))
        return NodeContext(empty_patches, resources, db, node_provider)

    assert node.requirement_to_collect.satisfied(ctx(), 0) != has_translator
    assert node.requirement_to_collect.satisfied(ctx(translator), 0)

    assert node.should_collect(ctx())
    assert node.should_collect(ctx(translator))

    resource = node.resource(ctx())
    assert not node.should_collect(ctx(resource))
    assert not node.should_collect(ctx(resource, translator))


def test_hint_node_resource_gain_on_collect(hint_node, empty_patches):
    # Setup
    db = empty_patches.game.resource_database
    node = hint_node[-1]
    context = NodeContext(empty_patches, db.create_resource_collection(), db, MagicMock())

    # Run
    gain = node.resource_gain_on_collect(context)

    # Assert
    assert dict(gain) == {node.resource(context): 1}
