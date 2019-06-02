from unittest.mock import patch, MagicMock

from randovania.cli.commands import batch_distribute
from randovania.layout.permalink import Permalink


@patch("randovania.generator.generator.generate_description", autospec=True)
@patch("time.perf_counter", autospec=False)  # TODO: pytest-qt bug
def test_batch_distribute_helper(mock_perf_counter: MagicMock,
                                 mock_generate_description: MagicMock,
                                 ):
    # Setup
    base_permalink = MagicMock()
    seed_number = 5000
    validate = MagicMock()
    output_dir = MagicMock()

    expected_permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        patcher_configuration=base_permalink.patcher_configuration,
        layout_configuration=base_permalink.layout_configuration,
    )

    mock_perf_counter.side_effect = [1000, 5000]

    # Run
    delta_time = batch_distribute.batch_distribute_helper(base_permalink, seed_number, validate, output_dir)

    # Assert
    mock_generate_description.assert_called_once_with(expected_permalink, None, validate)
    assert delta_time == 4000
    output_dir.joinpath.assert_called_once_with("{}.json".format(seed_number))
    mock_generate_description.return_value.save_to_file.assert_called_once_with(output_dir.joinpath.return_value)
