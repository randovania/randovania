import argparse
from asyncio import CancelledError
from unittest.mock import MagicMock, PropertyMock

import pytest
import pytest_mock

from randovania.cli.commands import benchmark
from randovania.games.game import RandovaniaGame


def test_generate_helper_success(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch("time.perf_counter", side_effect=[1, 20])
    mock_generate = mocker.patch("randovania.generator.generator.generate_and_validate_description")

    parameter = MagicMock()
    result = benchmark.generate_helper(parameter)

    mock_generate.assert_called_once_with(
        generator_params=parameter,
        status_update=None,
        validate_after_generation=True,
        attempts=0,
    )
    assert result == 19


def test_generate_helper_failure(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch("time.perf_counter", side_effect=[1, 20])
    mock_generate = mocker.patch(
        "randovania.generator.generator.generate_and_validate_description", side_effect=CancelledError()
    )

    parameter = MagicMock()
    result = benchmark.generate_helper(parameter)

    mock_generate.assert_called_once_with(
        generator_params=parameter,
        status_update=None,
        validate_after_generation=True,
        attempts=0,
    )
    assert result is None


def test_generate_list_of_permalinks(mocker: pytest_mock.MockerFixture) -> None:
    mock_submit = mocker.patch("concurrent.futures.ProcessPoolExecutor.submit")

    parameter = MagicMock()
    result = benchmark.generate_list_of_permalinks([parameter], 1)

    mock_submit.assert_called_once_with(benchmark.generate_helper, parameter)
    mock_submit.return_value.add_done_callback.assert_called()

    assert result == [None]


def test_compare_reports() -> None:
    mock = MagicMock()
    mock.get_preset.return_value.game = RandovaniaGame.BLANK

    parameters = [mock] * 6
    reference = [
        1,
        2,
        3,
        None,
        None,
        6,
    ]
    results = [
        5,
        2,
        5,
        4,
        None,
        None,
    ]

    benchmark.compare_reports(parameters, reference, results)


@pytest.mark.parametrize("no_data", [False, True])
def test_run_logic(mocker: pytest_mock.MockerFixture, no_data: bool) -> None:
    num_permalinks = 100 * sum(1 for _ in RandovaniaGame.all_games())
    results = [1.0] * num_permalinks
    mock_generate = mocker.patch("randovania.cli.commands.benchmark.generate_list_of_permalinks", return_value=results)
    mocker.patch("randovania.layout.permalink.Permalink.as_base64_str", new_callable=PropertyMock)

    args = argparse.Namespace()
    args.game = None
    args.no_data = no_data
    args.output_file = None

    benchmark.run_logic(args)

    if no_data:
        mock_generate.assert_not_called()
    else:
        mock_generate.assert_called_once()
