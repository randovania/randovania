from unittest.mock import MagicMock

from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.layout.permalink import Permalink


def test_generate_layout(mocker):
    # Setup
    options: Options = MagicMock()
    permalink: Permalink = MagicMock()
    progress_update = MagicMock()

    mock_generate_layout = mocker.patch("randovania.interface_common.echoes.generate_description", autospec=True)
    mock_constant_percentage_callback = mocker.patch(
        "randovania.interface_common.simplified_patcher.ConstantPercentageCallback",
        autospec=False,  # TODO: pytest-qt bug
    )

    # Run
    simplified_patcher.generate_layout(options, permalink, progress_update)

    # Assert
    mock_constant_percentage_callback.assert_called_once_with(progress_update, -1)
    mock_generate_layout.assert_called_once_with(
        permalink=permalink,
        status_update=mock_constant_percentage_callback.return_value,
        validate_after_generation=options.advanced_validate_seed_after,
        timeout_during_generation=options.advanced_timeout_during_generation,
        attempts=None,
    )
