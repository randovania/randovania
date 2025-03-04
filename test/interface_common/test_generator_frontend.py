from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.interface_common import generator_frontend
from randovania.layout.generator_parameters import GeneratorParameters

if TYPE_CHECKING:
    import pytest_mock

    from randovania.interface_common.options import Options


@pytest.mark.parametrize("retries", [None, 5])
@pytest.mark.parametrize("timeout", [False, True])
@pytest.mark.parametrize("spoiler", [False, True])
@pytest.mark.parametrize("another_process", [False, True])
def test_generate_layout(mocker: pytest_mock.MockerFixture, another_process, spoiler, timeout, retries):
    # Setup
    options: Options = MagicMock()
    options.advanced_generate_in_another_process = another_process
    options.advanced_timeout_during_generation = timeout
    parameters = MagicMock()
    parameters.spoiler = spoiler
    progress_update = MagicMock()
    world_names = MagicMock()

    mock_debug_level = mocker.patch("randovania.resolver.debug.debug_level")
    mock_generate_another_process = mocker.patch(
        "randovania.interface_common.generator_frontend.generate_in_another_process", autospec=True
    )
    mock_generate_host_process = mocker.patch(
        "randovania.interface_common.generator_frontend.generate_in_host_process", autospec=True
    )
    mock_constant_percentage_callback = mocker.patch(
        "randovania.interface_common.generator_frontend.ConstantPercentageCallback",
        autospec=False,  # TODO: pytest-qt bug
    )

    if another_process:
        correct_mock = mock_generate_another_process
        wrong_mock = mock_generate_host_process
    else:
        correct_mock = mock_generate_host_process
        wrong_mock = mock_generate_another_process

    if spoiler:
        debug_level = mock_debug_level.return_value
    else:
        debug_level = 0

    extra_args = {
        "generator_params": parameters,
        "validate_after_generation": options.advanced_validate_seed_after,
        "world_names": world_names,
    }

    if not timeout:
        extra_args["timeout"] = None

    if retries is not None:
        extra_args["attempts"] = retries

    # Run
    generator_frontend.generate_layout(options, parameters, progress_update, retries=retries, world_names=world_names)

    # Assert
    mock_debug_level.assert_called_once_with()
    mock_constant_percentage_callback.assert_called_once_with(progress_update, -1)
    correct_mock.assert_called_once_with(
        status_update=mock_constant_percentage_callback.return_value,
        debug_level=debug_level,
        extra_args=extra_args,
    )
    wrong_mock.assert_not_called()


def test_general_blank_layout(default_blank_preset):
    # Setup
    options: Options = MagicMock()
    options.advanced_validate_seed_after = True
    options.advanced_timeout_during_generation = True
    options.advanced_generate_in_another_process = True

    parameters = GeneratorParameters(
        seed_number=1000,
        spoiler=True,
        presets=[default_blank_preset],
        development=True,
    )

    progress_update = MagicMock()

    # Run
    result = generator_frontend.generate_layout(options, parameters, progress_update)

    # Assert
    assert result.generator_parameters == parameters
    assert result.get_seed_for_player(0) == 1000
