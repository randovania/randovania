from __future__ import annotations

from unittest.mock import ANY, MagicMock, call

import pytest
from PySide6.QtCore import QPoint

from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.gui.lib.data_editor_canvas import DataEditorCanvas


@pytest.fixture()
def canvas(skip_qtbot, dread_game_description):
    canvas = DataEditorCanvas()
    skip_qtbot.addWidget(canvas)

    region = dread_game_description.region_list.region_with_name("Artaria")
    area = region.area_by_name("First Tutorial")

    canvas.select_region(region)
    canvas.select_area(area)

    canvas.highlight_node(area.nodes[0])

    return canvas


def test_paintEvent(skip_qtbot, canvas, mocker):
    event = MagicMock()
    mock_painter: MagicMock = mocker.patch("PySide6.QtGui.QPainter")

    # Run
    canvas.paintEvent(event)

    # Assert
    mock_painter.assert_called_once_with(canvas)
    draw_ellipse: MagicMock = mock_painter.return_value.drawEllipse
    draw_ellipse.assert_any_call(ANY, 5, 5)
    draw_ellipse.assert_any_call(ANY, 7, 7)
    mock_painter.return_value.drawText.assert_called()


def test_mouseDoubleClickEvent_node(skip_qtbot, canvas):
    event = MagicMock()
    event.globalPos.return_value = QPoint(532, 319)
    canvas._update_scale_variables()

    expected_node = canvas.area.node_with_name("Door to Charge Tutorial")

    select_node = MagicMock()
    select_area = MagicMock()

    canvas.SelectNodeRequest.connect(select_node)
    canvas.SelectAreaRequest.connect(select_area)

    # Run
    canvas.mouseDoubleClickEvent(event)

    # Assert
    select_node.assert_called_once_with(expected_node)
    select_area.assert_not_called()


def test_contextMenuEvent(skip_qtbot, canvas, mocker):
    mock_qmenu: MagicMock = mocker.patch("PySide6.QtWidgets.QMenu")

    event = MagicMock()
    event.globalPos.return_value = QPoint(100, 200)
    canvas._update_scale_variables()

    # Run
    canvas.contextMenuEvent(event)

    # Assert
    mock_qmenu.assert_any_call(canvas)
    mock_qmenu.assert_any_call("Area: First Tutorial Access", canvas)
    event.globalPos.assert_has_calls([call(), call()])
    mock_qmenu.return_value.exec_.assert_called_once_with(QPoint(100, 200))


def test_area_maps(skip_qtbot, canvas: DataEditorCanvas, mocker):
    canvas.select_game(RandovaniaGame.CAVE_STORY)

    for region in default_database.game_description_for(RandovaniaGame.CAVE_STORY).region_list.regions:
        canvas.select_region(region)
        for area in region.areas:
            canvas.select_area(area)
            break
        break

    assert canvas._background_image is not None
