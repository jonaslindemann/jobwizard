"""Wizard page 1 – Job information (name, partition, account, QOS)."""

import os
from qtpy.QtWidgets import (
    QWizardPage, QFormLayout, QLineEdit, QComboBox, QLabel,
    QPushButton, QFileDialog, QHBoxLayout, QWidget,
)

from jobwizard.constants import PLUGIN_FIRST_PAGE


class JobInfoPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Job Information")
        self.setSubTitle(
            "Enter the basic job metadata and resource allocation details."
        )

        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Job name
        self.name_edit = QLineEdit("my_job")
        self.name_edit.setToolTip("Identifier shown in the queue (no spaces).")
        layout.addRow("Job name *:", self.name_edit)

        # Partition
        self.partition_combo = QComboBox()
        self.partition_combo.setEditable(True)
        self.partition_combo.setToolTip(
            "SLURM partition (queue).  Populated from sinfo if available."
        )
        layout.addRow("Partition:", self.partition_combo)

        # Account
        self.account_combo = QComboBox()
        self.account_combo.setEditable(True)
        self.account_combo.setToolTip(
            "Project / account for billing.  Leave blank to use default."
        )
        layout.addRow("Account:", self.account_combo)

        # QOS
        self.qos_combo = QComboBox()
        self.qos_combo.setEditable(True)
        self.qos_combo.setToolTip("Quality of Service.  Leave blank for default.")
        layout.addRow("QOS:", self.qos_combo)

        # Working directory
        wd_widget = QWidget()
        wd_layout = QHBoxLayout(wd_widget)
        wd_layout.setContentsMargins(0, 0, 0, 0)
        self.workdir_edit = QLineEdit(os.getcwd())
        self.workdir_edit.setToolTip(
            "Directory the job will run in (--chdir).  "
            "Leave blank to use the submission directory."
        )
        wd_layout.addWidget(self.workdir_edit)
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_workdir)
        wd_layout.addWidget(browse_btn)
        layout.addRow("Working directory:", wd_widget)

        # Output / error file patterns (common to all job types)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("<job-name>_%j.out")
        self.output_edit.setToolTip(
            "stdout file pattern.  Leave blank for default.  "
            "Use %j for job ID, %A for array job ID, %a for array index."
        )
        layout.addRow("Output file:", self.output_edit)

        self.error_edit = QLineEdit()
        self.error_edit.setPlaceholderText("<job-name>_%j.err")
        self.error_edit.setToolTip(
            "stderr file pattern.  Leave blank for default."
        )
        layout.addRow("Error file:", self.error_edit)

        # Register fields (job_name without * — completion handled by isComplete())
        self.registerField("job_name", self.name_edit)
        self.registerField("partition", self.partition_combo, "currentText",
                           self.partition_combo.currentTextChanged)
        self.registerField("account", self.account_combo, "currentText",
                           self.account_combo.currentTextChanged)
        self.registerField("qos", self.qos_combo, "currentText",
                           self.qos_combo.currentTextChanged)
        self.registerField("working_dir", self.workdir_edit)
        self.registerField("output_file", self.output_edit)
        self.registerField("error_file", self.error_edit)

        # Drive Next-button state from the job name field directly
        self.name_edit.textChanged.connect(self.completeChanged)

    def isComplete(self) -> bool:
        return bool(self.name_edit.text().strip())

    def initializePage(self):
        """Populate combo boxes from SLURM queries (non-blocking)."""
        try:
            from jobwizard.slurm.query import (
                get_partitions, get_accounts, get_qos_list,
                get_default_partition,
            )
            partitions = get_partitions()
            default = get_default_partition()
            self.partition_combo.clear()
            self.partition_combo.addItem("")
            for p in partitions:
                self.partition_combo.addItem(p)
            if default:
                idx = self.partition_combo.findText(default)
                if idx >= 0:
                    self.partition_combo.setCurrentIndex(idx)

            self.account_combo.clear()
            self.account_combo.addItem("")
            for a in get_accounts():
                self.account_combo.addItem(a)

            self.qos_combo.clear()
            self.qos_combo.addItem("")
            for q in get_qos_list():
                self.qos_combo.addItem(q)
        except Exception:
            pass  # SLURM not available; user fills in manually

    def _browse_workdir(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Working Directory", self.workdir_edit.text()
        )
        if path:
            self.workdir_edit.setText(path)

    def nextId(self):
        wiz = self.wizard()
        idx = wiz.property("_job_type_index") if wiz else 0
        if idx is None:
            idx = 0
        return PLUGIN_FIRST_PAGE.get(int(idx), 10)
