from __future__ import annotations

import json
import logging
import platform
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from randovania.game.game_enum import RandovaniaGame
from randovania.games.dread.exporter.game_exporter import DreadGameExportParams, DreadModPlatform, LinuxRyujinxPath
from randovania.games.dread.exporter.options import DreadPerGameOptions
from randovania.games.dread.gui.generated.dread_game_export_dialog_ui import Ui_DreadGameExportDialog
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog,
    is_directory_validator,
    output_input_intersection_validator,
    path_in_edit,
    prompt_for_input_directory,
    prompt_for_output_directory,
    spoiler_path_for_directory,
    update_validation,
)
from randovania.gui.lib import common_qt_lib
from randovania.lib import windows_lib
from randovania.lib.ftp_uploader import FtpUploader
from randovania.lib.windows_lib import get_windows_drives

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.exporter.game_exporter import GameExportParams
    from randovania.interface_common.options import Options


def return_linux_only_controls() -> set[str]:
    return {"linux_flatpak_radio", "linux_native_radio"}


def supports_ryujinx() -> bool:
    return platform.system() in {"Windows", "Linux", "Darwin"}


def serialize_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(path)


def decode_path(s: str | None) -> Path | None:
    if s is None:
        return None
    return Path(s)


def add_validation(edit: QtWidgets.QLineEdit, validation: Callable[[], bool], post_validation: Callable[[], None]):
    def field_validation():
        common_qt_lib.set_error_border_stylesheet(edit, not validation())
        post_validation()

    common_qt_lib.set_error_border_stylesheet(edit, False)
    edit.field_validation = field_validation
    edit.textChanged.connect(field_validation)


def romfs_validation(line: QtWidgets.QLineEdit):
    if is_directory_validator(line):
        return True

    path = Path(line.text())
    return not (
        all(
            p.is_file()
            for p in [
                path.joinpath("config.ini"),
                path.joinpath("system", "files.toc"),
                path.joinpath("packs", "system", "system.pkg"),
                path.joinpath("packs", "maps", "s010_cave", "s010_cave.pkg"),
                path.joinpath("packs", "maps", "s020_magma", "s020_magma.pkg"),
            ]
        )
        and not all(p.is_file() for p in [path.joinpath("custom_names.json")])
    )


