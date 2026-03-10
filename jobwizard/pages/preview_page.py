"""Wizard page – script preview, save, and job submission."""

import os
from qtpy.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QFileDialog, QMessageBox, QFrame,
)
from qtpy.QtGui import QFont
from qtpy.QtCore import Qt


class PreviewPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Preview & Submit")
        self.setSubTitle(
            "Review the generated SLURM script.  You may edit it freely "
            "before saving or submitting."
        )
        self._submitted = False

        layout = QVBoxLayout(self)

        self.script_edit = QPlainTextEdit()
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.TypeWriter)
        self.script_edit.setFont(mono)
        layout.addWidget(self.script_edit)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.regenerate_btn = QPushButton("Regenerate")
        self.regenerate_btn.setToolTip(
            "Regenerate the script from wizard fields, discarding manual edits."
        )
        self.regenerate_btn.clicked.connect(self._regenerate)
        btn_layout.addWidget(self.regenerate_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("Save script…")
        self.save_btn.clicked.connect(self._save)
        btn_layout.addWidget(self.save_btn)

        self.submit_btn = QPushButton("Submit job")
        self.submit_btn.setDefault(True)
        self.submit_btn.clicked.connect(self._submit)
        btn_layout.addWidget(self.submit_btn)

        layout.addLayout(btn_layout)

        # Result area
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.setTextFormat(Qt.RichText)
        layout.addWidget(self.result_label)

    # ------------------------------------------------------------------
    # QWizardPage overrides
    # ------------------------------------------------------------------

    def initializePage(self):
        self._submitted = False
        self.result_label.clear()
        self._regenerate()

    def isComplete(self) -> bool:
        # Allow Finish even without submitting
        return True

    def nextId(self):
        return -1  # Last page

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _regenerate(self):
        wiz = self.wizard()
        if wiz is None:
            return
        try:
            from jobwizard.slurm.generator import build_script
            plugin = wiz.current_plugin()
            script = build_script(plugin, wiz)
            self.script_edit.setPlainText(script)
        except Exception as exc:
            self.script_edit.setPlainText(f"# Error generating script:\n# {exc}")

    def _current_script(self) -> str:
        return self.script_edit.toPlainText()

    def _save(self):
        job_name = self.wizard().field("job_name") or "job"
        default_name = f"{job_name}.sh"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Script", default_name,
            "Shell scripts (*.sh);;All files (*)"
        )
        if not path:
            return
        from jobwizard.slurm.submitter import save_script
        ok, msg = save_script(self._current_script(), path)
        if ok:
            self.result_label.setText(
                f'<span style="color: green;">{msg}</span>'
            )
        else:
            QMessageBox.warning(self, "Save Error", msg)

    def _submit(self):
        script = self._current_script()
        if not script.strip():
            QMessageBox.warning(self, "Empty Script", "The script is empty.")
            return

        reply = QMessageBox.question(
            self,
            "Submit Job",
            "Submit this job to SLURM?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.submit_btn.setEnabled(False)
        self.result_label.setText("Submitting…")

        from jobwizard.slurm.submitter import submit_script
        ok, msg = submit_script(script)
        self.submit_btn.setEnabled(True)

        if ok:
            self._submitted = True
            self.result_label.setText(
                f'<span style="color: green;"><b>{msg}</b></span>'
            )
        else:
            self.result_label.setText(
                f'<span style="color: red;"><b>Submission failed:</b> {msg}</span>'
            )
