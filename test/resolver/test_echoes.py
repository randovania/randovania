from unittest.mock import patch, MagicMock, call

import pytest

from randovania.games.prime.log_parser import RandomizerLog
from randovania.resolver import echoes
from randovania.resolver.echoes import ResolverConfiguration, RandomizerConfiguration


@patch("randovania.resolver.resolver.resolve", autospec=True)
@patch("randovania.resolver.data_reader.decode_data", autospec=True)
def test_run_resolver_failure(mock_decode_data: MagicMock,
                              mock_resolve: MagicMock):
    data = MagicMock()
    randomizer_log = MagicMock(spec=RandomizerLog)
    resolver_config = MagicMock(spec=ResolverConfiguration)
    mock_resolve.return_value = None

    final_state = echoes.run_resolver(data, randomizer_log, resolver_config)

    # Assert
    assert final_state is None
    mock_resolve.assert_called_once_with(
        resolver_config.difficulty,
        resolver_config.enabled_tricks,
        resolver_config.item_loss,
        mock_decode_data.return_value
    )
    mock_decode_data.assert_called_once_with(data, randomizer_log.pickup_database, randomizer_log.elevators)


@patch("randovania.resolver.resolver.resolve", autospec=True)
@patch("randovania.resolver.data_reader.decode_data", autospec=True)
def test_run_resolver_success_without_minimum_difficulty(
        mock_decode_data: MagicMock,
        mock_resolve: MagicMock):
    data = MagicMock()
    randomizer_log = MagicMock(spec=RandomizerLog)
    resolver_config = MagicMock(spec=ResolverConfiguration)
    resolver_config.minimum_difficulty = 0

    final_state = echoes.run_resolver(data, randomizer_log, resolver_config)

    # Assert
    assert final_state is mock_resolve.return_value
    mock_resolve.assert_called_once_with(
        resolver_config.difficulty,
        resolver_config.enabled_tricks,
        resolver_config.item_loss,
        mock_decode_data.return_value
    )
    mock_decode_data.assert_called_once_with(data, randomizer_log.pickup_database, randomizer_log.elevators)


@patch("randovania.resolver.resolver.resolve", autospec=True)
@patch("randovania.resolver.data_reader.decode_data", autospec=True)
def test_run_resolver_success_with_minimum_difficulty(
        mock_decode_data: MagicMock,
        mock_resolve: MagicMock):
    data = MagicMock()
    randomizer_log = MagicMock(spec=RandomizerLog)
    resolver_config = MagicMock(spec=ResolverConfiguration)
    resolver_config.minimum_difficulty = 1
    success_response = MagicMock()

    mock_resolve.side_effect = [success_response, None]

    final_state = echoes.run_resolver(data, randomizer_log, resolver_config)

    # Assert
    assert final_state is success_response
    mock_resolve.assert_has_calls([
        call(resolver_config.difficulty, resolver_config.enabled_tricks,
             resolver_config.item_loss, mock_decode_data.return_value),
        call(resolver_config.minimum_difficulty - 1, resolver_config.enabled_tricks,
             resolver_config.item_loss, mock_decode_data.return_value),
    ])
    mock_decode_data.assert_called_once_with(data, randomizer_log.pickup_database, randomizer_log.elevators)


@patch("randovania.resolver.resolver.resolve", autospec=True)
@patch("randovania.resolver.data_reader.decode_data", autospec=True)
def test_run_resolver_failure_due_to_minimum_difficulty(
        mock_decode_data: MagicMock,
        mock_resolve: MagicMock):
    data = MagicMock()
    randomizer_log = MagicMock(spec=RandomizerLog)
    resolver_config = MagicMock(spec=ResolverConfiguration)
    resolver_config.minimum_difficulty = 1
    mock_resolve.return_value = MagicMock()

    final_state = echoes.run_resolver(data, randomizer_log, resolver_config)

    # Assert
    assert final_state is None
    mock_resolve.assert_has_calls([
        call(resolver_config.difficulty, resolver_config.enabled_tricks,
             resolver_config.item_loss, mock_decode_data.return_value),
        call(resolver_config.minimum_difficulty - 1, resolver_config.enabled_tricks,
             resolver_config.item_loss, mock_decode_data.return_value),
    ])
    mock_decode_data.assert_called_once_with(data, randomizer_log.pickup_database, randomizer_log.elevators)


@patch("randovania.resolver.echoes.run_resolver", autospec=True)
@patch("randovania.games.prime.log_parser.generate_log", autospec=True)
def test_generate_and_validate(mock_generate_log: MagicMock,
                               mock_run_resolver: MagicMock):
    data = MagicMock()
    randomizer_config = MagicMock(spec=RandomizerConfiguration)
    resolver_config = MagicMock(spec=ResolverConfiguration)
    input_queue = MagicMock()
    output_queue = MagicMock()
    seed = MagicMock()
    input_queue.get.side_effect = [seed, None]

    with pytest.raises(RuntimeError) as e:
        echoes.generate_and_validate(data,
                                     randomizer_config,
                                     resolver_config,
                                     input_queue,
                                     output_queue)
        assert e == "generate_and_validate got None from input queue"

    # Asserts
    mock_generate_log.assert_called_once_with(seed,
                                              randomizer_config.exclude_pickups,
                                              randomizer_config.randomize_elevators)
    mock_run_resolver(data=data,
                      randomizer_log=mock_generate_log.return_value,
                      resolver_config=resolver_config,
                      verbose=False)
    output_queue.put.assert_called_once_with((seed, mock_run_resolver.return_value))


@pytest.mark.parametrize("starting_seed", range(10000, 30000, 10000))
@pytest.mark.parametrize("seeds_to_generate", range(5, 10))
@pytest.mark.parametrize("cpu_count", range(1, 4))
@patch("multiprocessing.Process", autospec=True)
@patch("multiprocessing.Queue", autospec=True)
def test_search_seed(mock_queue: MagicMock,
                     mock_process: MagicMock,
                     starting_seed: int,
                     seeds_to_generate: int,
                     cpu_count: int):
    data = MagicMock(spec=RandomizerConfiguration)
    randomizer_config = MagicMock(spec=RandomizerConfiguration)
    resolver_config = MagicMock(spec=ResolverConfiguration)
    seed_report = MagicMock()

    input_queue = MagicMock()
    output_queue = MagicMock()
    mock_queue.side_effect = [input_queue, output_queue]

    output_queue.get.side_effect = [
                                       (starting_seed + i, False)
                                       for i in range(seeds_to_generate - 1)
                                   ] + [(starting_seed + seeds_to_generate, True), None, None]

    processes = [MagicMock() for _ in range(cpu_count)]
    mock_process.side_effect = processes

    # Call
    final_seed, seed_count = echoes.search_seed(
        data=data,
        randomizer_config=randomizer_config,
        resolver_config=resolver_config,
        cpu_count=cpu_count,
        seed_report=seed_report,
        start_on_seed=starting_seed)

    # Assertions
    assert final_seed == starting_seed + seeds_to_generate
    assert seed_count == seeds_to_generate

    input_queue.put_nowait.assert_has_calls([
        call(starting_seed + i)
        for i in range(seeds_to_generate)
    ])
    seed_report.assert_has_calls([
        call(i + 1)
        for i in range(seeds_to_generate - 1)
    ])

    mock_process.assert_has_calls([
        call(
            target=echoes.generate_and_validate,
            args=(data, randomizer_config, resolver_config, input_queue, output_queue)
        )
        for _ in range(cpu_count)
    ])
    for process in processes:
        process.start.assert_called_once_with()
        process.terminate.assert_called_once_with()
