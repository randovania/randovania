from __future__ import annotations

from PySide6 import QtCore

from randovania.gui.dialog.connector_prompt_dialog import ConnectorPromptDialog


async def test_connector_prompt_dialog(skip_qtbot, mocker):
    connector_prompt = ConnectorPromptDialog(
        parent=None,
        title="Dialog test",
        description="Description for dialog test",
        is_modal=False,
        initial_value=None,
        max_length=None,
        is_password=False,
        check_re=None,
    )
    skip_qtbot.addWidget(connector_prompt)

    assert connector_prompt.windowTitle() == "Dialog test"

    # test ip radio
    skip_qtbot.mouseClick(connector_prompt.ip_radio, QtCore.Qt.MouseButton.LeftButton)
    connector_prompt.prompt_edit.setText("192.168.69.69")
    assert connector_prompt.text_value == "192.168.69.69"

    # test localhost radio
    skip_qtbot.mouseClick(
        connector_prompt.top_radio,
        QtCore.Qt.MouseButton.LeftButton,
        pos=QtCore.QPoint(2, connector_prompt.top_radio.height() // 2),
    )
    assert connector_prompt.text_value == "localhost"
