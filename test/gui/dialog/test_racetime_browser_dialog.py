import pytest
from mock import AsyncMock, ANY, MagicMock

from randovania.gui.dialog.racetime_browser_dialog import RacetimeBrowserDialog


@pytest.mark.parametrize("success", [False, True])
@pytest.mark.asyncio
async def test_attempt_join_success(skip_qtbot, mocker, success):
    # Setup
    permalink = MagicMock()

    def from_str(s: str):
        if s == "<permalink>":
            return permalink
        raise ValueError("Invalid permalink")

    raw_data = {
        "current_races": [
            {
                "name": "Race 1",
                "status": {
                    "value": "open",
                    "verbose_value": "Open",
                    "help_text": "Anyone may join this race"
                },
                "goal": {
                    "name": "Beat the game",
                    "custom": False
                },
                "info": "<permalink>",
                "entrants_count": 1,
                "entrants_count_inactive": 0,
                "opened_at": "2020-10-01T18:00:00.000Z"
            },
            {
                "name": "Race 2",
                "status": {
                    "value": "open",
                    "verbose_value": "Open",
                    "help_text": "Anyone may join this race"
                },
                "goal": {
                    "name": "Beat the game",
                    "custom": False
                },
                "info": "random_stuff",
                "entrants_count": 1,
                "entrants_count_inactive": 0,
                "opened_at": "2020-10-01T18:00:00.000Z"
            }
        ]
    }

    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_from_str = mocker.patch("randovania.layout.permalink.Permalink.from_str", side_effect=from_str)
    mocker.patch("randovania.gui.dialog.racetime_browser_dialog._query_server", new_callable=AsyncMock,
                 return_value=raw_data)
    dialog = RacetimeBrowserDialog()

    # Run
    await dialog.refresh()
    dialog.table_widget.selectRow(0 if success else 1)
    await dialog.attempt_join()

    # Assert
    mock_from_str.assert_called_once()
    if success:
        mock_warning.assert_not_called()
        assert dialog.permalink is permalink
    else:
        mock_warning.assert_awaited_once_with(dialog, ANY, ANY)
        assert dialog.permalink is None
