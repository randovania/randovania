from __future__ import annotations

import asyncio
import locale
import logging.handlers
import os
import sys
import typing
from pathlib import Path

from PySide6 import QtCore, QtWidgets

import randovania
from randovania.games.game import RandovaniaGame
from randovania.interface_common import persistence

if typing.TYPE_CHECKING:
    import argparse
    from argparse import ArgumentParser

    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.gui.multiworld_client import MultiworldClient
    from randovania.interface_common.options import Options
    from randovania.interface_common.preset_manager import PresetManager

logger = logging.getLogger(__name__)


def display_exception(val: Exception):
    if not isinstance(val, KeyboardInterrupt):
        logging.exception("unhandled exception", exc_info=val)

        from randovania.gui.lib import error_message_box

        box = error_message_box.create_box_for_exception(val)
        box.exec_()


old_handler = None


def catch_exceptions(t, val, tb):
    display_exception(val)
    if old_handler is not None:
        return old_handler(t, val, tb)


def catch_exceptions_async(loop, context):
    if "future" in context:
        future: asyncio.Future = context["future"]
        logger.exception(context["message"], exc_info=future.exception())
    elif "exception" in context:
        logger.exception(context["message"], exc_info=context["exception"])
    else:
        logger.critical(str(context))


def _migrate_old_base_preset_uuid(preset_manager: PresetManager, options: Options):
    for uuid, preset in preset_manager.custom_presets.items():
        if options.get_parent_for_preset(uuid) is None and (parent_uuid := preset.recover_old_base_uuid()) is not None:
            options.set_parent_for_preset(uuid, parent_uuid)


async def show_main_window(
    app: QtWidgets.QApplication, options: Options, is_preview: bool, instantly_quit: bool
) -> None:
    from randovania.interface_common.preset_manager import PresetManager

    preset_manager = PresetManager(options.presets_path)

    logger.info("Loading user presets...")
    await preset_manager.load_user_presets()
    _migrate_old_base_preset_uuid(preset_manager, options)
    logger.info("Finished loading presets!")

    network_client: QtNetworkClient = app.network_client

    multiworld_client: MultiworldClient = app.multiworld_client

    async def attempt_login():
        from randovania.gui.lib import async_dialog
        from randovania.network_client.network_client import UnableToConnect

        try:
            if not await network_client.ensure_logged_in(None):
                await async_dialog.warning(None, "Login required", "Logging in is required to use dev builds.")
                return False

        except UnableToConnect as e:
            s = e.reason.replace("\n", "<br />")
            await async_dialog.warning(
                None,
                "Connection Error",
                f"<b>Unable to connect to the server:</b><br /><br />{s}<br /><br />"
                f"Logging in is required to use dev builds.",
            )
            return False

        return True

    if randovania.is_frozen() and randovania.is_dev_version():
        try:
            logger.info("Disabling quit on last window closed")
            app.setQuitOnLastWindowClosed(False)
            if not await attempt_login():
                app.quit()
                return
        finally:

            def reset_last_window_quit():
                logger.info("Re-enabling quit on last window closed")
                app.setQuitOnLastWindowClosed(True)

            QtCore.QTimer.singleShot(1000, reset_last_window_quit)

    from randovania.gui.main_window import MainWindow

    logger.info("Preparing main window...")
    main_window = MainWindow(options, preset_manager, network_client, multiworld_client, is_preview)
    app.main_window = main_window

    if instantly_quit:

        def quit_after() -> None:
            main_window.close()
            app.exit(0)

        main_window.InitPostShowCompleteSignal.connect(quit_after)

    logger.info("Displaying main window")
    main_window.show()
    await main_window.request_new_data()


async def show_tracker(app: QtWidgets.QApplication, options):
    from randovania.gui.auto_tracker_window import AutoTrackerWindow

    app.tracker = AutoTrackerWindow(app.game_connection, None, options)
    logger.info("Displaying auto tracker")
    app.tracker.show()


def show_data_editor(app: QtWidgets.QApplication, options, game: RandovaniaGame):
    from randovania.gui import data_editor

    data_editor.SHOW_REGION_MIN_MAX_SPINNER = True
    app.data_editor = data_editor.DataEditorWindow.open_internal_data(game, True)
    app.data_editor.show()


async def show_game_details(app: QtWidgets.QApplication, options, file_path: Path):
    from randovania.gui.game_details.game_details_window import GameDetailsWindow
    from randovania.gui.lib import layout_loader

    layout = await layout_loader.load_layout_description(None, file_path)
    if layout is None:
        return

    details_window = GameDetailsWindow(None, options)
    details_window.update_layout_description(layout)
    logger.info("Displaying game details")
    details_window.show()
    app.details_window = details_window


async def display_window_for(app: QtWidgets.QApplication, options: Options, command: str, args):
    if command == "tracker":
        await show_tracker(app, options)
    elif command == "main":
        await show_main_window(app, options, args.preview, args.instantly_quit)
    elif command == "data_editor":
        show_data_editor(app, options, RandovaniaGame(args.game))
    elif command == "game":
        await show_game_details(app, options, args.rdvgame)
    else:
        raise RuntimeError(f"Unknown command: {command}")


def abs_path_for_args(path: str):
    return Path(path).resolve()


def add_options_cli_args(parser: ArgumentParser):
    parser.add_argument(
        "--local-data",
        type=abs_path_for_args,
        default=persistence.local_data_dir(),
        help="Selects the local data path. This is used to store preferences and temporary copies of huge files.",
    )
    parser.add_argument(
        "--user-data",
        type=abs_path_for_args,
        default=persistence.roaming_data_dir(),
        help="Selects the user data path. This is used to store your presets.",
    )


