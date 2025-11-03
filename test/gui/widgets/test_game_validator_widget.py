from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import ANY, MagicMock

import pytest

from randovania.gui.widgets import game_validator_widget
from randovania.gui.widgets.game_validator_widget import LABEL_IDS, ValidatorWidgetResolverLogger
from randovania.resolver import debug
from test.resolver.test_logging import perform_logging

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


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
    logger = MagicMock()
    layout = MagicMock()
    debug_level = debug.LogLevel.HIGH

    def side_effect(**kwargs):
        assert debug.debug_level() == debug_level
        return "YES" if success else None

    mock_resolve = mocker.patch("randovania.resolver.resolver.resolve", side_effect=side_effect)
    mocker.patch("time.perf_counter", side_effect=[1, 2])

    # Run
    with debug.with_level(debug.LogLevel.SILENT):
        result = await game_validator_widget._run_validator(logger, debug_level, layout)

    # Assert
    mock_resolve.assert_awaited_once_with(
        configuration=layout.get_preset(0).configuration,
        patches=layout.all_patches[0],
        logger=logger,
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
@pytest.mark.parametrize(
    "verbosity", [debug.LogLevel.SILENT, debug.LogLevel.NORMAL, debug.LogLevel.HIGH, debug.LogLevel.EXTREME]
)
async def test_on_start_button_no_task(widget, mocker: MockerFixture, blank_game_patches, cancel, verbosity):
    widget._verbosity = verbosity

    async def side_effect(logger: ValidatorWidgetResolverLogger, *args: Any):
        assert widget.start_button.text() == "Stop"
        assert widget.status_label.text() == "Running..."

        perform_logging(blank_game_patches, logger)

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

    for line in widget.tree_as_lines():
        print(line)

    if verbosity >= debug.LogLevel.NORMAL:
        region_item = widget.log_widget.topLevelItem(0)
        assert region_item.childCount() == (9 if verbosity >= debug.LogLevel.HIGH else 7)
        assert region_item.text(LABEL_IDS["Node"]) == "Intro"

        assert not region_item.child(0).isExpanded()

        pickup_action = region_item.child(1)
        assert pickup_action.text(LABEL_IDS["Node"]) == "Starting Area/Pickup (Weapon)"
        assert pickup_action.text(LABEL_IDS["Type"]) == "Major"
        assert pickup_action.text(LABEL_IDS["Action"]) == "Blue Key"
        assert pickup_action.text(LABEL_IDS["Energy"]) == "100/100"
        assert pickup_action.text(LABEL_IDS["Resources"]) == ("Item: Blue Key, Node: Pickup (Weapon)")

        other_action = region_item.child(2)
        assert other_action.text(LABEL_IDS["Type"]) == "Start"
        assert other_action.text(LABEL_IDS["Action"]) == ""

        rollback = region_item.child(3)
        assert rollback.text(LABEL_IDS["Node"]) == "Rollback Starting Area/Spawn Point"
        assert rollback.text(LABEL_IDS["Type"]) == "Rollback"
        assert rollback.text(LABEL_IDS["Action"]) == "Had action? False; Possible action? False"

        event_action = region_item.child(4)
        assert event_action.text(LABEL_IDS["Node"]) == "Back-Only Lock Room/Event - Key Switch 1"
        assert event_action.text(LABEL_IDS["Type"]) == "Event"
        assert event_action.text(LABEL_IDS["Action"]) == "Key Switch 1"
        assert event_action.text(LABEL_IDS["Energy"]) == "100/100"
        assert event_action.text(LABEL_IDS["Resources"]) == ("Event: Key Switch 1")

        success = region_item.child(5)
        assert success.text(LABEL_IDS["Node"]) == "Playthrough Complete"
        assert success.text(LABEL_IDS["Type"]) == "Success"
        assert success.text(LABEL_IDS["Action"]) == "Game is possible"

        failure = region_item.child(6)
        assert failure.text(LABEL_IDS["Node"]) == "Playthrough Complete"
        assert failure.text(LABEL_IDS["Type"]) == "Failure"
        assert failure.text(LABEL_IDS["Action"]) == "Game is impossible"

    if verbosity >= debug.LogLevel.HIGH:
        pickup_satisfy = pickup_action.child(0)
        assert pickup_satisfy.text(0) == "Satisfiable actions"
        assert pickup_satisfy.child(0).text(0) == "• Intro/Starting Area/Lock - Door to Boss Arena"

        other_satisfy = other_action.child(0)
        assert other_satisfy.text(0) == "No satisfiable actions"
        assert other_satisfy.childCount() == 0

        skip1 = region_item.child(7)
        skip2 = region_item.child(8)

        for skip in (skip1, skip2):
            assert skip.text(LABEL_IDS["Node"]) == "Skip Back-Only Lock Room/Event - Key Switch 1"
            assert skip.text(LABEL_IDS["Type"]) == "Skip"
            assert skip.child(0).text(0) == "Additional Requirement Alternatives"
            assert skip.child(0).child(0).text(0) == "• Impossible"

        assert skip1.text(LABEL_IDS["Action"]) == "New additional"
        assert skip1.font(LABEL_IDS["Action"]).bold()

        assert skip2.text(LABEL_IDS["Action"]) == "Same additional"
        assert not skip2.font(LABEL_IDS["Action"]).bold()

    if verbosity >= debug.LogLevel.EXTREME:
        pickup_path = pickup_action.child(1)
        assert pickup_path.text(LABEL_IDS["Node"]) == "↪ Intro/Back-Only Lock Room/Door to Starting Area"

    for column in (LABEL_IDS["Energy"], LABEL_IDS["Resources"]):
        assert widget.log_widget.isColumnHidden(column) == (verbosity < debug.LogLevel.HIGH)

    assert widget.start_button.text() == "Start"
    assert widget.status_label.text() == "Cancelled!" if cancel else "Final result!"
    assert widget._current_task is None
