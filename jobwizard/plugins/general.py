"""General / serial SLURM job plugin."""

from typing import List
from qtpy.QtWidgets import (
    QWizardPage, QFormLayout, QHBoxLayout, QVBoxLayout,
    QSpinBox, QLineEdit, QComboBox, QWidget,
)

from jobwizard.constants import PAGE_GENERAL_RES
from jobwizard.plugins.base import JobPlugin
from jobwizard.widgets.node_diagram import NodeDiagramWidget


class _ResourcePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Job Resources")
        self.setSubTitle(
            "Specify the compute resources required for this job."
        )

        # ---- Split: form (left) | diagram (right) ----
        root = QHBoxLayout(self)

        left = QWidget()
        layout = QFormLayout(left)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        root.addWidget(left, 3)

        self.diagram = NodeDiagramWidget()
        root.addWidget(self.diagram, 2)

        # ---- Form fields ----
        self.nodes_spin = QSpinBox()
        self.nodes_spin.setRange(1, 9999)
        self.nodes_spin.setValue(1)
        self.nodes_spin.setToolTip("Number of nodes to allocate.")
        layout.addRow("Nodes:", self.nodes_spin)

        self.ntasks_spin = QSpinBox()
        self.ntasks_spin.setRange(1, 999999)
        self.ntasks_spin.setValue(1)
        self.ntasks_spin.setToolTip(
            "Total number of tasks (processes)."
        )
        layout.addRow("Tasks (–ntasks):", self.ntasks_spin)

        self.cpus_spin = QSpinBox()
        self.cpus_spin.setRange(1, 512)
        self.cpus_spin.setValue(1)
        self.cpus_spin.setToolTip("CPUs allocated per task.")
        layout.addRow("CPUs per task:", self.cpus_spin)

        self.mem_edit = QLineEdit("4")
        self.mem_unit = QComboBox()
        self.mem_unit.addItems(["MB", "GB"])
        self.mem_unit.setCurrentText("GB")
        mem_widget = QWidget()
        ml = QHBoxLayout(mem_widget)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.addWidget(self.mem_edit)
        ml.addWidget(self.mem_unit)
        layout.addRow("Memory per node:", mem_widget)

        self.time_edit = QLineEdit("01:00:00")
        self.time_edit.setToolTip(
            "Wall-clock time limit in HH:MM:SS or D-HH:MM:SS format."
        )
        layout.addRow("Time limit:", self.time_edit)

        # Register fields
        self.registerField("nodes", self.nodes_spin)
        self.registerField("ntasks", self.ntasks_spin)
        self.registerField("cpus_per_task", self.cpus_spin)
        self.registerField("memory", self.mem_edit)
        self.registerField("memory_unit", self.mem_unit, "currentText")
        self.registerField("time_limit", self.time_edit)

        # Connect diagram updates
        self.nodes_spin.valueChanged.connect(self._update_diagram)
        self.ntasks_spin.valueChanged.connect(self._update_diagram)
        self.cpus_spin.valueChanged.connect(self._update_diagram)
        self.mem_edit.textChanged.connect(self._update_diagram)
        self.mem_unit.currentTextChanged.connect(self._update_diagram)
        self._update_diagram()

    def _update_diagram(self):
        nodes   = self.nodes_spin.value()
        ntasks  = self.ntasks_spin.value()
        cpus    = self.cpus_spin.value()
        tpn     = max(1, (ntasks + nodes - 1) // nodes)  # tasks per node
        mem     = self.mem_edit.text()
        unit    = self.mem_unit.currentText()
        self.diagram.set_layout(
            num_nodes=nodes,
            tasks_per_node=tpn,
            threads_per_task=cpus,
            mem=mem,
            mem_unit=unit,
        )

    def nextId(self):
        plugin = self.wizard().current_plugin()
        return plugin.next_page_id(PAGE_GENERAL_RES)


class GeneralJobPlugin(JobPlugin):
    name = "General / Serial"
    description = (
        "A standard single or multi-process job with no special parallelism."
    )
    page_id = PAGE_GENERAL_RES
    extra_page_ids = []

    def create_resource_page(self):
        return _ResourcePage()

    def get_sbatch_directives(self, wizard) -> List[str]:
        nodes      = wizard.field("nodes") or 1
        ntasks     = wizard.field("ntasks") or 1
        cpus       = wizard.field("cpus_per_task") or 1
        memory     = wizard.field("memory") or "4"
        mem_unit   = wizard.field("memory_unit") or "GB"
        time_limit = wizard.field("time_limit") or "01:00:00"

        directives = [
            f"#SBATCH --nodes={nodes}",
            f"#SBATCH --ntasks={ntasks}",
        ]
        if cpus > 1:
            directives.append(f"#SBATCH --cpus-per-task={cpus}")
        directives += [
            f"#SBATCH --mem={memory}{mem_unit}",
            f"#SBATCH --time={time_limit}",
        ]
        return directives
