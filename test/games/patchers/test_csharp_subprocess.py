from __future__ import annotations

import asyncio
import platform
import sys
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from randovania.games.prime2.patcher import csharp_subprocess
from randovania.patching.patchers.exceptions import UnableToExportError

if TYPE_CHECKING:
    from pathlib import Path

    import pytest_mock


@pytest.fixture(params=[False, True])
def mock_is_windows(request):
    with patch("randovania.games.prime2.patcher.csharp_subprocess.is_windows", return_value=request.param):
        yield request.param


@pytest.fixture(params=[False, True])
def mock_is_mac(request):
    with patch("randovania.games.prime2.patcher.csharp_subprocess.is_mac", return_value=request.param):
        yield request.param


@pytest.mark.parametrize(
    ("system_name", "expected"),
    [
        ("Windows", True),
        ("Linux", False),
    ],
)
def test_is_windows(mocker, system_name, expected):
    # Setup
    mocker.patch("platform.system", return_value=system_name)

    # Run
    result = csharp_subprocess.is_windows()

    # Assert
    assert result == expected


@pytest.mark.parametrize("add_mono", [False, True])
def test_process_command_no_thread(
    mock_is_windows, mock_is_mac, mocker: pytest_mock.MockerFixture, monkeypatch, tmp_path, add_mono
):
    if mock_is_mac and mock_is_windows:
        pytest.skip("Impossible to be two different OS at the same time.")

    one = tmp_path.joinpath("one")
    one.write_text("hi")

    mock_run = mocker.patch("asyncio.run")
    mock_process = mocker.patch(
        "randovania.games.prime2.patcher.csharp_subprocess._process_command_async", new_callable=MagicMock
    )

    read_callback = MagicMock()

    csharp_subprocess.IO_LOOP = None

    mock_set_event: MagicMock = mocker.patch("asyncio.set_event_loop_policy")
    loop_policy = MagicMock()
    monkeypatch.setattr(asyncio, "WindowsProactorEventLoopPolicy", loop_policy, raising=False)
    input_data = "hello\r\nthis is a nice db\r\n\r\nWe some crazy stuff."

    # Run
    csharp_subprocess.process_command(
        [
            str(one),
            "two",
        ],
        input_data,
        read_callback,
        add_mono_if_needed=add_mono,
    )

    # Assert
    mac_paths = ("/Library/Frameworks/Mono.framework/Versions/Current/Commands", "/usr/local/bin", "/opt/homebrew/bin")
    mock_process.assert_called_once_with(
        [
            *(["mono"] if add_mono and not mock_is_windows else []),
            str(one),
            "two",
        ],
        input_data,
        read_callback,
        () if not add_mono or add_mono and not mock_is_mac else mac_paths,
    )

    mock_run.assert_called_once_with(mock_process.return_value)
    if mock_is_windows:
        mock_set_event.assert_called_once_with(loop_policy.return_value)
    else:
        mock_set_event.assert_not_called()


def test_process_command_no_mono(mocker: pytest_mock.MockerFixture, tmp_path: Path, mock_is_windows) -> None:
    executable = tmp_path.joinpath("executable.bin")
    executable.write_bytes(b"hi")

    mocker.patch(
        "randovania.games.prime2.patcher.csharp_subprocess._process_command_async",
        new_callable=AsyncMock,
        side_effect=FileNotFoundError,
    )

    if mock_is_windows:
        expectation = pytest.raises(FileNotFoundError)
        if platform.system() != "Windows":
            pytest.skip("windows variant process_command can only be ran on windows")
    else:
        expectation = pytest.raises(UnableToExportError)

    with expectation:
        csharp_subprocess.process_command([str(executable)], "", MagicMock())


def test_process_command_file_doesnt_exist(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        csharp_subprocess.process_command([str(tmp_path.joinpath("missing.txt"))], "", MagicMock())


async def test_process_command_async(echo_tool):
    read_callback = MagicMock()

    # Run
    await csharp_subprocess._process_command_async(
        [sys.executable, str(echo_tool)],
        "hello\r\nthis is a nice db\r\n\r\nWe some crazy stuff.",
        read_callback,
    )

    # Assert
    read_callback.assert_has_calls(
        [
            call("hello"),
            call("this is a nice db"),
            call("We some crazy stuff."),
        ]
    )
