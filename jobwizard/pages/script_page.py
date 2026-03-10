"""Wizard page – job script / command entry."""

from qtpy.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QPlainTextEdit,
    QHBoxLayout, QPushButton, QFileDialog,
)
from qtpy.QtGui import QFont

from jobwizard.constants import PAGE_PREVIEW


class ScriptPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Job Commands")
        self.setSubTitle(
            "Enter the commands your job should execute.  "
            "For MPI/Hybrid jobs the launcher command will be prepended "
            "automatically if not present."
        )

        layout = QVBoxLayout(self)

        hint = QLabel(
            "You can enter a single executable, a multi-line shell script, "
            "or use the load button to import an existing script."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.script_edit = QPlainTextEdit()
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.TypeWriter)
        self.script_edit.setFont(mono)
        self.script_edit.setPlaceholderText("./my_program --input data.txt")
        layout.addWidget(self.script_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        load_btn = QPushButton("Load from file…")
        load_btn.clicked.connect(self._load_file)
        btn_layout.addWidget(load_btn)
        layout.addLayout(btn_layout)

        self.registerField("script_content", self.script_edit, "plainText",
                           self.script_edit.textChanged)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Script", "", "Shell scripts (*.sh *.bash);;All files (*)"
        )
        if path:
            try:
                with open(path) as fh:
                    content = fh.read()
                # Strip shebang and #SBATCH lines – user likely wants just body
                lines = []
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("#!") or stripped.startswith("#SBATCH"):
                        continue
                    lines.append(line)
                self.script_edit.setPlainText("\n".join(lines).strip())
            except OSError as exc:
                from qtpy.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Load Error", str(exc))

    def nextId(self):
        return PAGE_PREVIEW