class DreadGameExportDialog(GameExportDialog, Ui_DreadGameExportDialog):
    def get_path_to_ryujinx(self) -> Path:
        ryujinx_path_tuple = ("Ryujinx", "mods", "contents", "010093801237c000")
        match (platform.system(), self.linux_ryujinx_path):
            case "Windows", _:
                # TODO: double check what ryujinx actually uses for windows. I don't think it reads the Appdata env var
                # but instead probably the value from QStandardPaths.
                return windows_lib.get_appdata().joinpath(*ryujinx_path_tuple)

            case "Linux", LinuxRyujinxPath.NATIVE:
                base_config_path = QtCore.QStandardPaths.writableLocation(
                    QtCore.QStandardPaths.StandardLocation.GenericConfigLocation
                )
                return Path(base_config_path, *ryujinx_path_tuple)
            case "Linux", LinuxRyujinxPath.FLATPAK:
                base_config_path = str(
                    Path(
                        QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.HomeLocation),
                        ".var",
                        "app",
                        "org.ryujinx.Ryujinx",
                        "config",
                    )
                )
                return Path(base_config_path, *ryujinx_path_tuple)

            case "Darwin", _:
                return Path(
                    QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.GenericDataLocation),
                    *ryujinx_path_tuple,
                )

        raise ValueError("Unsupported platform")

    @classmethod
    def game_enum(cls):
        return RandovaniaGame.METROID_DREAD

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        per_game = options.options_for_game(self.game_enum())
        assert isinstance(per_game, DreadPerGameOptions)

        self._validate_input_file()
        self._validate_custom_path()

        # Input
        self.input_file_edit.textChanged.connect(self._on_input_file_change)
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Target Platform
        if per_game.target_platform == DreadModPlatform.ATMOSPHERE:
            self.atmosphere_radio.setChecked(True)
        else:
            self.ryujinx_radio.setChecked(True)

        self.atmosphere_radio.toggled.connect(self._on_update_target_platform)
        self.ryujinx_radio.toggled.connect(self._on_update_target_platform)
        self._on_update_target_platform()

        # Output to SD
        self.sd_non_removable.clicked.connect(self.refresh_drive_list)
        self.sd_refresh_button.clicked.connect(self.refresh_drive_list)
        self.tab_sd_card.serialize_options = lambda: {
            "drive": serialize_path(self.sd_combo.currentData()),
            "non_removable": self.sd_non_removable.isChecked(),
            "mod_manager": self.sd_mod_manager_check.isChecked(),
        }
        self.tab_sd_card.restore_options = self.sd_restore_options
        self.tab_sd_card.is_valid = lambda: self.sd_combo.currentData() is not None

        # Output to FTP
        self.tab_ftp.is_valid = self.ftp_is_valid
        self.ftp_test_button.setVisible(False)
        self.ftp_anonymous_check.clicked.connect(self.ftp_on_anonymous_check)
        add_validation(
            self.ftp_username_edit,
            lambda: self.ftp_anonymous_check.isChecked() or self.ftp_username_edit.text(),
            self.update_accept_validation,
        )
        add_validation(
            self.ftp_password_edit,
            lambda: self.ftp_anonymous_check.isChecked() or self.ftp_password_edit.text(),
            self.update_accept_validation,
        )
        add_validation(self.ftp_ip_edit, lambda: self.ftp_ip_edit.text(), self.update_accept_validation)
        self.ftp_port_edit.setValidator(QtGui.QIntValidator(1, 65535, self))

        self.tab_ftp.serialize_options = lambda: {
            "anonymous": self.ftp_anonymous_check.isChecked(),
            "username": self.ftp_username_edit.text(),
            "password": self.ftp_password_edit.text(),
            "ip": self.ftp_ip_edit.text(),
            "port": self.ftp_port_edit.text(),
        }
        self.tab_ftp.restore_options = self.ftp_restore_options
        update_validation(self.ftp_username_edit)
        update_validation(self.ftp_ip_edit)
        self.ftp_on_anonymous_check()

        # Output to Ryujinx
        self.tab_ryujinx.serialize_options = dict
        self.tab_ryujinx.restore_options = lambda p: None
        self.tab_ryujinx.is_valid = lambda: True

        # Hide Linux Ryujinx controls on non-Linux
        is_linux = platform.system() == "Linux"
        for control_name in return_linux_only_controls():
            widget: QtWidgets.QWidget = getattr(self, control_name)
            widget.setVisible(is_linux)
        if per_game.linux_ryujinx_path == LinuxRyujinxPath.NATIVE:
            self.linux_native_radio.setChecked(True)
        else:
            self.linux_flatpak_radio.setChecked(True)
        self.old_linux_ryujinx_path = self.get_path_to_ryujinx()
        self.linux_native_radio.toggled.connect(self._on_update_linux_ryujinx_path)
        self.linux_flatpak_radio.toggled.connect(self._on_update_linux_ryujinx_path)

        self.update_ryujinx_ui()

        # Output to Custom
        self.custom_path_edit.textChanged.connect(self._on_custom_path_change)
        self.custom_path_button.clicked.connect(self._on_custom_path_button)
        self.tab_custom_path.serialize_options = lambda: {
            "path": serialize_path(path_in_edit(self.custom_path_edit)),
        }
        self.tab_custom_path.restore_options = self.custom_restore_options
        self.tab_custom_path.is_valid = lambda: not self.custom_path_edit.has_error

        self._output_tab_by_name = {
            "sd": self.tab_sd_card,
            "ftp": self.tab_ftp,
            "ryujinx": self.tab_ryujinx,
            "custom": self.tab_custom_path,
        }

        # Restore options
        if per_game.input_directory is not None:
            self.input_file_edit.setText(str(per_game.input_directory))

        if per_game.output_preference is not None:
            output_preference = json.loads(per_game.output_preference)
            tab_options = output_preference["tab_options"]

            for tab_name, the_tab in self._output_tab_by_name.items():
                if tab_name == output_preference.get("selected_tab"):
                    index = self.output_tab_widget.indexOf(the_tab)
                    if self.output_tab_widget.isTabVisible(index):
                        self.output_tab_widget.setCurrentIndex(index)

                try:
                    if tab_name in tab_options:
                        the_tab.restore_options(tab_options[tab_name])
                except Exception:
                    logging.exception("Unable to restore preferences for output")

        # Accept
        self.output_tab_widget.currentChanged.connect(self.update_accept_validation)
        self.sd_combo.currentIndexChanged.connect(self.update_accept_validation)

        self.update_accept_validation()

    def update_per_game_options(self, per_game: DreadPerGameOptions) -> DreadPerGameOptions:
        selected_tab = self.output_tab_widget.currentWidget()
        output_preference = json.dumps(
            {
                "selected_tab": next(
                    tab_name for tab_name, the_tab in self._output_tab_by_name.items() if selected_tab == the_tab
                ),
                "tab_options": {
                    tab_name: the_tab.serialize_options() for tab_name, the_tab in self._output_tab_by_name.items()
                },
            }
        )

        return DreadPerGameOptions(
            cosmetic_patches=per_game.cosmetic_patches,
            input_directory=self.input_file,
            target_platform=self.target_platform,
            linux_ryujinx_path=self.linux_ryujinx_path,
            output_preference=output_preference,
        )

    # Update

    def _on_update_target_platform(self):
        target_platform = self.target_platform

        self.output_tab_widget.setTabVisible(
            self.output_tab_widget.indexOf(self.tab_sd_card),
            target_platform == DreadModPlatform.ATMOSPHERE and platform.system() == "Windows",
        )
        self.output_tab_widget.setTabVisible(
            self.output_tab_widget.indexOf(self.tab_ftp), target_platform == DreadModPlatform.ATMOSPHERE
        )
        self.output_tab_widget.setTabVisible(
            self.output_tab_widget.indexOf(self.tab_ryujinx),
            target_platform == DreadModPlatform.RYUJINX and supports_ryujinx(),
        )

        visible_tabs = [i for i in range(self.output_tab_widget.count()) if self.output_tab_widget.isTabVisible(i)]
        if self.output_tab_widget.indexOf(self.tab_sd_card) in visible_tabs:
            self.refresh_drive_list()

        self.output_tab_widget.setCurrentIndex(visible_tabs[0])

    def _on_update_linux_ryujinx_path(self) -> None:
        self.ryujinx_label.setText(self.ryujinx_label.text().replace(str(self.old_linux_ryujinx_path), "{mod_path}"))
        self.old_linux_ryujinx_path = self.get_path_to_ryujinx()
        self.update_ryujinx_ui()

    # Getters
    @property
    def input_file(self) -> Path:
        return path_in_edit(self.input_file_edit)

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    @property
    def target_platform(self) -> DreadModPlatform:
        if self.atmosphere_radio.isChecked():
            return DreadModPlatform.ATMOSPHERE
        else:
            return DreadModPlatform.RYUJINX

    @property
    def linux_ryujinx_path(self) -> LinuxRyujinxPath:
        if self.linux_native_radio.isChecked():
            return LinuxRyujinxPath.NATIVE
        else:
            return LinuxRyujinxPath.FLATPAK

    # Input file

    def _validate_input_file(self):
        common_qt_lib.set_error_border_stylesheet(self.input_file_edit, romfs_validation(self.input_file_edit))

    def _on_input_file_change(self):
        self._validate_input_file()
        self.update_accept_validation()

    def _on_input_file_button(self):
        input_file = prompt_for_input_directory(self, self.input_file_edit)
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    # SD Card
    def get_sd_card_output_path(self) -> Path:
        root_path: Path = self.sd_combo.currentData()
        if self.sd_mod_manager_check.isChecked():
            return root_path.joinpath("mods", "Metroid Dread", f"Randovania {self._word_hash}")
        else:
            return root_path.joinpath("atmosphere")

    def refresh_drive_list(self):
        old_value = self.sd_combo.currentText()

        self.sd_combo.clear()
        for drive, type_name, path in get_windows_drives():
            if type_name == "Removable" or self.sd_non_removable.isChecked():
                self.sd_combo.addItem(f"{drive}: ({type_name})", path)

        if self.sd_combo.count() == 0:
            self.sd_combo.addItem("None found", None)
            common_qt_lib.set_error_border_stylesheet(self.sd_combo, True)
        else:
            common_qt_lib.set_error_border_stylesheet(self.sd_combo, False)

        index = self.sd_combo.findText(old_value)
        if index >= 0:
            self.sd_combo.setCurrentIndex(index)

    def sd_restore_options(self, options: dict):
        self.sd_mod_manager_check.setChecked(options["mod_manager"])

        self.sd_non_removable.setChecked(options["non_removable"])
        self.refresh_drive_list()

        drive_path = decode_path(options["drive"])
        for item_index in range(self.sd_combo.count()):
            if self.sd_combo.itemData(item_index) == drive_path:
                self.sd_combo.setCurrentIndex(item_index)
                break

    # Ryujinx
    def update_ryujinx_ui(self):
        if supports_ryujinx():
            self.ryujinx_label.setText(
                self.ryujinx_label.text().format(
                    mod_path=self.get_path_to_ryujinx(),
                )
            )

    # FTP
    def ftp_on_anonymous_check(self):
        self.ftp_username_edit.setEnabled(not self.ftp_anonymous_check.isChecked())
        self.ftp_password_edit.setEnabled(not self.ftp_anonymous_check.isChecked())
        update_validation(self.ftp_username_edit)
        update_validation(self.ftp_password_edit)
        self.update_accept_validation()

    def ftp_restore_options(self, options: dict):
        self.ftp_anonymous_check.setChecked(options["anonymous"])
        self.ftp_username_edit.setText(options["username"])
        self.ftp_password_edit.setText(options["password"])
        self.ftp_ip_edit.setText(options["ip"])
        self.ftp_port_edit.setText(str(options["port"]))
        self.ftp_on_anonymous_check()

    def ftp_is_valid(self):
        return not any(x.has_error for x in [self.ftp_username_edit, self.ftp_password_edit, self.ftp_ip_edit])

    def _get_ftp_internal_path(self):
        return self._options.internal_copies_path.joinpath("dread", "contents")

    def get_ftp_uploader(self):
        if self.ftp_anonymous_check.isChecked():
            auth = None
        else:
            auth = (self.ftp_username_edit.text(), self.ftp_password_edit.text())

        return FtpUploader(
            auth=auth,
            ip=self.ftp_ip_edit.text(),
            port=int(self.ftp_port_edit.text()),
            local_path=self._get_ftp_internal_path(),
            remote_path=f"/mods/Metroid Dread/Randovania {self._word_hash}",
        )

    # Custom Path
    def _validate_custom_path(self):
        common_qt_lib.set_error_border_stylesheet(
            self.custom_path_edit,
            (
                is_directory_validator(self.custom_path_edit)
                or output_input_intersection_validator(self.custom_path_edit, self.input_file_edit)
            ),
        )

    def _on_custom_path_change(self):
        self._validate_custom_path()
        self.update_accept_validation()

    def _on_custom_path_button(self):
        output_file = prompt_for_output_directory(self, "DreadRandovania", self.custom_path_edit)
        if output_file is not None:
            self.custom_path_edit.setText(str(output_file))

    def custom_restore_options(self, options: dict):
        if options["path"] is not None:
            self.custom_path_edit.setText(options["path"])

    # Export

    def update_accept_validation(self):
        tab = self.output_tab_widget.currentWidget()
        self.accept_button.setEnabled(
            hasattr(tab, "is_valid") and tab.is_valid() and not self.input_file_edit.has_error
        )

    def get_game_export_params(self) -> GameExportParams:
        clean_output_path = False
        output_tab = self.output_tab_widget.currentWidget()
        if output_tab is self.tab_custom_path:
            output_path = path_in_edit(self.custom_path_edit)
            post_export = None

        elif output_tab is self.tab_ryujinx:
            output_path = self.get_path_to_ryujinx()
            post_export = None

        elif output_tab is self.tab_ftp:
            output_path = self._get_ftp_internal_path()
            post_export = self.get_ftp_uploader()
            clean_output_path = True

        elif output_tab is self.tab_sd_card:
            output_path = self.get_sd_card_output_path()
            post_export = None

        else:
            raise RuntimeError(f"Unknown output_tab: {output_tab}")

        return DreadGameExportParams(
            spoiler_output=spoiler_path_for_directory(self.auto_save_spoiler, output_path),
            input_path=self.input_file,
            output_path=output_path,
            target_platform=self.target_platform,
            use_exlaunch=True,
            clean_output_path=clean_output_path,
            post_export=post_export,
        )
