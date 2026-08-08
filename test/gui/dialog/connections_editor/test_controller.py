from __future__ import annotations

from typing import cast

import pytest
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QComboBox, QStackedWidget, QTreeView, QWidget

from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.gui.dialog.connections_editor import requirement_tree
from randovania.gui.dialog.connections_editor.controller import RequirementController
from randovania.gui.dialog.connections_editor.model import ROLE, RequirementModel
from randovania.gui.dialog.connections_editor.path import RequirementTreePath
from randovania.gui.dialog.connections_editor.view import RequirementView


@pytest.fixture
def basic_requirement(make_and, make_or, echoes_item):
    """Requirement with just enough structure to test controller behavior"""
    return make_and(
        [echoes_item("Power"), make_or([echoes_item("Dark"), echoes_item("Light")]), echoes_item("Annihilator")]
    )


@pytest.fixture
def single_requirement(echoes_item):
    """Requirement with a leaf as the root"""
    return echoes_item("Power")


ROOT = RequirementTreePath(())
POWER = RequirementTreePath((0,))
OR = RequirementTreePath((1,))
DARK = RequirementTreePath((1, 0))
LIGHT = RequirementTreePath((1, 1))
ANNIHILATOR = RequirementTreePath((2,))


@pytest.fixture
def controller(skip_qtbot, echoes_game_description, basic_requirement):
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

    controller._model.build_tree(basic_requirement)
    return controller


@pytest.fixture
def select(controller):
    def _select(path: RequirementTreePath) -> None:
        index = controller._model.index_from_path(path)
        controller._on_item_selected(index)

    return _select


def test_on_add_requirement_pressed_adds_as_sibling(controller, select, echoes_game_description):
    select(POWER)
    controller._on_add_requirement_pressed()
    result = controller._model.build_requirement()
    expected_item_requirement = requirement_tree.default_from_type(
        ResourceType.ITEM, echoes_game_description.resource_database, echoes_game_description.region_list
    )
    assert requirement_tree._at_path(result, POWER.next_sibling()) == expected_item_requirement


def test_on_add_requirement_pressed_adds_as_last_child(controller, select, echoes_game_description):
    select(OR)
    controller._on_add_requirement_pressed()
    result = controller._model.build_requirement()
    expected_or_requirement = requirement_tree.default_from_type(
        RequirementOr, echoes_game_description.resource_database, echoes_game_description.region_list
    )
    assert requirement_tree._at_path(result, LIGHT.next_sibling()) == expected_or_requirement


def test_on_add_requirement_pressed_rejects_add(controller, select, single_requirement):
    controller._model.build_tree(single_requirement)
    select(ROOT)
    controller._on_add_requirement_pressed()
    assert controller._model.build_requirement() == single_requirement


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


def test_on_delete_requirement_pressed_rejects_delete(controller, select, single_requirement):
    controller._model.build_tree(single_requirement)
    select(ROOT)
    controller._on_delete_requirement_pressed()
    assert controller._model.build_requirement() == single_requirement


def test_on_shift_up_pressed_shifts_as_sibling(controller, select):
    select(LIGHT)
    selected_requirement = controller._model.index_from_path(LIGHT).data(ROLE)
    controller._on_shift_up_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, LIGHT.previous_sibling()) == selected_requirement


def test_on_shift_up_pressed_escapes_to_parent(controller, select):
    select(DARK)
    selected_requirement = controller._model.index_from_path(DARK).data(ROLE)
    controller._on_shift_up_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, POWER.next_sibling()) == selected_requirement


def test_on_shift_up_pressed_ascends_into_sibling(controller, select):
    select(ANNIHILATOR)
    selected_requirement = controller._model.index_from_path(ANNIHILATOR).data(ROLE)
    controller._on_shift_up_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, LIGHT.next_sibling()) == selected_requirement


def test_on_shift_up_pressed_rejects_shift(controller, select, basic_requirement):
    select(ROOT)
    controller._on_shift_up_pressed()
    assert controller._model.build_requirement() == basic_requirement


def test_on_shift_down_pressed_shifts_as_sibling(controller, select):
    select(DARK)
    selected_requirement = controller._model.index_from_path(DARK).data(ROLE)
    controller._on_shift_down_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, DARK.next_sibling()) == selected_requirement


def test_on_shift_down_pressed_escapes_to_parent(controller, select):
    select(LIGHT)
    selected_requirement = controller._model.index_from_path(LIGHT).data(ROLE)
    controller._on_shift_down_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, OR.next_sibling()) == selected_requirement


def test_on_shift_down_pressed_descends_into_sibling(controller, select):
    select(POWER)
    selected_requirement = controller._model.index_from_path(POWER).data(ROLE)
    controller._on_shift_down_pressed()
    result = controller._model.build_requirement()
    assert requirement_tree._at_path(result, OR.previous_sibling().extend_with(0)) == selected_requirement


def test_on_shift_down_pressed_rejects_shift(controller, select, basic_requirement):
    select(ROOT)
    controller._on_shift_down_pressed()
    assert controller._model.build_requirement() == basic_requirement


@pytest.mark.parametrize(
    "to_type",
    [
        RequirementArrayBase,
        ResourceType.ITEM,
        ResourceType.EVENT,
        ResourceType.TRICK,
        ResourceType.DAMAGE,
        ResourceType.VERSION,
        ResourceType.MISC,
        RequirementTemplate,
        NodeRequirement,
    ],
)
def test_on_type_combo_changed_changes_requirement_to_type(controller, select, to_type):
    select(ROOT)
    type_index = controller._combo_type.findData(to_type, ROLE)
    controller._combo_type.setCurrentIndex(type_index)

    controller._on_type_combo_changed()
    result = controller._model.build_requirement()

    if isinstance(to_type, ResourceType):
        assert isinstance(result, ResourceRequirement)
        assert result.resource.resource_type == to_type
    else:
        assert isinstance(result, to_type)
