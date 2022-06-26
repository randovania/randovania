import datetime
import json
import logging
from pathlib import Path

import aiofiles
import aiohttp

from randovania.interface_common import persistence

_RELEASES_URL = "https://api.github.com/repos/randovania/randovania/releases"


def _last_check_file() -> Path:
    return persistence.local_data_dir() / "last_releases.json"


def _is_recent(last_check) -> bool:
    last_check_date = datetime.datetime.fromisoformat(last_check["last_check"])
    return (datetime.datetime.now() - last_check_date) <= datetime.timedelta(days=1)


async def _read_from_persisted() -> list[dict] | None:
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


async def _download_from_github(page_size: int = 100) -> list[dict] | None:
    async with aiohttp.ClientSession() as session:
        try:
            result = []

            current_page = 1

            while True:
                async with session.get(_RELEASES_URL,
                                       params={"page": current_page, "per_page": page_size}) as response:
                    response.raise_for_status()
                    last_result = await response.json()
                    result.extend(last_result)
                    if len(last_result) < page_size:
                        return result

                    current_page += 1

        except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError):
            return None


async def _persist(data: list[dict]):
    _last_check_file().parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(_last_check_file(), "w") as open_file:
        await open_file.write(
            json.dumps(
                {
                    "last_check": datetime.datetime.now().isoformat(),
                    "data": data,
                },
                default=str))


async def get_releases() -> list[dict] | None:
    data = await _read_from_persisted()

    if data is None:
        data = await _download_from_github()
        if data is None:
            logging.warning("Unable to fetch release data from Github")
            return []
        await _persist(data)

    return data
