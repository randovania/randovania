import datetime
import json
import logging
import threading
from pathlib import Path
from typing import Callable, Optional, NamedTuple

import requests

from randovania import VERSION
from randovania.interface_common import persistence

_LATEST_RELEASE_URL = "https://api.github.com/repos/henriquegemignani/randovania/releases/latest"


class VersionDescription(NamedTuple):
    tag_name: str
    html_url: str


def _last_check_file() -> Path:
    return persistence.user_data_dir() / "last_version_check.json"


def _is_recent(last_check) -> bool:
    last_check_date = datetime.datetime.fromisoformat(last_check["last_check"])
    return (datetime.datetime.now() - last_check_date) <= datetime.timedelta(days=1)


def _read_from_persisted() -> Optional[VersionDescription]:
    try:
        with _last_check_file().open() as open_file:
            last_check = json.load(open_file)

        if _is_recent(last_check):
            return VersionDescription(last_check["tag_name"], last_check["html_url"])
        else:
            return None

    except json.JSONDecodeError as e:
        logging.warning("Unable to decode persisted last update check: %s", str(e))
        return None

    except FileNotFoundError:
        return None


def _download_from_github() -> Optional[VersionDescription]:
    latest_release = requests.get(_LATEST_RELEASE_URL)
    if latest_release.ok:
        data = latest_release.json()
        return VersionDescription(data["tag_name"], data["html_url"])
    else:
        return None


def _persist_version(version: VersionDescription):
    _last_check_file().parent.mkdir(parents=True, exist_ok=True)
    with _last_check_file().open("w") as open_file:
        json.dump({
            "source": "github",
            "last_check": datetime.datetime.now().isoformat(),
            "tag_name": version.tag_name,
            "html_url": version.html_url,
        }, open_file, default=str)


def _get_latest_version_work(on_result: Callable[[str, str], None]):
    version = _read_from_persisted()

    if version is None:
        version = _download_from_github()
        if version is not None:
            _persist_version(version)

    if version is not None:
        if version.tag_name != "v{}".format(VERSION):
            on_result(version.tag_name, version.html_url)


def get_latest_version(on_result: Callable[[str, str], None]):
    def work():
        _get_latest_version_work(on_result)

    background_thread = threading.Thread(target=work)
    background_thread.start()
