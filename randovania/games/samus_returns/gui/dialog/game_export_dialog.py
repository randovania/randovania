from __future__ import annotations

import json
import logging
import os
import platform
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets

from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.exporter.game_exporter import MSRGameExportParams, MSRGameVersion, MSRModPlatform
from randovania.games.samus_returns.exporter.options import MSRPerGameOptions
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
from randovania.gui.generated.msr_game_export_dialog_ui import Ui_MSRGameExportDialog
from randovania.gui.lib import common_qt_lib
from randovania.lib.ftp_uploader import FtpUploader
from randovania.lib.windows_drives import get_windows_drives

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.exporter.game_exporter import GameExportParams
    from randovania.interface_common.options import Options, PerGameOptions


def get_title_id(version: MSRGameVersion) -> str:
    if version == MSRGameVersion.NTSC:
        return "00040000001BB200"
    else:
        return "00040000001BFB00"


def get_path_to_citra(version: MSRGameVersion) -> Path:
    id = get_title_id(version)
    if platform.system() == "Windows":
        return Path(os.environ["APPDATA"], "Citra", "load", "mods", id)

    raise ValueError("Unsupported platform")


def supports_citra() -> bool:
    return platform.system() in {"Windows"}


def serialize_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(path)


def decode_path(s: str | None) -> Path | None:
    if s is None:
        return None
    return Path(s)


def add_validation(
    edit: QtWidgets.QLineEdit, validation: Callable[[], bool], post_validation: Callable[[], None]
) -> None:
    def field_validation() -> None:
        common_qt_lib.set_error_border_stylesheet(edit, not validation())
        post_validation()

    common_qt_lib.set_error_border_stylesheet(edit, False)
    edit.textChanged.connect(field_validation)


def romfs_validation(line: QtWidgets.QLineEdit) -> bool:
    if is_directory_validator(line):
        return True

    path = Path(line.text())
    return not all(
        p.is_file()
        for p in [
            path.joinpath("system", "files.toc"),
            path.joinpath("packs", "system", "system_discardables.pkg"),
            path.joinpath("packs", "maps", "s000_surface", "s000_surface.pkg"),
            path.joinpath("packs", "maps", "s010_area1", "s010_area1.pkg"),
        ]
    )


