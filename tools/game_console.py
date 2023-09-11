from __future__ import annotations

import argparse
import asyncio
import logging.config
import os
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication

from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder
from randovania.game_connection.game_connection import GameConnection
from randovania.network_common.game_connection_status import GameConnectionStatus

if TYPE_CHECKING:
    from randovania.game_connection.builder.connector_builder import ConnectorBuilder

should_quit = False
old_hook = sys.excepthook


async def worker(connector_builder: ConnectorBuilder):
    connection = GameConnection(connector_builder)

    await connection.start()
    try:
        while connection.current_status not in (GameConnectionStatus.InGame, GameConnectionStatus.TrackerOnly):
            await asyncio.sleep(1)
            print(connection.pretty_current_status)

        await asyncio.sleep(20)

    except KeyboardInterrupt:
        return

    finally:
        await connection.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nintendont", help="Connect to the given IP via the Nintendont protocol instead.")
    args = parser.parse_args()

    app = QCoreApplication(sys.argv)

    os.environ["QT_API"] = "PySide6"
    import qasync

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(funcName)s: %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "level": "DEBUG",
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",  # Default is stderr
                },
            },
            "loggers": {},
            "root": {
                "level": "DEBUG",
                "handlers": ["default"],
            },
        }
    )

    def catch_exceptions(t, val, tb):
        global should_quit
        should_quit = True
        old_hook(t, val, tb)

    def catch_exceptions_async(loop, context):
        if "future" in context:
            future: asyncio.Future = context["future"]
            logging.exception(context["message"], exc_info=future.exception())
        else:
            logging.critical(str(context))

    sys.excepthook = catch_exceptions
    loop.set_exception_handler(catch_exceptions_async)

    if args.nintendont is not None:
        connector_builder = NintendontConnectorBuilder(args.nintendont)
    else:
        connector_builder = DolphinConnectorBuilder()

    with loop:
        try:
            asyncio.get_event_loop().run_until_complete(worker(connector_builder))
        finally:
            app.quit()


if __name__ == "__main__":
    main()
