import asyncio
import platform
import sys
from unittest.mock import patch, MagicMock, call

import pytest

from randovania.games.patchers import csharp_subprocess


@pytest.fixture(
    params=[False, True],
    name="mock_is_windows")
def _mock_is_windows(request):
    with patch("randovania.games.patchers.csharp_subprocess.is_windows", return_value=request.param):
        yield request.param


@pytest.mark.parametrize(["system_name", "expected"], [
    ("Windows", True),
    ("Linux", False),
])
def test_is_windows(mocker, system_name, expected):
    # Setup
    mocker.patch("platform.system", return_value=system_name)

    # Run
    result = csharp_subprocess.is_windows()

    # Assert
    assert result == expected


def test_process_command_no_thread(echo_tool, mock_is_windows, mocker, monkeypatch):
    read_callback = MagicMock()

    csharp_subprocess.IO_LOOP = None
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    mock_set_event: MagicMock = mocker.patch("asyncio.set_event_loop_policy")
    loop_policy = MagicMock()
    monkeypatch.setattr(asyncio, "WindowsProactorEventLoopPolicy", loop_policy, raising=False)

    # Run
    csharp_subprocess.process_command(
        [
            sys.executable,
            str(echo_tool)
        ],
        "hello\r\nthis is a nice world\r\n\r\nWe some crazy stuff.",
        read_callback,
        add_mono_if_needed=False,
    )

    # Assert
    read_callback.assert_has_calls([
        call("hello"),
        call("this is a nice world"),
        call("We some crazy stuff."),
    ])
    if mock_is_windows:
        mock_set_event.assert_called_once_with(loop_policy.return_value)
    else:
        mock_set_event.assert_not_called()
