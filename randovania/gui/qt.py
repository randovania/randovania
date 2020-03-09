import asyncio
import os
import sys
from argparse import ArgumentParser

from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QMessageBox, QWidget

from randovania.interface_common.options import Options, DecodeFailedException
from randovania.interface_common.preset_manager import PresetManager, InvalidPreset
from randovania.layout.preset import Preset


def catch_exceptions(t, val, tb):
    QMessageBox.critical(None,
                         "An exception was raised",
                         "An unhandled Exception occurred:\n{}".format(val))
    old_hook(t, val, tb)


old_hook = sys.excepthook


def load_options_from_disk(options: Options) -> bool:
    parent: QWidget = None
    try:
        options.load_from_disk()
        return True

    except DecodeFailedException as decode_failed:
        user_response = QMessageBox.critical(
            parent,
            "Error loading previous settings",
            ("The following error occurred while restoring your settings:\n"
             "{}\n\n"
             "Do you want to reset this part of your settings?").format(decode_failed),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if user_response == QMessageBox.Yes:
            options.load_from_disk(True)
            return True
        else:
            return False


def load_user_presets(preset_manager: PresetManager) -> bool:
    parent: QWidget = None
    try:
        preset_manager.load_user_presets(False)
        return True

    except InvalidPreset as invalid_file:
        user_response = QMessageBox.critical(
            parent,
            "Error loading saved preset",
            ("An error happened when loading the preset '{}'.\n\n"
             "Do you want to delete this preset? Say No to ignore all invalid presets in this session."
             ).format(invalid_file.file.stem),
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )
        if user_response == QMessageBox.Yes:
            os.remove(invalid_file.file)
            return load_user_presets(preset_manager)
        elif user_response == QMessageBox.No:
            preset_manager.load_user_presets(True)
            return True
        else:
            return False


def show_main_window(app: QApplication, args):
    options = Options.with_default_data_dir()
    preset_manager = PresetManager(options.data_dir)

    for old_preset in options.data_dir.joinpath("presets").glob("*.randovania_preset"):
        old_preset.rename(old_preset.with_name(f"{old_preset.stem}.{Preset.file_extension()}"))

    if not load_options_from_disk(options):
        raise SystemExit(1)

    if not load_user_presets(preset_manager):
        raise SystemExit(2)

    from randovania.gui.main_window import MainWindow
    main_window = MainWindow(options, preset_manager, getattr(args, "preview", False))
    app.main_window = main_window
    main_window.show()
    main_window.request_new_data()


def show_data_editor(app: QApplication, args):
    from randovania.games.prime import default_data
    from randovania.gui.data_editor import DataEditorWindow

    app.data_visualizer = DataEditorWindow(default_data.decode_default_prime2(), True)
    app.data_visualizer.show()


def show_tracker(app: QApplication, args):
    from randovania.gui.tracker_window import TrackerWindow

    options = Options.with_default_data_dir()
    if not load_options_from_disk(options):
        raise SystemExit(1)

    app.tracker = TrackerWindow(options.tracker_files_path, options.selected_preset.layout_configuration)
    app.tracker.show()


def run(args):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)

    os.environ['QT_API'] = "PySide2"
    import asyncqt
    loop = asyncqt.QEventLoop(app)
    asyncio.set_event_loop(loop)

    sys.excepthook = catch_exceptions

    target_window = getattr(args, "window", None)
    if target_window == "data-editor":
        show_data_editor(app, args)
    elif target_window == "tracker":
        show_tracker(app, args)
    else:
        show_main_window(app, args)

    with loop:
        sys.exit(loop.run_forever())


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "gui",
        help="Run the Graphical User Interface"
    )
    parser.add_argument("--preview", action="store_true", help="Activates preview features")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--data-editor", action="store_const", dest="window", const="data-editor",
                       help="Opens only data editor window")
    group.add_argument("--tracker", action="store_const", dest="window", const="tracker",
                       help="Opens only the tracker window")
    parser.set_defaults(func=run)
