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
        logging.exception("unhandled exception", exc_info=val)
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


def catch_exceptions_async(loop, context):
    if 'future' in context:
        future: asyncio.Future = context['future']
        logger.exception(context["message"], exc_info=future.exception())
    else:
        logger.critical(str(context))


async def show_main_window(app: QtWidgets.QApplication, options, is_preview: bool):
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.interface_common.options import Options
    options = typing.cast(Options, options)
    preset_manager = PresetManager(options.presets_path)

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


async def show_tracker(app: QtWidgets.QApplication):
    from randovania.gui.auto_tracker_window import AutoTrackerWindow
    options = await _load_options()
    if options is None:
        app.exit(1)
        return

    app.tracker = AutoTrackerWindow(app.game_connection, options)
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


async def show_game_session(app: QtWidgets.QApplication, options, session_id: int):
    from randovania.gui.game_session_window import GameSessionWindow
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.interface_common.preset_manager import PresetManager

    network_client: QtNetworkClient = app.network_client

    sessions = [
        session
        for session in await network_client.get_game_session_list()
        if session.id == session_id
    ]
    if not sessions:
        app.quit()
        return
    await network_client.join_game_session(sessions[0], None)

    preset_manager = PresetManager(options.presets_path)

    app.game_session_window = await GameSessionWindow.create_and_update(
        network_client,
        app.game_connection,
        preset_manager,
        None,
        options
    )
    app.game_session_window.show()


async def display_window_for(app, options, command: str, args):
    if command == "tracker":
        await show_tracker(app)
    elif command == "main":
        await show_main_window(app, options, args.preview)
    elif command == "game":
        show_game_details(app, options, args.rdvgame)
    elif command == "session":
        await show_game_session(app, options, args.session_id)
    else:
        raise RuntimeError(f"Unknown command: {command}")


def create_memory_executor(debug_game_backend: bool, options):
    from randovania.interface_common.options import Options
    options = typing.cast(Options, options)

    logger.info("Preparing game backend...")
    if debug_game_backend:
        from randovania.gui.debug_backend_window import DebugExecutorWindow
        backend = DebugExecutorWindow()
        backend.show()
    else:
        try:
            from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
        except ImportError as e:
            from randovania.gui.lib import common_qt_lib
            import traceback
            common_qt_lib.show_install_visual_cpp_redist("{}\n\nTraceback:\n{}".format(
                e,
                "\n".join(traceback.format_tb(e.__traceback__)))
            )
            raise SystemExit(1)

        from randovania.game_connection.executor.nintendont_executor import NintendontExecutor
        from randovania.game_connection.memory_executor_choice import MemoryExecutorChoice

        logger.info("Loaded all game backends...")
        if options.game_backend == MemoryExecutorChoice.NINTENDONT and options.nintendont_ip is not None:
            backend = NintendontExecutor(options.nintendont_ip)
        else:
            backend = DolphinExecutor()

    logger.info("Game backend configured: %s", type(backend))
    return backend


async def _load_options():
    logger.info("Loading up user preferences code...")
    from randovania.interface_common.options import Options
    from randovania.gui.lib import startup_tools, theme

    logger.info("Restoring saved user preferences...")
    options = Options.with_default_data_dir()
    if not await startup_tools.load_options_from_disk(options):
        return None

    logger.info("Creating user preferences folder")
    import dulwich.repo
    import dulwich.errors
    try:
        dulwich.repo.Repo(options.user_dir)

    except (dulwich.errors.NotGitRepository, ValueError):
        options.user_dir.mkdir(parents=True, exist_ok=True)
        dulwich.repo.Repo.init(options.user_dir)

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
    import qasync
    loop: asyncio.AbstractEventLoop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    sys.excepthook = catch_exceptions
    loop.set_exception_handler(catch_exceptions_async)
    return loop


async def qt_main(app: QtWidgets.QApplication, data_dir: Path, args):
    app.setQuitOnLastWindowClosed(False)
    app.network_client = None
    logging.info("Loading server client...")
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    logging.info("Configuring server client...")
    app.network_client = QtNetworkClient(data_dir)
    logging.info("Server client ready.")

    if args.login_as_guest:
        logging.info("Logging as %s", args.login_as_guest)
        await app.network_client.login_as_guest(args.login_as_guest)

    options = await _load_options()
    if options is None:
        app.exit(1)
        return

    executor = create_memory_executor(args.debug_game_backend, options)

    logging.info("Configuring game connection with the backend...")
    from randovania.game_connection.game_connection import GameConnection
    app.game_connection = GameConnection(executor)

    logging.info("Configuring qasync...")
    import qasync

    @qasync.asyncClose
    async def _on_last_window_closed():
        await app.network_client.disconnect_from_server()
        await app.game_connection.stop()
        logger.info("Last QT window closed")

    app.setQuitOnLastWindowClosed(True)
    app.lastWindowClosed.connect(_on_last_window_closed, QtCore.Qt.QueuedConnection)

    await asyncio.gather(app.game_connection.start(),
                         display_window_for(app, options, args.command, args))


def run(args):
    locale.setlocale(locale.LC_ALL, "")  # use system's default locale
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    data_dir = args.custom_network_storage
    if data_dir is None:
        from randovania.interface_common import persistence
        data_dir = persistence.local_data_dir()

    is_preview = args.preview
    start_logger(data_dir, is_preview)
    app = QtWidgets.QApplication(sys.argv)

    def main_done(done: asyncio.Task):
        e: typing.Optional[Exception] = done.exception()
        if e is not None:
            display_exception(e)
            app.exit(1)

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
    parser.add_argument("--login-as-guest", type=str, help="Login as the given quest user")
    parser.add_argument("--debug-game-backend", action="store_true", help="Opens the debug game backend.")

    gui_parsers = parser.add_subparsers(dest="command")
    gui_parsers.add_parser("main", help="Displays the Main Window").set_defaults(func=run)
    gui_parsers.add_parser("tracker", help="Opens only the auto tracker").set_defaults(func=run)

    game_parser = gui_parsers.add_parser("game", help="Opens an rdvgame")
    game_parser.add_argument("rdvgame", type=Path, help="Path ")
    game_parser.set_defaults(func=run)

    session_parser = gui_parsers.add_parser("session", help="Connects to a game session")
    session_parser.add_argument("session_id", type=int, help="Id of the session")
    session_parser.set_defaults(func=run)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
