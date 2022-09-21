from unittest.mock import MagicMock, ANY

import pytest

from randovania.gui.widgets import game_validator_widget
from randovania.resolver import debug


@pytest.fixture(name="widget")
def _widget(skip_qtbot):
    layout = MagicMock()
    widget = game_validator_widget.GameValidatorWidget(layout)
    skip_qtbot.addWidget(widget)
    return widget


@pytest.mark.parametrize("success", [False, True])
async def test_run_validator(mocker, success):
    # Setup
    old_print_function = debug.print_function
    write_to_log = MagicMock()
    layout = MagicMock()
    debug_level = 2

    def side_effect(**kwargs):
        assert debug.debug_level() == debug_level
        assert debug.print_function is write_to_log
        return "YES" if success else None

    mock_resolve = mocker.patch("randovania.resolver.resolver.resolve", side_effect=side_effect)
    mocker.patch("time.perf_counter", side_effect=[1, 2])

    # Run
    with debug.with_level(0):
        result = await game_validator_widget._run_validator(write_to_log, debug_level, layout)

    # Assert
    mock_resolve.assert_awaited_once_with(
        configuration=layout.get_preset(0).configuration,
        patches=layout.all_patches[0],
    )
    assert result == "Took 1.000 seconds. Game is {}.".format("possible" if success else "impossible")
    assert debug.print_function is old_print_function


@pytest.mark.parametrize("has_task", [False, True])
def test_stop_validator(widget, has_task):
    task = MagicMock()

    if has_task:
        widget._current_task = task

    # Run
    widget.stop_validator()

    if has_task:
        task.cancel.assert_called_once_with()


async def test_on_start_button_has_task(widget):
    task = MagicMock()
    widget._current_task = task
    widget.start_button.setText("Weird Text")

    # Run
    await widget.on_start_button()

    # Assert
    task.cancel.assert_called_once_with()
    assert widget.start_button.text() == "Weird Text"


@pytest.mark.parametrize("cancel", [False, True])
async def test_on_start_button_no_task(widget, mocker, cancel):
    verbosity = 1  # defaults to 1 in the UI

    async def side_effect(write_to_log, *args):
        assert widget.start_button.text() == "Stop"
        assert widget.status_label.text() == "Running..."
        write_to_log("Hello World")
        write_to_log("  > We are nesting")
        write_to_log("Back up")
        if cancel:
            widget._current_task.cancel()
        else:
            assert widget._current_task is not None
        return "Final result!"

    mock_run_validator = mocker.patch(
        "randovania.gui.widgets.game_validator_widget._run_validator", side_effect=side_effect,
    )

    # Run
    await widget.on_start_button()

    # Assert
    mock_run_validator.assert_awaited_once_with(
        ANY, verbosity, widget.layout
    )
    assert widget.log_widget.topLevelItemCount() == 2
    assert not widget.log_widget.topLevelItem(0).isExpanded()
    assert widget.log_widget.topLevelItem(0).child(0).text(0) == "We are nesting"
    assert widget.log_widget.topLevelItem(1).isExpanded()
    assert widget.start_button.text() == "Start"
    assert widget.status_label.text() == "Cancelled!" if cancel else "Final result!"
    assert widget._current_task is None

