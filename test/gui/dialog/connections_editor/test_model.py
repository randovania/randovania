from __future__ import annotations

import pytest

from randovania.gui.dialog.connections_editor.model import ROLE, RequirementModel
from randovania.gui.dialog.connections_editor.path import Path


@pytest.fixture
def model() -> RequirementModel:
    return RequirementModel()


def test_build_no_changes(model, echoes_varied_requirement):
    model.build_tree(echoes_varied_requirement)
    assert model.build_requirement() == echoes_varied_requirement


def test_path_from_index_discards_root(model, echoes_varied_requirement):
    model.build_tree(echoes_varied_requirement)

    root_index = model.invisibleRootItem().index()
    or_index = model.index(0, 0, root_index)
    template_index = model.index(2, 0, or_index)

    assert model.path_from_index(template_index) == Path((2,))


def test_index_from_path_adds_root(model, echoes_varied_requirement, echoes_simple_resource):
    model.build_tree(echoes_varied_requirement)
    path = Path((1, 0))
    assert model.index_from_path(path).data(ROLE) == echoes_simple_resource("Dark")


@pytest.mark.parametrize(("path", "expected"), [(Path((1, 1)), 1), (Path((3,)), 4), (Path((4, 1, 0)), 3)])
def test_sibling_count_is_last_index(model, echoes_varied_requirement, path, expected):
    model.build_tree(echoes_varied_requirement)
    assert model.sibling_count(path) == expected
