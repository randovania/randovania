from unittest.mock import MagicMock

import pytest

from randovania.gui.dialog.permalink_dialog import PermalinkDialog


@pytest.mark.parametrize("valid", [False, True])
def test_on_permalink_changed(skip_qtbot, mocker, valid):
    mock_from_str: MagicMock = mocker.patch("randovania.layout.permalink.Permalink.from_str")
    mock_from_str.return_value.as_base64_str = ""
    if not valid:
        mock_from_str.side_effect = ValueError("Invalid permalink")

    dialog = PermalinkDialog()
    dialog.permalink_edit.setText("")
    skip_qtbot.addWidget(dialog)

    # Run
    dialog._on_permalink_changed("")

    # Assert
    assert dialog.accept_button.isEnabled() == valid


def test_on_permalink_changed_permalink_different_str(skip_qtbot, mocker):
    mock_from_str: MagicMock = mocker.patch("randovania.layout.permalink.Permalink.from_str")
    mock_from_str.return_value.as_base64_str = "!permalink_wrong"

    dialog = PermalinkDialog()
    skip_qtbot.addWidget(dialog)

    # Run
    dialog._on_permalink_changed("")

    # Assert
    assert not dialog.accept_button.isEnabled()
    assert dialog.import_error_label.text() == "Invalid permalink: Imported permalink is different from text field."