async def _load_options(args: argparse.Namespace) -> Options | None:
    logger.info("Loading up user preferences code...")
    from randovania.gui.lib import startup_tools, theme
    from randovania.interface_common.options import Options

    logger.info("Restoring saved user preferences...")
    options = Options(args.local_data, args.user_data)
    if not await startup_tools.load_options_from_disk(options):
        return None

    logger.info("Creating user preferences folder")
    import dulwich.errors
    import dulwich.repo

    try:
        dulwich.repo.Repo(os.fspath(options.user_dir))

    except (dulwich.errors.NotGitRepository, ValueError):
        options.user_dir.mkdir(parents=True, exist_ok=True)
        dulwich.repo.Repo.init(os.fspath(options.user_dir))

    theme.set_dark_theme(options.dark_mode)
    logger.info("Loaded user preferences")

    return options


def start_logger(data_dir: Path, is_preview: bool) -> None:
    # Ensure the log dir exists early on
    log_dir = data_dir.joinpath("logs", randovania.VERSION)
    log_dir.mkdir(parents=True, exist_ok=True)

    randovania.setup_logging("DEBUG" if is_preview else "INFO", log_dir.joinpath("logger.log"))


def create_loop(app: QtWidgets.QApplication) -> asyncio.AbstractEventLoop:
    os.environ["QT_API"] = "PySide6"
    import qasync

    loop: asyncio.AbstractEventLoop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    global old_handler
    old_handler = sys.excepthook
    sys.excepthook = catch_exceptions
    loop.set_exception_handler(catch_exceptions_async)

    return loop


async def qt_main(app: QtWidgets.QApplication, args: argparse.Namespace) -> None:
    app.setQuitOnLastWindowClosed(False)

    options = await _load_options(args)
    if options is None:
        app.exit(1)
        return

    import randovania

    if options.allow_crash_reporting or randovania.is_dev_version():
        import randovania.monitoring

        randovania.monitoring.client_init()

    app.network_client = None
    logging.info("Loading server client...")
    from randovania.gui.lib.qt_network_client import QtNetworkClient

    app.network_client = QtNetworkClient(options.data_dir)
    app.network_client.allow_reporting_username = options.use_user_for_crash_reporting
    logging.info("Server client ready.")

    if args.login_as_guest:
        logging.info("Logging as %s", args.login_as_guest)
        await app.network_client.login_as_guest(args.login_as_guest)

    logging.info("Creating the world database")
    from randovania.interface_common.world_database import WorldDatabase

    app.world_database = WorldDatabase(app.network_client.server_data_path.joinpath("multiworld_games"))
    await app.world_database.load_existing_data()

    logging.info("Creating the global game connection")
    from randovania.game_connection.game_connection import GameConnection

    app.game_connection = GameConnection(options, app.world_database)

    logging.info("Creating the global multiworld client")
    from randovania.gui.multiworld_client import MultiworldClient

    app.multiworld_client = MultiworldClient(app.network_client, app.game_connection, app.world_database)
    await app.multiworld_client.start()

    logging.info("Configuring qasync...")
    import qasync

    @qasync.asyncClose
    async def _on_last_window_closed():
        if app.quitOnLastWindowClosed():
            await app.network_client.disconnect_from_server()
            await app.game_connection.stop()
            logger.info("Last QT window closed")
        else:
            logger.warning("Last Qt window closed, but currently not doing anything")

    app.setQuitOnLastWindowClosed(True)
    app.lastWindowClosed.connect(_on_last_window_closed, QtCore.Qt.ConnectionType.QueuedConnection)

    await asyncio.gather(app.game_connection.start(), display_window_for(app, options, args.command, args))


def _on_application_state_changed(new_state: QtCore.Qt.ApplicationState) -> None:
    logger.debug("New application state: %s", new_state)
    import sentry_sdk

    if new_state == QtCore.Qt.ApplicationState.ApplicationActive:
        sentry_sdk.Hub.current.start_session(session_mode="application")
    elif new_state == QtCore.Qt.ApplicationState.ApplicationInactive:
        sentry_sdk.Hub.current.end_session()


def run(args: argparse.Namespace) -> None:
    locale.setlocale(locale.LC_ALL, "")  # use system's default locale
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    is_preview = args.preview
    start_logger(args.local_data, is_preview)

    app = QtWidgets.QApplication(sys.argv)
    app.applicationStateChanged.connect(_on_application_state_changed)

    def main_done(done: asyncio.Task):
        e: Exception | None = done.exception()
        if e is not None:
            display_exception(e)
            app.exit(1)

    loop = create_loop(app)
    with loop:
        loop.create_task(qt_main(app, args)).add_done_callback(main_done)
        loop.run_forever()


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser("gui", help="Run the Graphical User Interface")
    parser.add_argument("--preview", action="store_true", help="Activates preview features")
    parser.add_argument("--login-as-guest", type=str, help="Login as the given quest user")
    add_options_cli_args(parser)

    gui_parsers = parser.add_subparsers(dest="command")
    main_parser = gui_parsers.add_parser("main", help="Displays the Main Window")
    main_parser.add_argument("--instantly-quit", action="store_true", help="Quits the app instantly after it starts.")
    main_parser.set_defaults(func=run)
    gui_parsers.add_parser("tracker", help="Opens only the auto tracker").set_defaults(func=run)

    editor_parser = gui_parsers.add_parser("data_editor", help="Opens a data editor for the given game")
    editor_parser.add_argument("--game", required=True, choices=[game.value for game in RandovaniaGame])
    editor_parser.set_defaults(func=run)

    game_parser = gui_parsers.add_parser("game", help="Opens an rdvgame")
    game_parser.add_argument("rdvgame", type=Path, help="Path ")
    game_parser.set_defaults(func=run)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
