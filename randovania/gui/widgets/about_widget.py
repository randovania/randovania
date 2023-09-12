from __future__ import annotations

from PySide6 import QtGui, QtWidgets

from randovania import get_readme_section


class AboutWidget(QtWidgets.QTextBrowser):
    _first_show: bool = True

    def _on_first_show(self):
        self.setup_about_text()

    def showEvent(self, arg: QtGui.QShowEvent) -> None:
        if self._first_show:
            self._first_show = False
            self._on_first_show()

        return super().showEvent(arg)

    def setup_about_text(self):
        ABOUT_TEXT = "\n".join(
            [
                "# Randovania",
                "",
                "<https://github.com/randovania/randovania>",
                "",
                "This software is covered by the"
                " [GNU General Public License v3 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.en.html)",
                "",
                "{community}",
                "",
                "{credits}",
            ]
        )

        about_document = self.document()

        # Populate from README.md
        community = get_readme_section("COMMUNITY")
        credit = get_readme_section("CREDITS")
        about_document.setMarkdown(ABOUT_TEXT.format(community=community, credits=credit))

        # Remove all hardcoded link color
        about_document.setHtml(about_document.toHtml().replace("color:#0000ff;", ""))
        # Set links to open in a browser
        self.setOpenExternalLinks(True)

        # FIXME: For some reason, changing the cursor shape does not work here, as that changes the cursor of the
        # scrollbar only.
        # self.setCursor(QtCore.Qt.CursorShape.IBeamCursor)
        self.setStyleSheet("border: none;")

        cursor = self.textCursor()
        cursor.setPosition(0)
        self.setTextCursor(cursor)
