import json
import logging
import os
import platform
import string
from pathlib import Path
from typing import Optional, Iterator, Callable

from PySide6 import QtGui, QtWidgets

from randovania.exporter.game_exporter import GameExportParams
from randovania.games.dread.exporter.game_exporter import DreadGameExportParams, DreadModPlatform
from randovania.games.dread.exporter.options import DreadPerGameOptions
from randovania.games.dread.gui.dialog.ftp_uploader import FtpUploader
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import (
    GameExportDialog, prompt_for_output_directory, prompt_for_input_directory,
    is_directory_validator, path_in_edit, spoiler_path_for_directory, update_validation
)
from randovania.gui.generated.dread_game_export_dialog_ui import Ui_DreadGameExportDialog
from randovania.gui.lib import common_qt_lib
from randovania.interface_common.options import Options


def get_path_to_ryujinx() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ["APPDATA"], "Ryujinx", "mods", "contents", "010093801237c000")

    raise ValueError("Unsupported platform")


def supports_ryujinx() -> bool:
    return platform.system() in {"Windows"}


def serialize_path(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    return str(path)


def decode_path(s: Optional[str]) -> Optional[Path]:
    if s is None:
        return None
    return Path(s)


def get_windows_drives() -> Iterator[tuple[str, str, Path]]:
    from ctypes import windll

    drive_types = [
        'Not identified', 'Not Mounted', 'Removable', 'HDD', 'Network',
        'CD-Rom', 'Ramdisk',
    ]

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    for drive in drives:
        path = Path(f"{drive}:/")
        type_index = windll.kernel32.GetDriveTypeW(str(path))
        yield drive, drive_types[type_index], path


def add_validation(edit: QtWidgets.QLineEdit, validation: Callable[[], bool], post_validation: Callable[[], None]):
    def field_validation():
        common_qt_lib.set_error_border_stylesheet(edit, not validation())
        post_validation()

    common_qt_lib.set_error_border_stylesheet(edit, False)
    edit.field_validation = field_validation
    edit.textChanged.connect(field_validation)


class DreadGameExportDialog(GameExportDialog, Ui_DreadGameExportDialog):
    @property
    def _game(self):
        return RandovaniaGame.METROID_DREAD

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        per_game = options.options_for_game(self._game)
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

        # Small Size
        self.exlaunch_check.setChecked(per_game.reduce_mod_size)

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
        add_validation(self.ftp_username_edit,
                       lambda: self.ftp_anonymous_check.isChecked() or self.ftp_username_edit.text(),
                       self.update_accept_validation)
        add_validation(self.ftp_password_edit,
                       lambda: self.ftp_anonymous_check.isChecked() or self.ftp_password_edit.text(),
                       self.update_accept_validation)
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
        self.update_ryujinx_ui()
        self.tab_ryujinx.serialize_options = lambda: {}
        self.tab_ryujinx.restore_options = lambda p: None
        self.tab_ryujinx.is_valid = lambda: True

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

    def save_options(self):
        with self._options as options:
            if self._has_spoiler:
                options.auto_save_spoiler = self.auto_save_spoiler

            per_game = options.options_for_game(self._game)

            selected_tab = self.output_tab_widget.currentWidget()
            output_preference = json.dumps({
                "selected_tab": next(tab_name for tab_name, the_tab in self._output_tab_by_name.items()
                                     if selected_tab == the_tab),
                "tab_options": {
                    tab_name: the_tab.serialize_options()
                    for tab_name, the_tab in self._output_tab_by_name.items()
                }
            })

            options.set_options_for_game(self._game, DreadPerGameOptions(
                cosmetic_patches=per_game.cosmetic_patches,
                input_directory=self.input_file,
                target_platform=self.target_platform,
                reduce_mod_size=self.exlaunch_check.isChecked(),
                output_preference=output_preference,
            ))

    # Update

    def _on_update_target_platform(self):
        target_platform = self.target_platform
        self.exlaunch_check.setVisible(target_platform == DreadModPlatform.ATMOSPHERE)

        self.output_tab_widget.setTabVisible(
            self.output_tab_widget.indexOf(self.tab_sd_card),
            target_platform == DreadModPlatform.ATMOSPHERE and platform.system() == "Windows"
        )
        self.output_tab_widget.setTabVisible(
            self.output_tab_widget.indexOf(self.tab_ftp),
            target_platform == DreadModPlatform.ATMOSPHERE
        )
        self.output_tab_widget.setTabVisible(
            self.output_tab_widget.indexOf(self.tab_ryujinx),
            target_platform == DreadModPlatform.RYUJINX and supports_ryujinx()
        )

        visible_tabs = [
            i
            for i in range(self.output_tab_widget.count())
            if self.output_tab_widget.isTabVisible(i)
        ]
        if self.output_tab_widget.indexOf(self.tab_sd_card) in visible_tabs:
            self.refresh_drive_list()

        self.output_tab_widget.setCurrentIndex(visible_tabs[0])

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

    # Input file

    def _validate_input_file(self):
        common_qt_lib.set_error_border_stylesheet(self.input_file_edit, is_directory_validator(self.input_file_edit))

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
            if type_name == 'Removable' or self.sd_non_removable.isChecked():
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
            self.ryujinx_label.setText(self.ryujinx_label.text().format(
                mod_path=get_path_to_ryujinx(),
            ))

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
        return not any(x.has_error for x in [self.ftp_username_edit, self.ftp_password_edit,
                                             self.ftp_ip_edit])

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
        common_qt_lib.set_error_border_stylesheet(self.custom_path_edit, is_directory_validator(self.custom_path_edit))

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
        self.accept_button.setEnabled(hasattr(tab, "is_valid")
                                      and tab.is_valid()
                                      and not self.input_file_edit.has_error)

    def get_game_export_params(self) -> GameExportParams:
        clean_output_path = False
        output_tab = self.output_tab_widget.currentWidget()
        if output_tab is self.tab_custom_path:
            output_path = path_in_edit(self.custom_path_edit)
            post_export = None

        elif output_tab is self.tab_ryujinx:
            output_path = get_path_to_ryujinx()
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
            use_exlaunch=self.exlaunch_check.isChecked() and self.target_platform == DreadModPlatform.ATMOSPHERE,
            clean_output_path=clean_output_path,
            post_export=post_export,
        )
