import threading
from typing import Callable

import requests

from randovania import VERSION

_LATEST_RELEASE_URL = "https://api.github.com/repos/henriquegemignani/randovania/releases/latest"


def get_latest_version(on_result: Callable[[str, str], None]):
    def work():
        latest_release = requests.get(_LATEST_RELEASE_URL)
        if latest_release.ok:
            data = latest_release.json()
            if data["tag_name"] != "v{}".format(VERSION):
                on_result(
                    data["tag_name"],
                    data["html_url"]
                )

    background_thread = threading.Thread(target=work)
    background_thread.start()
