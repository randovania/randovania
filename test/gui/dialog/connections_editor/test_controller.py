from __future__ import annotations

from typing import cast

import pytest
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QComboBox, QStackedWidget, QTreeView, QWidget

from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.dialog.connections_editor import requirement_tree
from randovania.gui.dialog.connections_editor.controller import RequirementController
from randovania.gui.dialog.connections_editor.model import ROLE, RequirementModel
from randovania.gui.dialog.connections_editor.path import Path
from randovania.gui.dialog.connections_editor.view import RequirementView


@pytest.fixture
def controller(skip_qtbot, echoes_game_description, echoes_simple_resource):
    parent = QWidget()
    tree = QTreeView()
    stacked_widget = QStackedWidget()
    combo_type = QComboBox()
    undo_stack = QUndoStack()

    skip_qtbot.addWidget(parent)
    skip_qtbot.addWidget(tree)
    skip_qtbot.addWidget(stacked_widget)
    skip_qtbot.addWidget(combo_type)

    model = RequirementModel()
    view = RequirementView(parent, tree, model)
    controller = RequirementController(
        parent,
        stacked_widget,
        combo_type,
        echoes_game_description.resource_database,
        echoes_game_description.region_list,
        model,
        view,
        undo_stack,
    )

    basic_requirement = RequirementAnd(
        [
            echoes_simple_resource("Power"),
            RequirementOr([echoes_simple_resource("Dark"), echoes_simple_resource("Light")]),
            echoes_simple_resource("Annihilator"),
        ]
    )

    controller._model.build_tree(basic_requirement)
    return controller


ROOT = Path(())
POWER = Path((0,))
OR = Path((1,))
DARK = Path((1, 0))
LIGHT = Path((1, 1))
ANNIHILATOR = Path((2,))


@pytest.fixture
def select(controller):
    def _select(path: Path) -> None:
        index = controller._model.index_from_path(path)
        controller._on_item_selected(index)

    return _select


@pytest.fixture
def expected_item_requirement(echoes_game_description):
    return requirement_tree.default_from_type(
        ResourceType.ITEM, echoes_game_description.resource_database, echoes_game_description.region_list
    )


@pytest.fixture
def expected_or_requirement(echoes_game_description):
    return requirement_tree.default_from_type(
        RequirementOr, echoes_game_description.resource_database, echoes_game_description.region_list
    )


def test_on_add_requirement_pressed_adds_as_sibling(controller, select, expected_item_requirement):
    select(POWER)
    controller._on_add_requirement_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, POWER.next_sibling()) == expected_item_requirement


def test_on_add_requirement_pressed_adds_as_last_child(controller, select, expected_or_requirement):
    select(OR)
    controller._on_add_requirement_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, LIGHT.next_sibling()) == expected_or_requirement


def test_on_delete_requirement_pressed_deletes(controller, select):
    select(POWER)
    controller._on_delete_requirement_pressed()
    result = cast(RequirementAnd, controller._model.build_requirement())
    assert len(result.items) == 2


def test_on_delete_requirement_pressed_selects_parent(controller, select):
    select(LIGHT)
    controller._on_delete_requirement_pressed()
    select(DARK)
    controller._on_delete_requirement_pressed()
    assert controller._view._tree.selectionModel().currentIndex().data(ROLE) == controller._model.index_from_path(
        OR
    ).data(ROLE)


def test_on_delete_requirement_pressed_selects_previous_sibling(controller, select):
    select(ANNIHILATOR)
    controller._on_delete_requirement_pressed()
    assert controller._view._tree.selectionModel().currentIndex().data(ROLE) == controller._model.index_from_path(
        OR
    ).data(ROLE)


def test_on_shift_up_pressed_shifts_as_sibling(controller, select):
    select(LIGHT)
    selected_requirement = controller._model.index_from_path(LIGHT).data(ROLE)
    controller._on_shift_up_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, DARK) == selected_requirement


def test_on_shift_up_pressed_escapes_to_parent(controller, select):
    select(DARK)
    selected_requirement = controller._model.index_from_path(DARK).data(ROLE)
    controller._on_shift_up_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, OR) == selected_requirement


def test_on_shift_up_pressed_ascends_into_sibling(controller, select):
    select(ANNIHILATOR)
    selected_requirement = controller._model.index_from_path(ANNIHILATOR).data(ROLE)
    controller._on_shift_up_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, LIGHT.next_sibling()) == selected_requirement


def test_on_shift_down_pressed_shifts_as_sibling(controller, select):
    select(DARK)
    selected_requirement = controller._model.index_from_path(DARK).data(ROLE)
    controller._on_shift_down_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, LIGHT) == selected_requirement


def test_on_shift_down_pressed_escapes_to_parent(controller, select):
    select(LIGHT)
    selected_requirement = controller._model.index_from_path(LIGHT).data(ROLE)
    controller._on_shift_down_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, ANNIHILATOR) == selected_requirement


def test_on_shift_down_pressed_descends_into_sibling(controller, select):
    select(POWER)
    selected_requirement = controller._model.index_from_path(POWER).data(ROLE)
    controller._on_shift_down_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, POWER.extend_with(0)) == selected_requirement
