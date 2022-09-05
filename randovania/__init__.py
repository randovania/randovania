import json
import sys
from pathlib import Path

from randovania.version import version
from randovania.version_hash import git_hash, git_branch as _git_branch

CONFIGURATION_FILE_PATH: Path | None = None


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def is_dev_version():
    return ".dev" in VERSION and _git_branch != "stable"


def get_icon_path():
    if is_dev_version():
        icon_name = "dark_temple_key.ico"
    else:
        icon_name = "sky_temple_key_NqN_icon.ico"

    return get_data_path().joinpath("icons", icon_name)


def get_file_path() -> Path:
    if is_frozen():
        file_dir = Path(getattr(sys, "_MEIPASS"))
    else:
        file_dir = Path(__file__).parent
    return file_dir


def get_readme() -> Path:
    if is_frozen():
        return get_data_path().joinpath("README.md")
    return get_file_path().parent.joinpath("README.md")


def get_readme_section(section: str) -> str:
    readme = get_readme().read_text()

    start_comment = f"<!-- Begin {section} -->\n"
    end_comment = f"<!-- End {section} -->"

    start = readme.find(start_comment) + len(start_comment)
    end = readme.find(end_comment)

    return readme[start:end]


def get_data_path() -> Path:
    return get_file_path().joinpath("data")


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


def setup_logging(default_level: str, log_to_file: Path | None, quiet: bool = False):
    import logging.config
    import logging.handlers
    import time

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

    logging.Formatter.converter = time.gmtime
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
    if not quiet:
        logging.info("Logging initialized with level %s for version %s.", default_level, VERSION)


__version__ = version
VERSION = version
GIT_HASH = git_hash