#
class MSRGameExportDialog(GameExportDialog, Ui_MSRGameExportDialog):
    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_SAMUS_RETURNS

    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)

        per_game = options.options_for_game(self.game_enum())
        assert isinstance(per_game, MSRPerGameOptions)

        self._validate_input_file()
        self._validate_custom_path()

        # Input
        self.input_file_edit.textChanged.connect(self._on_input_file_change)
        self.input_file_button.clicked.connect(self._on_input_file_button)

        # Target Platform
        if per_game.target_platform == MSRModPlatform.LUMA:
            self.luma_radio.setChecked(True)
        else:
            self.citra_radio.setChecked(True)

        self.luma_radio.toggled.connect(self._on_update_target_platform)
        self.citra_radio.toggled.connect(self._on_update_target_platform)
        self._on_update_target_platform()

        # Output to SD
        self.sd_non_removable.clicked.connect(self.refresh_drive_list)
        self.sd_refresh_button.clicked.connect(self.refresh_drive_list)
        self.tab_sd_card.serialize_options = lambda: {
            "drive": serialize_path(self.sd_combo.currentData()),
            "non_removable": self.sd_non_removable.isChecked(),
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

        # Output to Citra
        self._citra_label_placeholder = self.citra_label.text()
        self.update_citra_ui()
        self.tab_citra.serialize_options = dict
        self.tab_citra.restore_options = lambda p: None
        self.tab_citra.is_valid = lambda: True

        if per_game.target_version == MSRGameVersion.NTSC:
            self.ntsc_radio.setChecked(True)
        else:
            self.pal_radio.setChecked(True)
        self.ntsc_radio.toggled.connect(self.update_citra_ui)
        self.pal_radio.toggled.connect(self.update_citra_ui)

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
            "citra": self.tab_citra,
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

    def update_per_game_options(self, per_game: PerGameOptions) -> MSRPerGameOptions:
        assert isinstance(per_game, MSRPerGameOptions)
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

        return MSRPerGameOptions(
            cosmetic_patches=per_game.cosmetic_patches,
            input_directory=self.input_file,
            target_platform=self.target_platform,
            target_version=self.target_version,
            output_preference=output_preference,
        )

    # Update

    def _on_update_target_platform(self) -> None:
        target_platform = self.target_platform

        self.output_tab_widget.setTabVisible(
            self.output_tab_widget.indexOf(self.tab_sd_card),
            target_platform == MSRModPlatform.LUMA and platform.system() == "Windows",
        )
        self.output_tab_widget.setTabVisible(
            self.output_tab_widget.indexOf(self.tab_ftp), target_platform == MSRModPlatform.LUMA
        )
        self.output_tab_widget.setTabVisible(
            self.output_tab_widget.indexOf(self.tab_citra),
            target_platform == MSRModPlatform.CITRA and supports_citra(),
        )

        visible_tabs = [i for i in range(self.output_tab_widget.count()) if self.output_tab_widget.isTabVisible(i)]
        if self.output_tab_widget.indexOf(self.tab_sd_card) in visible_tabs:
            self.refresh_drive_list()

        self.output_tab_widget.setCurrentIndex(visible_tabs[0])

    # Getters
    @property
    def input_file(self) -> Path | None:
        return path_in_edit(self.input_file_edit)

    @property
    def auto_save_spoiler(self) -> bool:
        return self.auto_save_spoiler_check.isChecked()

    @property
    def target_platform(self) -> MSRModPlatform:
        if self.luma_radio.isChecked():
            return MSRModPlatform.LUMA
        else:
            return MSRModPlatform.CITRA

    @property
    def target_version(self) -> MSRGameVersion:
        if self.ntsc_radio.isChecked():
            return MSRGameVersion.NTSC
        else:
            return MSRGameVersion.PAL

    # Input file

    def _validate_input_file(self) -> None:
        common_qt_lib.set_error_border_stylesheet(self.input_file_edit, romfs_validation(self.input_file_edit))

    def _on_input_file_change(self) -> None:
        self._validate_input_file()
        self.update_accept_validation()

    def _on_input_file_button(self) -> None:
        input_file = prompt_for_input_directory(self, self.input_file_edit)
        if input_file is not None:
            self.input_file_edit.setText(str(input_file.absolute()))

    # SD Card
    def get_sd_card_output_path(self) -> Path:
        root_path: Path = self.sd_combo.currentData()
        return root_path.joinpath("luma", "titles", get_title_id(self.target_version))

    def refresh_drive_list(self) -> None:
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

    def sd_restore_options(self, options: dict) -> None:
        self.sd_non_removable.setChecked(options["non_removable"])
        self.refresh_drive_list()

        drive_path = decode_path(options["drive"])
        for item_index in range(self.sd_combo.count()):
            if self.sd_combo.itemData(item_index) == drive_path:
                self.sd_combo.setCurrentIndex(item_index)
                break

    # Citra
    def update_citra_ui(self) -> None:
        if supports_citra():
            self.citra_label.setText(
                self._citra_label_placeholder.format(
                    mod_path=get_path_to_citra(self.target_version),
                )
            )

    # FTP
    def ftp_on_anonymous_check(self) -> None:
        self.ftp_username_edit.setEnabled(not self.ftp_anonymous_check.isChecked())
        self.ftp_password_edit.setEnabled(not self.ftp_anonymous_check.isChecked())
        update_validation(self.ftp_username_edit)
        update_validation(self.ftp_password_edit)
        self.update_accept_validation()

    def ftp_restore_options(self, options: dict) -> None:
        self.ftp_anonymous_check.setChecked(options["anonymous"])
        self.ftp_username_edit.setText(options["username"])
        self.ftp_password_edit.setText(options["password"])
        self.ftp_ip_edit.setText(options["ip"])
        self.ftp_port_edit.setText(str(options["port"]))
        self.ftp_on_anonymous_check()

    def ftp_is_valid(self) -> bool:
        return not any(x.has_error for x in [self.ftp_username_edit, self.ftp_password_edit, self.ftp_ip_edit])

    def _get_ftp_internal_path(self) -> Path:
        return self._options.internal_copies_path.joinpath("msr", "contents")

    def get_ftp_uploader(self) -> FtpUploader:
        if self.ftp_anonymous_check.isChecked():
            auth = None
        else:
            auth = (self.ftp_username_edit.text(), self.ftp_password_edit.text())

        return FtpUploader(
            auth=auth,
            ip=self.ftp_ip_edit.text(),
            port=int(self.ftp_port_edit.text()),
            local_path=self._get_ftp_internal_path(),
            remote_path=f"/luma/titles/{get_title_id(self.target_version)}",
        )

    # Custom Path
    def _validate_custom_path(self) -> None:
        common_qt_lib.set_error_border_stylesheet(
            self.custom_path_edit,
            (
                is_directory_validator(self.custom_path_edit)
                or output_input_intersection_validator(self.custom_path_edit, self.input_file_edit)
            ),
        )

    def _on_custom_path_change(self) -> None:
        self._validate_custom_path()
        self.update_accept_validation()

    def _on_custom_path_button(self) -> None:
        output_file = prompt_for_output_directory(self, "MSRRandovania", self.custom_path_edit)
        if output_file is not None:
            self.custom_path_edit.setText(str(output_file))

    def custom_restore_options(self, options: dict) -> None:
        if options["path"] is not None:
            self.custom_path_edit.setText(options["path"])

    # Export

    def update_accept_validation(self) -> None:
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

        elif output_tab is self.tab_citra:
            output_path = get_path_to_citra(self.target_version)
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

        assert output_path is not None
        assert self.input_file is not None

        return MSRGameExportParams(
            spoiler_output=spoiler_path_for_directory(self.auto_save_spoiler, output_path),
            input_path=self.input_file,
            output_path=output_path,
            target_platform=self.target_platform,
            target_version=self.target_version,
            clean_output_path=clean_output_path,
            post_export=post_export,
        )
