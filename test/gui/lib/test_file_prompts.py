from unittest.mock import AsyncMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.lib import file_prompts


@pytest.mark.parametrize("found", [False, True])
async def test_prompt_preset(skip_qtbot, mocker, found, tmp_path):
    tmp_file = tmp_path.joinpath("foo.rdvpreset")
    tmp_file.write_text("foo")

    def side_effect(file_dialog: QtWidgets.QFileDialog):
        if found:
            file_dialog.selectedFiles = lambda: [tmp_file.as_posix()]
            return QtWidgets.QDialog.Accepted
        else:
            return QtWidgets.QDialog.Rejected

    mock_execute_dialog: AsyncMock = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog",
        side_effect=side_effect,
    )

    parent = QtWidgets.QWidget()
    skip_qtbot.addWidget(parent)

    # Run
    result = await file_prompts.prompt_preset(parent, False)

    # Assert
    mock_execute_dialog.assert_awaited_once()
    if found:
        assert result == tmp_file
    else:
        assert result is None
