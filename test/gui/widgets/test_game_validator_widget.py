from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import ANY, MagicMock

import pytest

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.gui.widgets import game_validator_widget
from randovania.gui.widgets.game_validator_widget import LABEL_IDS, ValidatorWidgetResolverLogger
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_mock import MockerFixture

    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.game_description.resources.resource_info import ResourceGainTuple, ResourceQuantity


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
async def test_on_start_button_no_task(
    widget, mocker: MockerFixture, blank_game_description, cancel: bool, verbosity: int
):
    widget._verbosity = verbosity

    def mock_state(
        node_id: NodeIdentifier,
        *,
        resources: ResourceGainTuple = (),
        target: PickupTarget | None = None,
        path: Iterable[NodeIdentifier] = (),
    ) -> MagicMock:
        state = MagicMock()
        state.node = blank_game_description.node_by_identifier(node_id)
        state.game_state_debug_string.return_value = "100/100 Energy"
        if isinstance(state.node, PickupNode):
            state.patches.pickup_assignment = {state.node.pickup_index: target}
        state.path_from_previous_state = tuple(
            blank_game_description.node_by_identifier(path_node) for path_node in path
        )
        return state

    def res(res_type: ResourceType, name: str, amount: int = 1) -> ResourceQuantity:
        info = SimpleResourceInfo(0, name, name, res_type)
        return info, amount

    def satisfiable(node: NodeIdentifier) -> tuple[ResourceNode, Any]:
        return (blank_game_description.node_by_identifier(node), MagicMock())

    async def side_effect(logger: ValidatorWidgetResolverLogger, *args: Any):
        assert widget.start_button.text() == "Stop"
        assert widget.status_label.text() == "Running..."
        logger.logger_start()

        logger.log_action(
            mock_state(
                NodeIdentifier("Intro", "Starting Area", "Spawn Point"),
            )
        )
        logger.log_action(
            mock_state(
                NodeIdentifier("Intro", "Starting Area", "Pickup (Weapon)"),
                target=PickupTarget(
                    blank_game_description.get_pickup_database().standard_pickups["Blue Key"],
                    player=0,
                ),
                resources=(
                    res(ResourceType.NODE_IDENTIFIER, "Pickup (Weapon)"),
                    res(ResourceType.ITEM, "Blue Key"),
                ),
            )
        )
        logger.log_checking_satisfiable(
            [
                satisfiable(NodeIdentifier("Intro", "Starting Area", "Lock - Door to Boss Arena")),
            ]
        )
        logger.log_action(
            mock_state(
                NodeIdentifier("Intro", "Starting Area", "Spawn Point"),
                resources=(res(ResourceType.NODE_IDENTIFIER, "Spawn Point"),),
                path=(NodeIdentifier("Intro", "Back-Only Lock Room", "Door to Starting Area"),),
            )
        )
        logger.log_rollback(
            mock_state(NodeIdentifier("Intro", "Starting Area", "Spawn Point")),
            False,
            False,
            MagicMock(),
        )
        logger.log_action(
            mock_state(
                NodeIdentifier("Intro", "Back-Only Lock Room", "Event - Key Switch 1"),
                resources=(res(ResourceType.EVENT, "Key Switch 1"),),
            )
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

    if verbosity >= debug.LogLevel.NORMAL:
        region_item = widget.log_widget.topLevelItem(0)
        assert region_item.childCount() == 5
        assert region_item.text(LABEL_IDS["Node"]) == "Intro"

        assert not region_item.child(0).isExpanded()

        pickup_action = region_item.child(1)
        assert pickup_action.text(LABEL_IDS["Type"]) == "Major"
        assert pickup_action.text(LABEL_IDS["Action"]) == "Blue Key"

        other_action = region_item.child(2)
        assert other_action.text(LABEL_IDS["Type"]) == "Start"
        assert other_action.text(LABEL_IDS["Action"]) == ""

        rollback = region_item.child(3)
        assert rollback.text(LABEL_IDS["Node"]) == "Rollback Starting Area/Spawn Point"
        assert rollback.text(LABEL_IDS["Type"]) == "Rollback"

    if verbosity >= debug.LogLevel.HIGH:
        child = pickup_action.child(0)
        assert child.text(0) == "Satisfiable actions"
        assert child.child(0).text(LABEL_IDS["Node"]) == "• Intro/Starting Area/Lock - Door to Boss Arena"

    if verbosity >= debug.LogLevel.EXTREME:
        child = pickup_action.child(1)
        assert child.text(LABEL_IDS["Node"]) == "↪ Intro/Back-Only Lock Room/Door to Starting Area"

    for column in (LABEL_IDS["Energy"], LABEL_IDS["Resources"]):
        assert widget.log_widget.isColumnHidden(column) == (verbosity < debug.LogLevel.HIGH)

    assert widget.start_button.text() == "Start"
    assert widget.status_label.text() == "Cancelled!" if cancel else "Final result!"
    assert widget._current_task is None


async def test_on_start_button_with_resolver(skip_qtbot, test_files_dir):
    layout = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "blank/issue-3717.rdvgame"))
    players = PlayersConfiguration(
        player_index=0,
        player_names={0: "Player"},
    )
    widget = game_validator_widget.GameValidatorWidget(layout, players)
    skip_qtbot.addWidget(widget)

    # Run
    await widget.on_start_button()

    assert widget.start_button.text() == "Start"
    assert widget.status_label.text().endswith("Game is possible.")
    assert widget._current_task is None
