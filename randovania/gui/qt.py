from __future__ import annotations

import asyncio
import locale
import logging.handlers
import os
import sys
import typing
from argparse import ArgumentParser
from pathlib import Path

from PySide6 import QtCore, QtWidgets

import randovania
from randovania.games.game import RandovaniaGame

if typing.TYPE_CHECKING:
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.interface_common.options import Options

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
    if 'future' in context:
        future: asyncio.Future = context['future']
        logger.exception(context["message"], exc_info=future.exception())
    elif 'exception' in context:
        logger.exception(context["message"], exc_info=context['exception'])
    else:
        logger.critical(str(context))


def _migrate_old_base_preset_uuid(preset_manager: PresetManager, options: Options):
    for uuid, preset in preset_manager.custom_presets.items():
        if options.get_parent_for_preset(uuid) is None and (parent_uuid := preset.recover_old_base_uuid()) is not None:
            options.set_parent_for_preset(uuid, parent_uuid)


async def show_main_window(app: QtWidgets.QApplication, options: Options, is_preview: bool):
    from randovania.interface_common.preset_manager import PresetManager
    preset_manager = PresetManager(options.presets_path)

    logger.info("Loading user presets...")
    await preset_manager.load_user_presets()
    _migrate_old_base_preset_uuid(preset_manager, options)
    logger.info("Finished loading presets!")

    from randovania.gui.lib.qt_network_client import QtNetworkClient
    network_client: QtNetworkClient = app.network_client

    async def attempt_login():
        from randovania.network_client.network_client import UnableToConnect
        from randovania.gui.lib import async_dialog

        try:
            from randovania.gui import main_online_interaction
            if not await main_online_interaction.ensure_logged_in(None, network_client):
                await async_dialog.warning(None, "Login required",
                                           "Logging in is required to use dev builds.")
                return False

        except UnableToConnect as e:
            s = e.reason.replace('\n', '<br />')
            await async_dialog.warning(
                None, "Connection Error",
                f"<b>Unable to connect to the server:</b><br /><br />{s}<br /><br />"
                f"Logging in is required to use dev builds.")
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
    main_window = MainWindow(options, preset_manager, network_client, is_preview)
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

    app.tracker = AutoTrackerWindow(app.game_connection, None, options)
    logger.info("Displaying auto tracker")
    app.tracker.show()


def show_data_editor(app: QtWidgets.QApplication, options, game: RandovaniaGame):
    from randovania.gui import data_editor
    data_editor.SHOW_WORLD_MIN_MAX_SPINNER = True
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


async def show_game_session(app: QtWidgets.QApplication, options, session_id: int):
    from randovania.gui.game_session_window import GameSessionWindow
    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.interface_common.preset_manager import PresetManager

    network_client: QtNetworkClient = app.network_client

    sessions = [
        session
        for session in await network_client.get_game_session_list(False)
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


async def display_window_for(app: QtWidgets.QApplication, options: Options, command: str, args):
    if command == "tracker":
        await show_tracker(app)
    elif command == "main":
        await show_main_window(app, options, args.preview)
    elif command == "data_editor":
        show_data_editor(app, options, RandovaniaGame(args.game))
    elif command == "game":
        await show_game_details(app, options, args.rdvgame)
    elif command == "session":
        await show_game_session(app, options, args.session_id)
    else:
        raise RuntimeError(f"Unknown command: {command}")


async def _load_options() -> Options | None:
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
        dulwich.repo.Repo(os.fspath(options.user_dir))

    except (dulwich.errors.NotGitRepository, ValueError):
        options.user_dir.mkdir(parents=True, exist_ok=True)
        dulwich.repo.Repo.init(os.fspath(options.user_dir))

    theme.set_dark_theme(options.dark_mode)

    from randovania.layout.versioned_preset import VersionedPreset
    for old_preset in options.data_dir.joinpath("presets").glob("*.randovania_preset"):
        old_preset.rename(old_preset.with_name(f"{old_preset.stem}.{VersionedPreset.file_extension()}"))

    logger.info("Loaded user preferences")

    return options


def start_logger(data_dir: Path, is_preview: bool):
    # Ensure the log dir exists early on
    log_dir = data_dir.joinpath("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    randovania.setup_logging('DEBUG' if is_preview else 'INFO', log_dir.joinpath("logger.log"))


def create_loop(app: QtWidgets.QApplication) -> asyncio.AbstractEventLoop:
    os.environ['QT_API'] = "PySide6"
    import qasync
    loop: asyncio.AbstractEventLoop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    global old_handler
    old_handler = sys.excepthook
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

    logging.info("Configuring game connection with the backend...")
    from randovania.game_connection.game_connection import GameConnection
    app.game_connection = GameConnection(options)

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
    app.lastWindowClosed.connect(_on_last_window_closed, QtCore.Qt.QueuedConnection)

    await asyncio.gather(app.game_connection.start(),
                         display_window_for(app, options, args.command, args))


def _on_application_state_changed(new_state: QtCore.Qt.ApplicationState):
    logger.info("New application state: %s", new_state)
    import sentry_sdk
    if new_state == QtCore.Qt.ApplicationState.ApplicationActive:
        sentry_sdk.Hub.current.start_session(session_mode="application")
    elif new_state == QtCore.Qt.ApplicationState.ApplicationInactive:
        sentry_sdk.Hub.current.end_session()


def run(args):
    import randovania.monitoring
    randovania.monitoring.client_init()

    locale.setlocale(locale.LC_ALL, "")  # use system's default locale
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    data_dir = args.custom_network_storage
    if data_dir is None:
        from randovania.interface_common import persistence
        data_dir = persistence.local_data_dir()

    is_preview = args.preview
    start_logger(data_dir, is_preview)
    app = QtWidgets.QApplication(sys.argv)
    app.applicationStateChanged.connect(_on_application_state_changed)

    def main_done(done: asyncio.Task):
        e: Exception | None = done.exception()
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

    gui_parsers = parser.add_subparsers(dest="command")
    gui_parsers.add_parser("main", help="Displays the Main Window").set_defaults(func=run)
    gui_parsers.add_parser("tracker", help="Opens only the auto tracker").set_defaults(func=run)

    editor_parser = gui_parsers.add_parser("data_editor", help="Opens a data editor for the given game")
    editor_parser.add_argument("--game", required=True, choices=[game.value for game in RandovaniaGame])
    editor_parser.set_defaults(func=run)

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
