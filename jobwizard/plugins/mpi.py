"""MPI parallel job plugin."""

from typing import List
from qtpy.QtWidgets import (
    QWizardPage, QFormLayout, QHBoxLayout,
    QSpinBox, QLineEdit, QComboBox, QWidget,
)

from jobwizard.constants import PAGE_MPI_RES
from jobwizard.plugins.base import JobPlugin
from jobwizard.widgets.node_diagram import NodeDiagramWidget


class _ResourcePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("MPI Job Resources")
        self.setSubTitle(
            "Specify node and process layout for an MPI parallel job."
        )

        root = QHBoxLayout(self)

        left = QWidget()
        layout = QFormLayout(left)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        root.addWidget(left, 3)

        self.diagram = NodeDiagramWidget()
        root.addWidget(self.diagram, 2)

        self.nodes_spin = QSpinBox()
        self.nodes_spin.setRange(1, 9999)
        self.nodes_spin.setValue(2)
        self.nodes_spin.setToolTip("Number of nodes to request.")
        layout.addRow("Nodes:", self.nodes_spin)

        self.tasks_per_node_spin = QSpinBox()
        self.tasks_per_node_spin.setRange(1, 512)
        self.tasks_per_node_spin.setValue(16)
        self.tasks_per_node_spin.setToolTip(
            "MPI ranks per node.  Total ranks = nodes × tasks-per-node."
        )
        layout.addRow("MPI tasks per node:", self.tasks_per_node_spin)

        self.mem_edit = QLineEdit("16")
        self.mem_unit = QComboBox()
        self.mem_unit.addItems(["MB", "GB"])
        self.mem_unit.setCurrentText("GB")
        mem_widget = QWidget()
        ml = QHBoxLayout(mem_widget)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.addWidget(self.mem_edit)
        ml.addWidget(self.mem_unit)
        layout.addRow("Memory per node:", mem_widget)

        self.time_edit = QLineEdit("04:00:00")
        layout.addRow("Time limit:", self.time_edit)

        self.launcher_combo = QComboBox()
        self.launcher_combo.addItems(["srun", "mpirun", "mpiexec"])
        self.launcher_combo.setToolTip(
            "Command used to launch MPI processes.  "
            "'srun' is recommended on most SLURM systems."
        )
        layout.addRow("MPI launcher:", self.launcher_combo)

        self.registerField("mpi_nodes", self.nodes_spin)
        self.registerField("mpi_tasks_per_node", self.tasks_per_node_spin)
        self.registerField("mpi_memory", self.mem_edit)
        self.registerField("mpi_memory_unit", self.mem_unit, "currentText")
        self.registerField("mpi_time_limit", self.time_edit)
        self.registerField("mpi_launcher", self.launcher_combo, "currentText")

        self.nodes_spin.valueChanged.connect(self._update_diagram)
        self.tasks_per_node_spin.valueChanged.connect(self._update_diagram)
        self.mem_edit.textChanged.connect(self._update_diagram)
        self.mem_unit.currentTextChanged.connect(self._update_diagram)
        self._update_diagram()

    def _update_diagram(self):
        self.diagram.set_layout(
            num_nodes=self.nodes_spin.value(),
            tasks_per_node=self.tasks_per_node_spin.value(),
            threads_per_task=1,
            mem=self.mem_edit.text(),
            mem_unit=self.mem_unit.currentText(),
        )

    def nextId(self):
        plugin = self.wizard().current_plugin()
        return plugin.next_page_id(PAGE_MPI_RES)


class MPIJobPlugin(JobPlugin):
    name = "MPI Parallel"
    description = (
        "A distributed-memory parallel job using MPI across one or more nodes."
    )
    page_id = PAGE_MPI_RES
    extra_page_ids = []

    def create_resource_page(self):
        return _ResourcePage()

    def get_sbatch_directives(self, wizard) -> List[str]:
        nodes          = wizard.field("mpi_nodes") or 2
        tasks_per_node = wizard.field("mpi_tasks_per_node") or 16
        memory         = wizard.field("mpi_memory") or "16"
        mem_unit       = wizard.field("mpi_memory_unit") or "GB"
        time_limit     = wizard.field("mpi_time_limit") or "04:00:00"

        return [
            f"#SBATCH --nodes={nodes}",
            f"#SBATCH --ntasks={nodes * tasks_per_node}",
            f"#SBATCH --ntasks-per-node={tasks_per_node}",
            f"#SBATCH --mem={memory}{mem_unit}",
            f"#SBATCH --time={time_limit}",
        ]

    def get_job_body(self, wizard) -> str:
        launcher = wizard.field("mpi_launcher") or "srun"
        script   = wizard.field("script_content") or "./my_mpi_program"
        first    = script.splitlines()[0].strip() if script.strip() else ""
        launchers = ("srun", "mpirun", "mpiexec")
        if first and not any(first.startswith(l) for l in launchers):
            return f"{launcher} {script}"
        return script
