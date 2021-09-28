import datetime
import json
import logging
from pathlib import Path
from typing import Optional, List

import aiofiles
import aiohttp

from randovania.interface_common import persistence

_RELEASES_URL = "https://api.github.com/repos/randovania/randovania/releases"


def _last_check_file() -> Path:
    return persistence.local_data_dir() / "last_releases.json"


def _is_recent(last_check) -> bool:
    last_check_date = datetime.datetime.fromisoformat(last_check["last_check"])
    return (datetime.datetime.now() - last_check_date) <= datetime.timedelta(days=1)


async def _read_from_persisted() -> Optional[List[dict]]:
    try:
        async with aiofiles.open(_last_check_file()) as open_file:
            last_check = json.loads(await open_file.read())

        if _is_recent(last_check):
            return last_check["data"]
        else:
            return None

    except json.JSONDecodeError as e:
        logging.warning("Unable to decode persisted releases check: %s", str(e))
        return None

    except FileNotFoundError:
        return None


async def _download_from_github() -> Optional[List[dict]]:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(_RELEASES_URL) as response:
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError):
            return None


async def _persist(data: List[dict]):
    _last_check_file().parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(_last_check_file(), "w") as open_file:
        await open_file.write(
            json.dumps(
                {
                    "last_check": datetime.datetime.now().isoformat(),
                    "data": data,
                },
                default=str))


async def get_releases() -> Optional[List[dict]]:
    data = await _read_from_persisted()

    if data is None:
        data = await _download_from_github()
        if data is None:
            logging.warning("Unable to fetch release data from Github")
            return []
        await _persist(data)

    return data
