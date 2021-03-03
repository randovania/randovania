import asyncio
import locale
import logging.handlers
import os
import sys
import traceback
import typing
from argparse import ArgumentParser
from pathlib import Path

from PySide2 import QtCore, QtWidgets

import randovania

logger = logging.getLogger(__name__)


def display_exception(val: Exception):
    if not isinstance(val, KeyboardInterrupt):
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                    "An exception was raised",
                                    "An unhandled Exception occurred:\n{}".format(val),
                                    QtWidgets.QMessageBox.Ok)
        from randovania.gui.lib import common_qt_lib
        common_qt_lib.set_default_window_icon(box)
        if val.__traceback__ is not None:
            box.setDetailedText("".join(traceback.format_tb(val.__traceback__)))
        box.exec_()


def catch_exceptions(t, val, tb):
    display_exception(val)
    old_hook(t, val, tb)


old_hook = sys.excepthook


def catch_exceptions_async(loop, context):
    if 'future' in context:
        future: asyncio.Future = context['future']
        logger.exception(context["message"], exc_info=future.exception())
    else:
        logger.critical(str(context))


async def show_main_window(app: QtWidgets.QApplication, options, is_preview: bool):
    from randovania.interface_common.preset_manager import PresetManager
    preset_manager = PresetManager(options.data_dir)

    logger.info("Loading user presets...")
    await preset_manager.load_user_presets()
    logger.info("Finished loading presets!")

    from randovania.gui.main_window import MainWindow
    logger.info("Preparing main window...")
    main_window = MainWindow(options, preset_manager, app.network_client, is_preview)
    app.main_window = main_window

    logger.info("Displaying main window")
    main_window.show()
    await main_window.request_new_data()


def show_tracker(app: QtWidgets.QApplication):
    from randovania.gui.auto_tracker_window import AutoTrackerWindow

    app.tracker = AutoTrackerWindow(app.game_connection, _load_options())
    logger.info("Displaying auto tracker")
    app.tracker.show()


def show_game_details(app: QtWidgets.QApplication, options, game: Path):
    from randovania.layout.layout_description import LayoutDescription
    from randovania.gui.seed_details_window import SeedDetailsWindow

    layout = LayoutDescription.from_file(game)
    details_window = SeedDetailsWindow(None, options)
    details_window.update_layout_description(layout)
    logger.info("Displaying game details")
    details_window.show()
    app.details_window = details_window


async def display_window_for(app, options, command: str, args):
    if command == "tracker":
        show_tracker(app)
    elif command == "main":
        await show_main_window(app, options, args.preview)
    elif command == "game":
        show_game_details(app, options, args.rdvgame)
    else:
        raise RuntimeError(f"Unknown command: {command}")


def create_backend(debug_game_backend: bool, options):
    from randovania.interface_common.options import Options
    options = typing.cast(Options, options)

    logger.info("Preparing game backend...")
    if debug_game_backend:
        from randovania.gui.debug_backend_window import DebugBackendWindow
        backend = DebugBackendWindow()
        backend.show()
    else:
        try:
            from randovania.game_connection.dolphin_backend import DolphinBackend
        except ImportError:
            from randovania.gui.lib import common_qt_lib
            common_qt_lib.show_install_visual_cpp_redist()
            raise SystemExit(1)

        from randovania.game_connection.nintendont_backend import NintendontBackend
        from randovania.game_connection.backend_choice import GameBackendChoice

        logger.info("Loaded all game backends...")
        if options.game_backend == GameBackendChoice.NINTENDONT and options.nintendont_ip is not None:
            backend = NintendontBackend(options.nintendont_ip)
        else:
            backend = DolphinBackend()

    logger.info("Game backend configured: %s", type(backend))
    return backend


def _load_options():
    logger.info("Loading up user preferences code...")
    from randovania.interface_common.options import Options
    from randovania.gui.lib import startup_tools, theme

    logger.info("Restoring saved user preferences...")
    options = Options.with_default_data_dir()
    if not startup_tools.load_options_from_disk(options):
        raise SystemExit(1)

    theme.set_dark_theme(options.dark_mode)

    from randovania.layout.preset_migration import VersionedPreset
    for old_preset in options.data_dir.joinpath("presets").glob("*.randovania_preset"):
        old_preset.rename(old_preset.with_name(f"{old_preset.stem}.{VersionedPreset.file_extension()}"))

    logger.info("Loaded user preferences")

    return options


def start_logger(data_dir: Path, is_preview: bool):
    # Ensure the log dir exists early on
    log_dir = data_dir.joinpath("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    randovania.setup_logging('DEBUG' if is_preview else 'INFO', log_dir.joinpath(f"logger.log"))


def create_loop(app: QtWidgets.QApplication) -> asyncio.AbstractEventLoop:
    os.environ['QT_API'] = "PySide2"
    import asyncqt
    loop: asyncio.AbstractEventLoop = asyncqt.QEventLoop(app)
    asyncio.set_event_loop(loop)

    sys.excepthook = catch_exceptions
    loop.set_exception_handler(catch_exceptions_async)
    return loop


async def qt_main(app: QtWidgets.QApplication, data_dir: Path, args):
    app.network_client = None
    logging.info("Loading server client...")
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    logging.info("Configuring server client...")
    app.network_client = QtNetworkClient(data_dir)
    logging.info("Server client ready.")

    options = _load_options()
    backend = create_backend(args.debug_game_backend, options)

    logging.info("Configuring game connection with the backend...")
    from randovania.game_connection.game_connection import GameConnection
    app.game_connection = GameConnection(backend)

    logging.info("Configuring asyncqt...")
    import asyncqt

    @asyncqt.asyncClose
    async def _on_last_window_closed():
        await app.network_client.disconnect_from_server()
        await app.game_connection.stop()
        logger.info("Last QT window closed")

    app.lastWindowClosed.connect(_on_last_window_closed, QtCore.Qt.QueuedConnection)

    await asyncio.gather(app.game_connection.start(),
                         display_window_for(app, options, args.command, args))


def run(args):
    locale.setlocale(locale.LC_ALL, "")  # use system's default locale
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    data_dir = args.custom_network_storage
    if data_dir is None:
        from randovania.interface_common import persistence
        data_dir = persistence.user_data_dir()

    is_preview = args.preview
    start_logger(data_dir, is_preview)
    app = QtWidgets.QApplication(sys.argv)

    def main_done(done: asyncio.Task):
        e: typing.Optional[Exception] = done.exception()
        if e is not None:
            display_exception(e)

    loop = create_loop(app)
    with loop:
        loop.create_task(qt_main(app, data_dir, args)).add_done_callback(main_done)
        loop.run_forever()


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "gui",
        help="Run the Graphical User Interface"
    )
    parser.add_argument("--preview", action="store_true", help="Activates preview features")
    parser.add_argument("--custom-network-storage", type=Path, help="Use a custom path to store the network login.")
    parser.add_argument("--debug-game-backend", action="store_true", help="Opens the debug game backend.")

    gui_parsers = parser.add_subparsers(dest="command")
    gui_parsers.add_parser("main", help="Displays the Main Window").set_defaults(func=run)
    gui_parsers.add_parser("tracker", help="Opens only the auto tracker").set_defaults(func=run)

    game_parser = gui_parsers.add_parser("game", help="Opens an rdvgame")
    game_parser.add_argument("rdvgame", type=Path, help="Path ")
    game_parser.set_defaults(func=run)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
