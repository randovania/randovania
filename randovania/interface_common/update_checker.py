import datetime
import threading
from typing import Callable, Optional, Tuple, NamedTuple

import requests
from dataset import Table

from randovania import VERSION
from randovania.interface_common import persistence

_LATEST_RELEASE_URL = "https://api.github.com/repos/henriquegemignani/randovania/releases/latest"


class VersionDescription(NamedTuple):
    tag_name: str
    html_url: str


def _table() -> Table:
    db = persistence.db()
    return db.create_table(
        "update_checker",
        primary_id='source',
        primary_type=db.types.string(25)
    )


def _is_recent(last_check) -> bool:
    return (datetime.datetime.now() - last_check["last_check"]) <= datetime.timedelta(days=1)


def _read_from_db() -> Optional[VersionDescription]:
    last_check = _table().find_one(source='github')
    if last_check is not None and _is_recent(last_check):
        return VersionDescription(last_check["tag_name"], last_check["html_url"])
    else:
        return None


def _download_from_github() -> Optional[VersionDescription]:
    latest_release = requests.get(_LATEST_RELEASE_URL)
    if latest_release.ok:
        data = latest_release.json()
        return VersionDescription(data["tag_name"], data["html_url"])
    else:
        return None


def _persist_version(version: VersionDescription):
    _table().upsert(
        {
            "source": "github",
            "last_check": datetime.datetime.now(),
            "tag_name": version.tag_name,
            "html_url": version.html_url,
        },
        ["source"])


def _get_latest_version_work(on_result: Callable[[str, str], None]):
    version = _read_from_db()

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
