import json
import os
import random
from pathlib import Path

from cryptography.fernet import Fernet

_FOLDER = Path(__file__).parent


def main():
    with _FOLDER.joinpath("dev-server-configuration.json").open("w") as f:
        json.dump({
            "server_address": "http://127.0.0.1:5000",
            "socketio_path": "/socket.io",
            "guest_secret": Fernet.generate_key().decode("ascii"),
            "discord_client_id": "",
            "server_config": {
                "secret_key": "dev-server-{}".format(random.randint(1000, 9999)),
                "fernet_key": Fernet.generate_key().decode("ascii"),
                "client_version_checking": "ignore",
                "database_path": os.fspath(_FOLDER.joinpath("data.db")),
                "discord_client_secret": "",
            }
        }, f, indent=4)


if __name__ == '__main__':
    main()