from mock import MagicMock, AsyncMock

from randovania.cli.commands import batch_distribute
from randovania.layout.permalink import Permalink


def test_batch_distribute_helper(mocker):
    # Setup
    description = MagicMock()
    mock_generate_description: AsyncMock = mocker.patch(
        "randovania.generator.generator.generate_and_validate_description",
        new_callable=AsyncMock, return_value=description)
    mock_perf_counter = mocker.patch("time.perf_counter", autospec=False)  # TODO: pytest-qt bug

    base_permalink = MagicMock()
    seed_number = 5000
    validate = MagicMock()
    output_dir = MagicMock()
    timeout = 67
    description.file_extension.return_value = "rdvgame"

    expected_permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        presets=base_permalink.presets,
    )

    mock_perf_counter.side_effect = [1000, 5000]

    # Run
    delta_time = batch_distribute.batch_distribute_helper(base_permalink, seed_number, timeout, validate, output_dir)

    # Assert
    mock_generate_description.assert_awaited_once_with(permalink=expected_permalink, status_update=None,
                                                       validate_after_generation=validate, timeout=timeout,
                                                       attempts=0)

    assert delta_time == 4000
    output_dir.joinpath.assert_called_once_with("{}.rdvgame".format(seed_number))
    description.save_to_file.assert_called_once_with(output_dir.joinpath.return_value)
