import argparse
import asyncio
import os
import sys

from PySide2.QtCore import QCoreApplication

from randovania.game_connection.connection_base import GameConnectionStatus
from randovania.game_connection.dolphin_backend import DolphinBackend
from randovania.game_connection.game_connection import GameConnection


should_quit = False
old_hook = sys.excepthook


async def worker(app: QCoreApplication):
    connection = GameConnection(DolphinBackend())

    await connection.start()
    try:
        while connection.current_status != GameConnectionStatus.InGame:
            await asyncio.sleep(1)
            print(connection.pretty_current_status)

        await connection.display_message("Hello Samus.")
        await connection.display_message("I see you are trying to do a multiworld.")
        await connection.display_message("But are you authorized for that?")
        await asyncio.sleep(20)

    except KeyboardInterrupt:
        return

    finally:
        await connection.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.parse_args()

    app = QCoreApplication(sys.argv)

    os.environ['QT_API'] = "PySide2"
    import asyncqt
    loop = asyncqt.QEventLoop(app)
    asyncio.set_event_loop(loop)

    def catch_exceptions(t, val, tb):
        global should_quit
        should_quit = True
        old_hook(t, val, tb)

    sys.excepthook = catch_exceptions

    with loop:
        try:
            asyncio.get_event_loop().run_until_complete(worker(app))
        finally:
            app.quit()


if __name__ == '__main__':
    main()
