from __future__ import annotations

from unittest.mock import ANY, MagicMock, call

import pytest
from PySide6.QtCore import QPoint, QPointF

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.gui.widgets.data_editor_canvas import CameraData, DataEditorCanvas


@pytest.fixture
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


@pytest.mark.parametrize(
    ("camera_data", "expected"),
    [
        (
            CameraData(
                coords="opengl",
                projection=(
                    (1.7127298, 0.0, 0.0, 0.0),
                    (0.0, 1.9209821, 0.0, 0.0),
                    (0.0, 0.0, -1.0000489, -0.20000489),
                    (0.0, 0.0, -1.0, 0.0),
                ),
                view=(
                    (-0.34270626, -0.93944263, 0, -172.76392),
                    (0.14038785, -0.051213127, 0.98877126, 50.90325),
                    (-0.9288938, 0.33885807, 0.14943738, -235.46387),
                    (0.0, 0.0, 0.0, 1.0),
                ),
            ),
            (-0.12832976063125112, 0.7076416905953024),
        ),
        (
            CameraData(
                coords="opengl",
                projection=(
                    (1.7963935, 0.0, 0.0, 0.0),
                    (0.0, 1.9209821, 0.0, 0.0),
                    (0.0, 0.0, -1.0000489, -0.20000489),
                    (0.0, 0.0, -1.0, 0.0),
                ),
                view=(
                    (-0.23653346, -0.97162336, 0.0, -164.78668),
                    (-0.08732812, 0.021259291, 0.9959528, 46.97933),
                    (-0.96769094, 0.2355761, -0.089878574, -143.77861),
                    (0.0, 0.0, 0.0, 1.0),
                ),
            ),
            (-0.529435883538518, 0.8138382406117051),
        ),
    ],
)
def test_camera_data_game_loc_to_qt_local(
    camera_data: CameraData,
    expected: tuple[float, float],
):
    x, y, z = (0.0, 0.0, 0.0)
    result = camera_data.game_loc_to_qt_local(x, y, z)

    assert result == expected


def test_camera_data_invalid():
    camera_data = CameraData("something_wrong", (), ())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Unknown coordinate system"):
        camera_data.game_loc_to_qt_local(0.0, 0.0, 0.0)


def _world_loc_at(canvas: DataEditorCanvas, widget_point: QPointF):
    return canvas.qt_local_to_game_loc(widget_point - canvas.get_area_canvas_offset())


def test_set_zoom_value_keeps_center(skip_qtbot, canvas: DataEditorCanvas):
    canvas.resize(800, 600)
    canvas._update_scale_variables()
    center = QPointF(400, 300)

    world_before = _world_loc_at(canvas, center)
    canvas.set_zoom_value(30)
    world_after = _world_loc_at(canvas, center)

    assert world_after.x == pytest.approx(world_before.x)
    assert world_after.y == pytest.approx(world_before.y)


def test_wheel_zoom_keeps_mouse_position(skip_qtbot, canvas: DataEditorCanvas):
    canvas.resize(800, 600)
    canvas._update_scale_variables()
    anchor = QPointF(600, 150)

    event = MagicMock()
    event.position.return_value = anchor
    event.angleDelta.return_value.y.return_value = 120

    update_slider = MagicMock()
    canvas.UpdateSlider.connect(update_slider)

    canvas.wheelEvent(event)
    update_slider.assert_called_once_with(True)

    world_before = _world_loc_at(canvas, anchor)
    canvas.set_zoom_value(25)
    world_after = _world_loc_at(canvas, anchor)

    assert world_after.x == pytest.approx(world_before.x)
    assert world_after.y == pytest.approx(world_before.y)

    # the anchor is one-shot: a following slider-only zoom must not reuse it
    assert canvas._wheel_zoom_anchor is None


def test_region_image(skip_qtbot, canvas: DataEditorCanvas, dread_game_description):
    canvas.select_game(RandovaniaGame.METROID_DREAD)

    region = dread_game_description.region_list.region_with_name("Artaria")
    canvas.select_region(region)
    assert canvas._region_image is not None
    assert canvas._background_image is None

    # the image bounds must have the same aspect ratio as the world bounds, or the image is drawn stretched
    image_bounds = canvas._calculated_region_image_bounds
    assert image_bounds is not None
    world_bounds = canvas.region_bounds
    image_ratio = (image_bounds.max_x - image_bounds.min_x) / (image_bounds.max_y - image_bounds.min_y)
    world_ratio = (world_bounds.max_x - world_bounds.min_x) / (world_bounds.max_y - world_bounds.min_y)
    assert image_ratio == pytest.approx(world_ratio, abs=0.005)

    canvas.select_area(region.areas[0])
    assert canvas._background_image is not None
