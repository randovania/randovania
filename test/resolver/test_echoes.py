from unittest.mock import patch, MagicMock, call

from randovania.games.prime.log_parser import RandomizerLog
from randovania.resolver import echoes
from randovania.resolver.echoes import ResolverConfiguration


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
