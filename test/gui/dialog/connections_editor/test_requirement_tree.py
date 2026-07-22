from __future__ import annotations

import pytest

from randovania.gui.dialog.connections_editor import requirement_tree
from randovania.gui.dialog.connections_editor.path import Path

TUPLE = (0, 2, 1)


@pytest.mark.parametrize(
    ("items", "idx", "value", "expected"),
    [(TUPLE, 0, 3, (3, *TUPLE)), (TUPLE, 1, 3, (0, 3, 2, 1)), (TUPLE, 2, 3, (0, 2, 3, 1)), (TUPLE, 3, 3, (*TUPLE, 3))],
)
def test_tuple_insert_inserts(items, idx, value, expected):
    assert requirement_tree.tuple_insert(items, idx, value) == expected


@pytest.mark.parametrize(
    ("items", "idx", "value", "expected"),
    [(TUPLE, 0, 3, (3, 2, 1)), (TUPLE, 1, 3, (0, 3, 1)), (TUPLE, 2, 3, (0, 2, 3))],
)
def test_tuple_replace_replaces(items, idx, value, expected):
    assert requirement_tree.tuple_replace(items, idx, value) == expected


@pytest.mark.parametrize(("items", "idx", "expected"), [(TUPLE, 0, (2, 1)), (TUPLE, 1, (0, 1)), (TUPLE, 2, (0, 2))])
def test_tuple_remove_removes(items, idx, expected):
    assert requirement_tree.tuple_remove(items, idx) == expected


@pytest.mark.parametrize(("path"), [Path((1, 1)), Path((4, 1, 2)), Path((0,))])
def test_insert_at_path_inserts(echoes_varied_requirement, echoes_simple_resource, path):
    inserted_item = echoes_simple_resource("MorphBall")
    after_insert = requirement_tree.insert_at_path(echoes_varied_requirement, path, inserted_item)
    assert requirement_tree._at_path(after_insert, path) == inserted_item


@pytest.mark.parametrize(("path"), [Path((1, 0)), Path((4, 1, 2)), Path((0,))])
def test_remove_at_path_removes(echoes_varied_requirement, path):
    item_to_be_removed = requirement_tree._at_path(echoes_varied_requirement, path)
    after_remove = requirement_tree.remove_at_path(echoes_varied_requirement, path)
    assert requirement_tree._at_path(after_remove, path) != item_to_be_removed


@pytest.mark.parametrize(("path"), [Path((1, 1)), Path((4, 1, 2)), Path((0,))])
def test_replace_at_path_replaces(echoes_varied_requirement, echoes_simple_resource, path):
    item_to_replace_with = echoes_simple_resource("MorphBall")
    after_replace = requirement_tree.replace_at_path(echoes_varied_requirement, path, item_to_replace_with)
    assert requirement_tree._at_path(after_replace, path) == item_to_replace_with
