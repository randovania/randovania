from unittest.mock import MagicMock, call, ANY

import pytest
from PySide2.QtCore import QPoint

from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.gui.lib.data_editor_canvas import DataEditorCanvas


@pytest.fixture(name="canvas")
def _canvas(skip_qtbot, dread_game_description):
    canvas = DataEditorCanvas()
    skip_qtbot.addWidget(canvas)

    world = dread_game_description.world_list.world_with_name("Artaria")
    area = world.area_by_name("First Tutorial")

    canvas.select_world(world)
    canvas.select_area(area)

    canvas.highlight_node(area.nodes[0])

    return canvas


def test_paintEvent(skip_qtbot, canvas, mocker):
    event = MagicMock()
    mock_painter: MagicMock = mocker.patch("PySide2.QtGui.QPainter")

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

    canvas.SelectNodeRequest = MagicMock()
    canvas.SelectAreaRequest = MagicMock()

    # Run
    canvas.mouseDoubleClickEvent(event)

    # Assert
    canvas.SelectNodeRequest.emit.assert_called_once_with(expected_node)
    canvas.SelectAreaRequest.emit.assert_not_called()


def test_contextMenuEvent(skip_qtbot, canvas, mocker):
    mock_qmenu: MagicMock = mocker.patch("PySide2.QtWidgets.QMenu")

    event = MagicMock()
    event.globalPos.return_value = QPoint(100, 200)
    canvas._update_scale_variables()

    # Run
    canvas.contextMenuEvent(event)

    # Assert
    mock_qmenu.assert_any_call(canvas)
    mock_qmenu.assert_any_call('Area: First Tutorial Access', canvas)
    event.globalPos.assert_has_calls([call(), call()])
    mock_qmenu.return_value.exec_.assert_called_once_with(QPoint(100, 200))


def test_area_maps(skip_qtbot, canvas: DataEditorCanvas, mocker):
    canvas.select_game(RandovaniaGame.CAVE_STORY)

    for world in default_database.game_description_for(RandovaniaGame.CAVE_STORY).world_list.worlds:
        canvas.select_world(world)
        for area in world.areas:
            canvas.select_area(area)
            break
        break

    assert canvas._background_image is not None
