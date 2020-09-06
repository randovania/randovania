import asyncio
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QMessageBox
from asyncqt import asyncClose


def catch_exceptions(t, val, tb):
    if not isinstance(val, KeyboardInterrupt):
        QMessageBox.critical(None,
                             "An exception was raised",
                             "An unhandled Exception occurred:\n{}".format(val))
    old_hook(t, val, tb)


old_hook = sys.excepthook


def show_main_window(app: QApplication, is_preview: bool):
    from randovania.interface_common.options import Options
    from randovania.gui.lib import startup_tools
    from randovania.layout.preset import Preset

    options = Options.with_default_data_dir()

    for old_preset in options.data_dir.joinpath("presets").glob("*.randovania_preset"):
        old_preset.rename(old_preset.with_name(f"{old_preset.stem}.{Preset.file_extension()}"))

    if not startup_tools.load_options_from_disk(options):
        raise SystemExit(1)

    from randovania.interface_common.preset_manager import PresetManager
    preset_manager = PresetManager(options.data_dir)

    if not startup_tools.load_user_presets(preset_manager):
        raise SystemExit(2)

    from randovania.gui.main_window import MainWindow
    main_window = MainWindow(options, preset_manager, app.network_client, is_preview)
    app.main_window = main_window
    main_window.show()
    main_window.request_new_data()


def show_tracker(app: QApplication):
    from randovania.gui.auto_tracker_window import AutoTrackerWindow

    app.tracker = AutoTrackerWindow(app.game_connection)
    app.tracker.show()


def show_game_details(app: QApplication, game: Path):
    from randovania.layout.layout_description import LayoutDescription
    from randovania.gui.seed_details_window import SeedDetailsWindow
    from randovania.interface_common.options import Options
    from randovania.gui.lib import startup_tools

    options = Options.with_default_data_dir()
    if not startup_tools.load_options_from_disk(options):
        raise SystemExit(1)

    layout = LayoutDescription.from_file(game)
    details_window = SeedDetailsWindow(None, options)
    details_window.update_layout_description(layout)
    details_window.show()
    app.details_window = details_window


def display_window_for(app, command: str, args):
    if command == "tracker":
        show_tracker(app)
    elif command == "main":
        show_main_window(app, args.preview)
    elif command == "game":
        show_game_details(app, args.rdvgame)
    else:
        raise RuntimeError(f"Unknown command: {command}")


def create_backend(debug_game_backend: bool):
    if debug_game_backend:
        from randovania.gui.debug_backend_window import DebugBackendWindow
        backend = DebugBackendWindow()
        backend.show()
    else:
        from randovania.game_connection.dolphin_backend import DolphinBackend
        backend = DolphinBackend()
    return backend


def run(args):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    app = QApplication(sys.argv)

    os.environ['QT_API'] = "PySide2"
    import asyncqt
    loop = asyncqt.QEventLoop(app)
    asyncio.set_event_loop(loop)

    sys.excepthook = catch_exceptions

    data_dir = args.custom_network_storage
    if data_dir is None:
        from randovania.interface_common import persistence
        data_dir = persistence.user_data_dir()

    from randovania.gui.lib.qt_network_client import QtNetworkClient
    from randovania.game_connection.game_connection import GameConnection

    app.network_client = QtNetworkClient(data_dir)
    app.game_connection = GameConnection()

    backend = create_backend(args.debug_game_backend)
    app.game_connection.set_backend(backend)

    @asyncClose
    async def _on_last_window_closed():
        await app.network_client.disconnect_from_server()
        await app.game_connection.stop()

    app.lastWindowClosed.connect(_on_last_window_closed, QtCore.Qt.QueuedConnection)

    display_window_for(app, args.command, args)

    with loop:
        loop.create_task(app.game_connection.start())
        # loop.create_task(app.network_client.connect_if_authenticated())
        sys.exit(loop.run_forever())


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
