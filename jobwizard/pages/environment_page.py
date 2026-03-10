"""Wizard page – environment setup (modules + env vars)."""

from qtpy.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QPlainTextEdit,
    QGroupBox, QFormLayout,
)

from jobwizard.constants import PAGE_SCRIPT


class EnvironmentPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Environment Setup")
        self.setSubTitle(
            "Specify environment modules to load and any shell environment "
            "variables to set before your job runs."
        )

        layout = QVBoxLayout(self)

        # Modules group
        mod_group = QGroupBox("Modules to load")
        mod_layout = QVBoxLayout(mod_group)
        mod_hint = QLabel(
            "Enter one module name per line.  "
            "Each will be expanded to <tt>module load &lt;name&gt;</tt>."
        )
        mod_hint.setWordWrap(True)
        mod_layout.addWidget(mod_hint)
        self.modules_edit = QPlainTextEdit()
        self.modules_edit.setPlaceholderText(
            "gcc/12.2\nopenmpi/4.1.4\npython/3.11"
        )
        self.modules_edit.setMaximumHeight(120)
        mod_layout.addWidget(self.modules_edit)
        layout.addWidget(mod_group)

        # Environment variables group
        env_group = QGroupBox("Environment variables")
        env_layout = QVBoxLayout(env_group)
        env_hint = QLabel(
            "Enter one <tt>KEY=VALUE</tt> pair per line.  "
            "Each will be expanded to <tt>export KEY=VALUE</tt>."
        )
        env_hint.setWordWrap(True)
        env_layout.addWidget(env_hint)
        self.env_edit = QPlainTextEdit()
        self.env_edit.setPlaceholderText(
            "MY_SCRATCH=/scratch/$USER\nDATA_DIR=/data/project"
        )
        self.env_edit.setMaximumHeight(120)
        env_layout.addWidget(self.env_edit)
        layout.addWidget(env_group)

        layout.addStretch()

        # Register fields (plain text, optional)
        self.registerField("modules", self.modules_edit, "plainText",
                           self.modules_edit.textChanged)
        self.registerField("env_vars", self.env_edit, "plainText",
                           self.env_edit.textChanged)

    def nextId(self):
        return PAGE_SCRIPT
