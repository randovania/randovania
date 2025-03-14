from __future__ import annotations

from unittest.mock import ANY, MagicMock

import pytest

from randovania.gui.widgets import game_validator_widget
from randovania.gui.widgets.game_validator_widget import LABEL_IDS
from randovania.resolver import debug


@pytest.fixture
def widget(skip_qtbot):
    layout = MagicMock()
    layout.world_count = 1
    layout.all_presets = [MagicMock()]
    players = MagicMock()
    players.player_names = {0: "Player"}
    players.player_index = 0
    widget = game_validator_widget.GameValidatorWidget(layout, players)
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
        fully_indent_log=False,
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


def test_set_filter(widget):
    assert not widget._action_filters["Hint"]
    assert not widget.show_hints_check.isChecked()

    widget.show_hints_check.setChecked(True)
    assert widget._action_filters["Hint"]
    assert widget.show_hints_check.isChecked()
    assert widget.needs_refresh_label.text() == ""

    widget._last_run_filters = dict(widget._action_filters)

    widget.show_hints_check.setChecked(False)
    assert not widget._action_filters["Hint"]
    assert not widget.show_hints_check.isChecked()
    assert widget.needs_refresh_label.text() == "Please re-run the resolver to update the data"


@pytest.mark.parametrize("cancel", [False, True])
@pytest.mark.parametrize("verbosity", [0, 1, 2, 3])
async def test_on_start_button_no_task(widget, mocker, cancel: bool, verbosity: int):
    widget._verbosity = verbosity

    async def side_effect(write_to_log, *args):
        assert widget.start_button.text() == "Stop"
        assert widget.status_label.text() == "Running..."
        if verbosity:
            write_to_log("> Intro/Starting Area/Spawn Point for []")
            write_to_log(
                "> Intro/Starting Area/Pickup (Weapon) [100/100 Energy] for "
                "[action Major - World 0's Blue Key] ['N: Pickup (Weapon)', 'I: Blue Key']"
            )
            if verbosity > 1:
                write_to_log(" # Satisfiable Actions")
                write_to_log("  = Intro/Starting Area/Lock - Door to Boss Arena")
            if verbosity > 2:
                write_to_log(": Intro/Back-Only Lock Room/Door to Starting Area")
            write_to_log(
                "> Intro/Starting Area/Spawn Point [100/100 Energy] for [action Some weird action] ['N: Spawn Point']"
            )
            write_to_log(" * Rollback Intro/Starting Area/Spawn Point [action Some weird action]")
            write_to_log(
                "> Intro/Back-Only Lock Room/Event - Key Switch 1 [100/100 Energy] for "
                "[action Event - Key Switch 1] ['E: Key Switch 1']"
            )
        if cancel:
            widget._current_task.cancel()
        else:
            assert widget._current_task is not None
        return "Final result!"

    mock_run_validator = mocker.patch(
        "randovania.gui.widgets.game_validator_widget._run_validator",
        side_effect=side_effect,
    )

    # Run
    await widget.on_start_button()

    # Assert
    mock_run_validator.assert_awaited_once_with(ANY, verbosity, widget.layout_description)
    assert widget.log_widget.topLevelItemCount() == (1 if verbosity else 0)

    if verbosity:
        region_item = widget.log_widget.topLevelItem(0)
        assert region_item.childCount() == 5
        assert region_item.text(LABEL_IDS["Node"]) == "Intro"

        assert not region_item.child(0).isExpanded()

        pickup_action = region_item.child(1)
        assert pickup_action.text(LABEL_IDS["Type"]) == "Major"
        assert pickup_action.text(LABEL_IDS["Action"]) == "Blue Key"

        other_action = region_item.child(2)
        assert other_action.text(LABEL_IDS["Type"]) == "Other"
        assert other_action.text(LABEL_IDS["Action"]) == "Some weird action"

        rollback = region_item.child(3)
        assert rollback.text(LABEL_IDS["Node"]) == "Rollback Starting Area/Spawn Point"
        assert rollback.text(LABEL_IDS["Type"]) == "Rollback"

    if verbosity > 1:
        child = pickup_action.child(0)
        assert child.text(0) == "# Satisfiable Actions"
        assert child.child(0).text(LABEL_IDS["Node"]) == "Intro/Starting Area/Lock - Door to Boss Arena"

    if verbosity > 2:
        child = pickup_action.child(1)
        assert child.text(LABEL_IDS["Node"]) == "Intro/Back-Only Lock Room/Door to Starting Area"

    for column in (LABEL_IDS["Energy"], LABEL_IDS["Resources"]):
        assert widget.log_widget.isColumnHidden(column) == (verbosity < 2)

    assert widget.start_button.text() == "Start"
    assert widget.status_label.text() == "Cancelled!" if cancel else "Final result!"
    assert widget._current_task is None
