import json
import sys
from pathlib import Path
from typing import Optional

from randovania.version import version

CONFIGURATION_FILE_PATH: Optional[Path] = None


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_data_path() -> Path:
    if is_frozen():
        file_dir = Path(getattr(sys, "_MEIPASS"))
    else:
        file_dir = Path(__file__).parent
    return file_dir.joinpath("data")


def _get_default_configuration_path() -> Path:
    return get_data_path().joinpath("configuration.json")


def get_configuration() -> dict:
    file_path = CONFIGURATION_FILE_PATH
    if file_path is None:
        file_path = _get_default_configuration_path()

    try:
        with file_path.open() as file:
            return json.load(file)
    except FileNotFoundError:
        if CONFIGURATION_FILE_PATH is None:
            return {
                "server_address": "http://127.0.0.1:5000",
                "socketio_path": "/socket.io",
            }
        else:
            raise


def setup_logging(default_level: str, log_to_file: Optional[Path]):
    import logging.config
    import logging.handlers

    handlers = {
        'default': {
            'level': default_level,
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    }
    if log_to_file is not None:
        handlers['local_app_data'] = {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': log_to_file,
            'encoding': 'utf-8',
            'backupCount': 10,
        }

    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] [%(levelname)s] [%(name)s] %(funcName)s: %(message)s',
            }
        },
        'handlers': handlers,
        'loggers': {
            'randovania.network_client.network_client': {
                'level': 'DEBUG',
            },
            'randovania.game_connection.connection_backend': {
                'level': 'DEBUG',
            },
            'randovania.gui.multiworld_client': {
                'level': 'DEBUG',
            },
            'NintendontExecutor': {
                'level': 'DEBUG',
            },
            'DolphinExecutor': {
                'level': 'DEBUG',
            },
            'Prime1RemoteConnector': {
                'level': 'DEBUG',
            },
            'EchoesRemoteConnector': {
                'level': 'DEBUG',
            },
            'CorruptionRemoteConnector': {
                'level': 'DEBUG',
            },
            'randovania.gui.qt': {
                'level': 'INFO',
            },
            'qasync': {
                'level': 'INFO',
            },
            # 'socketio.client': {
            #     'level': 'DEBUG',
            # }
        },
        'root': {
            'level': default_level,
            'handlers': list(handlers.keys()),
        },
    })
    logging.info("Logging initialized with level %s for version %s.", default_level, VERSION)


__version__ = version
VERSION = version
