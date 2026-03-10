"""Main application window."""

from qtpy.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar,
)
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont

from jobwizard.wizard import SlurmJobWizard


class MainWindow(QMainWindow):
    """
    Minimal launcher window.  Users click "New Job" to open the wizard.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SLURM Job Wizard")
        self.setMinimumSize(500, 300)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Title
        title = QLabel("SLURM Job Wizard")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Create and submit SLURM batch jobs using a step-by-step wizard."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Launch button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.new_job_btn = QPushButton("New Job…")
        self.new_job_btn.setFixedSize(140, 40)
        font2 = QFont()
        font2.setPointSize(11)
        self.new_job_btn.setFont(font2)
        self.new_job_btn.clicked.connect(self._launch_wizard)
        btn_layout.addWidget(self.new_job_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setStatusBar(QStatusBar())

    def _launch_wizard(self):
        wizard = SlurmJobWizard(self)
        wizard.exec()
