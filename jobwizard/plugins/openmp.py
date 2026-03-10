"""OpenMP shared-memory parallel job plugin."""

from typing import List
from qtpy.QtWidgets import (
    QWizardPage, QFormLayout, QHBoxLayout,
    QSpinBox, QLineEdit, QComboBox, QWidget,
)

from jobwizard.constants import PAGE_OPENMP_RES
from jobwizard.plugins.base import JobPlugin
from jobwizard.widgets.node_diagram import NodeDiagramWidget


class _ResourcePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("OpenMP Job Resources")
        self.setSubTitle(
            "Specify thread count and per-node resources for a "
            "shared-memory OpenMP job."
        )

        root = QHBoxLayout(self)

        left = QWidget()
        layout = QFormLayout(left)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        root.addWidget(left, 3)

        self.diagram = NodeDiagramWidget()
        root.addWidget(self.diagram, 2)

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 512)
        self.threads_spin.setValue(8)
        self.threads_spin.setToolTip(
            "Number of OpenMP threads (= OMP_NUM_THREADS = cpus-per-task)."
        )
        layout.addRow("Threads (OMP_NUM_THREADS):", self.threads_spin)

        self.mem_edit = QLineEdit("8")
        self.mem_unit = QComboBox()
        self.mem_unit.addItems(["MB", "GB"])
        self.mem_unit.setCurrentText("GB")
        mem_widget = QWidget()
        ml = QHBoxLayout(mem_widget)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.addWidget(self.mem_edit)
        ml.addWidget(self.mem_unit)
        layout.addRow("Memory:", mem_widget)

        self.time_edit = QLineEdit("02:00:00")
        layout.addRow("Time limit:", self.time_edit)

        self.registerField("omp_threads", self.threads_spin)
        self.registerField("omp_memory", self.mem_edit)
        self.registerField("omp_memory_unit", self.mem_unit, "currentText")
        self.registerField("omp_time_limit", self.time_edit)

        self.threads_spin.valueChanged.connect(self._update_diagram)
        self.mem_edit.textChanged.connect(self._update_diagram)
        self.mem_unit.currentTextChanged.connect(self._update_diagram)
        self._update_diagram()

    def _update_diagram(self):
        self.diagram.set_layout(
            num_nodes=1,
            tasks_per_node=1,
            threads_per_task=self.threads_spin.value(),
            mem=self.mem_edit.text(),
            mem_unit=self.mem_unit.currentText(),
        )

    def nextId(self):
        plugin = self.wizard().current_plugin()
        return plugin.next_page_id(PAGE_OPENMP_RES)


class OpenMPJobPlugin(JobPlugin):
    name = "OpenMP Threaded"
    description = (
        "A shared-memory parallel job using OpenMP threads on a single node."
    )
    page_id = PAGE_OPENMP_RES
    extra_page_ids = []

    def create_resource_page(self):
        return _ResourcePage()

    def get_sbatch_directives(self, wizard) -> List[str]:
        threads    = wizard.field("omp_threads") or 8
        memory     = wizard.field("omp_memory") or "8"
        mem_unit   = wizard.field("omp_memory_unit") or "GB"
        time_limit = wizard.field("omp_time_limit") or "02:00:00"

        return [
            "#SBATCH --nodes=1",
            "#SBATCH --ntasks=1",
            f"#SBATCH --cpus-per-task={threads}",
            f"#SBATCH --mem={memory}{mem_unit}",
            f"#SBATCH --time={time_limit}",
        ]

    def get_preamble(self, wizard) -> List[str]:
        threads = wizard.field("omp_threads") or 8
        return [f"export OMP_NUM_THREADS={threads}"]
