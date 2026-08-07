from __future__ import annotations

import pytest

from randovania.gui.dialog.connections_editor.model import ROLE, RequirementModel
from randovania.gui.dialog.connections_editor.path import RequirementTreePath


@pytest.fixture
def model(echoes_varied_requirement) -> RequirementModel:
    requirement_model = RequirementModel()
    requirement_model.build_tree(echoes_varied_requirement)
    return requirement_model


def test_build_no_changes(model, echoes_varied_requirement):
    assert model.build_requirement() == echoes_varied_requirement


def test_path_from_index_discards_root(model):
    TEMPLATE = RequirementTreePath((6,))

    root_index = model.invisibleRootItem().index()
    and_index = model.index(0, 0, root_index)
    template_index = model.index(6, 0, and_index)

    assert model.path_from_index(template_index) == TEMPLATE


def test_index_from_path_adds_root(model, echoes_item):
    DARK = RequirementTreePath((0, 1))
    assert model.index_from_path(DARK).data(ROLE) == echoes_item("Dark")


OR = RequirementTreePath((0,))
ANNIHILATOR = RequirementTreePath((0, 3))
MISC = RequirementTreePath((5,))


@pytest.mark.parametrize(
    ("path", "expected"),
    [(OR, 7), (ANNIHILATOR, 3), (MISC, 7)],
)
def test_sibling_count_is_last_index(model, path, expected):
    assert model.sibling_count(path) == expected
