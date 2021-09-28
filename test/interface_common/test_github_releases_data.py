import aiohttp
import pytest
from unittest.mock import AsyncMock, MagicMock
from randovania.interface_common import github_releases_data

@pytest.mark.asyncio
async def test_download_from_github_success(mocker):
    # Setup
    mock_get_response: MagicMock = mocker.patch.object(aiohttp.ClientSession, 'get')
    mock_get_response.return_value.__aenter__.return_value.json = AsyncMock()
 
    # Run
    returned_value = await github_releases_data._download_from_github()
    
    # Assert
    mock_get_response.assert_called()
    mock_get_response.return_value.__aenter__.return_value.json.assert_awaited()
    assert returned_value == mock_get_response.return_value.__aenter__.return_value.json.return_value


@pytest.mark.asyncio
async def test_download_from_github_bad_response_is_caught(mocker):
    # Setup
    mock_get_response: MagicMock = mocker.patch.object(aiohttp.ClientSession, 'get')
    mock_get_response.return_value.__aenter__.return_value.raise_for_status = MagicMock(side_effect = aiohttp.ClientResponseError(None, None))
 
    # Run
    returned_value = await github_releases_data._download_from_github()
    
    # Assert
    mock_get_response.assert_called()
    mock_get_response.return_value.__aenter__.return_value.raise_for_status.assert_called()
    assert returned_value == None


@pytest.mark.asyncio
async def test_download_from_github_connection_failure_is_caught(mocker):
    # Setup
    mock_get_response: MagicMock = mocker.patch.object(aiohttp.ClientSession, 'get', side_effect=aiohttp.ClientConnectionError())

    # Run
    returned_value = await github_releases_data._download_from_github()
    
    # Assert
    mock_get_response.assert_called()
    assert returned_value == None
