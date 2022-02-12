from unittest.mock import AsyncMock, MagicMock, call

import aiohttp

from randovania.interface_common import github_releases_data


async def test_download_from_github_success(mocker):
    # Setup
    page_size = 5
    response_a = AsyncMock()
    response_b = AsyncMock()
    responses = [response_a, response_b]

    mock_get_response: MagicMock = mocker.patch.object(aiohttp.ClientSession, 'get')
    mock_get_response.side_effect = responses
    for r in responses:
        r.__aenter__.return_value.raise_for_status = MagicMock()

    response_a.__aenter__.return_value.json = AsyncMock(return_value=[1, 2, 3, 4, 5])
    response_b.__aenter__.return_value.json = AsyncMock(return_value=[6, 7])

    # Run
    returned_value = await github_releases_data._download_from_github(page_size=page_size)

    # Assert
    mock_get_response.assert_has_calls([
        call(
            github_releases_data._RELEASES_URL,
            params={"page": 1, "per_page": page_size},
        ),
        call(
            github_releases_data._RELEASES_URL,
            params={"page": 2, "per_page": page_size},
        ),
    ])
    for r in responses:
        r.__aenter__.return_value.raise_for_status.assert_called_once_with()
        r.__aenter__.return_value.json.assert_awaited()
    assert returned_value == [1, 2, 3, 4, 5, 6, 7]


async def test_download_from_github_bad_response_is_caught(mocker):
    # Setup
    mock_get_response: MagicMock = mocker.patch.object(aiohttp.ClientSession, 'get')
    mock_get_response.return_value.__aenter__.return_value.raise_for_status = MagicMock(
        side_effect=aiohttp.ClientResponseError(None, None))

    # Run
    returned_value = await github_releases_data._download_from_github()

    # Assert
    mock_get_response.assert_called()
    mock_get_response.return_value.__aenter__.return_value.raise_for_status.assert_called()
    assert returned_value is None


async def test_download_from_github_connection_failure_is_caught(mocker):
    # Setup
    mock_get_response: MagicMock = mocker.patch.object(aiohttp.ClientSession, 'get',
                                                       side_effect=aiohttp.ClientConnectionError())

    # Run
    returned_value = await github_releases_data._download_from_github()

    # Assert
    mock_get_response.assert_called()
    assert returned_value is None
