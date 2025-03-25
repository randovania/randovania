from PySide6 import QtWidgets
from PySide6.QtGui import Qt

from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin


class BackgroundTaskWidget(QtWidgets.QWidget, BackgroundTaskMixin):
    """A widget with a progress label, a stop button and a progress bar"""

    can_stop_background_process: bool = True

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self.root_layout = QtWidgets.QGridLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_label = QtWidgets.QLabel(self)
        self.progress_label.setObjectName("progress_label")
        policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        policy.setHorizontalStretch(0)
        policy.setVerticalStretch(0)
        policy.setHeightForWidth(self.progress_label.sizePolicy().hasHeightForWidth())
        self.progress_label.setSizePolicy(policy)
        self.progress_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.progress_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.progress_label.setWordWrap(True)
        self.progress_label.setOpenExternalLinks(True)

        self.root_layout.addWidget(self.progress_label, 0, 0, 1, 2)

        self.background_process_button = QtWidgets.QPushButton("Stop", self)
        self.background_process_button.setEnabled(False)
        self.root_layout.addWidget(self.background_process_button, 1, 0, 1, 1)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setInvertedAppearance(False)

        self.root_layout.addWidget(self.progress_bar, 1, 1, 1, 1)

        # Connect
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.background_process_button.clicked.connect(self.background_process_button_clicked)

    def background_process_button_clicked(self) -> None:
        self.stop_background_process()

    def update_background_process_button(self) -> None:
        self.background_process_button.setEnabled(self.has_background_process and self.can_stop_background_process)
        self.background_process_button.setText("Stop")

    def enable_buttons_with_background_tasks(self, value: bool) -> None:
        self.update_background_process_button()

    def update_progress(self, message: str, percentage: int) -> None:
        self.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setRange(0, 0)
