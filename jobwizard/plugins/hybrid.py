"""Hybrid MPI + OpenMP job plugin."""

from typing import List
from qtpy.QtWidgets import (
    QWizardPage, QFormLayout, QHBoxLayout,
    QSpinBox, QLineEdit, QLabel, QComboBox, QWidget,
)

from jobwizard.constants import PAGE_HYBRID_RES
from jobwizard.plugins.base import JobPlugin
from jobwizard.widgets.node_diagram import NodeDiagramWidget


class _ResourcePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Hybrid MPI + OpenMP Resources")
        self.setSubTitle(
            "Configure a job that uses MPI for inter-node communication "
            "and OpenMP threads within each rank."
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
        self.nodes_spin.setValue(4)
        layout.addRow("Nodes:", self.nodes_spin)

        self.tasks_per_node_spin = QSpinBox()
        self.tasks_per_node_spin.setRange(1, 512)
        self.tasks_per_node_spin.setValue(4)
        self.tasks_per_node_spin.setToolTip("Number of MPI ranks per node.")
        layout.addRow("MPI ranks per node:", self.tasks_per_node_spin)

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 512)
        self.threads_spin.setValue(8)
        self.threads_spin.setToolTip(
            "OpenMP threads per MPI rank (= cpus-per-task)."
        )
        layout.addRow("OpenMP threads per rank:", self.threads_spin)

        self.mem_edit = QLineEdit("32")
        self.mem_unit = QComboBox()
        self.mem_unit.addItems(["MB", "GB"])
        self.mem_unit.setCurrentText("GB")
        mem_widget = QWidget()
        ml = QHBoxLayout(mem_widget)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.addWidget(self.mem_edit)
        ml.addWidget(self.mem_unit)
        layout.addRow("Memory per node:", mem_widget)

        self.time_edit = QLineEdit("08:00:00")
        layout.addRow("Time limit:", self.time_edit)

        self.launcher_combo = QComboBox()
        self.launcher_combo.addItems(["srun", "mpirun", "mpiexec"])
        layout.addRow("MPI launcher:", self.launcher_combo)

        self.registerField("hyb_nodes", self.nodes_spin)
        self.registerField("hyb_tasks_per_node", self.tasks_per_node_spin)
        self.registerField("hyb_threads", self.threads_spin)
        self.registerField("hyb_memory", self.mem_edit)
        self.registerField("hyb_memory_unit", self.mem_unit, "currentText")
        self.registerField("hyb_time_limit", self.time_edit)
        self.registerField("hyb_launcher", self.launcher_combo, "currentText")

        self.nodes_spin.valueChanged.connect(self._update_diagram)
        self.tasks_per_node_spin.valueChanged.connect(self._update_diagram)
        self.threads_spin.valueChanged.connect(self._update_diagram)
        self.mem_edit.textChanged.connect(self._update_diagram)
        self.mem_unit.currentTextChanged.connect(self._update_diagram)
        self._update_diagram()

    def _update_diagram(self):
        self.diagram.set_layout(
            num_nodes=self.nodes_spin.value(),
            tasks_per_node=self.tasks_per_node_spin.value(),
            threads_per_task=self.threads_spin.value(),
            mem=self.mem_edit.text(),
            mem_unit=self.mem_unit.currentText(),
        )

    def nextId(self):
        plugin = self.wizard().current_plugin()
        return plugin.next_page_id(PAGE_HYBRID_RES)


class HybridJobPlugin(JobPlugin):
    name = "Hybrid MPI + OpenMP"
    description = (
        "A distributed-memory MPI job with shared-memory OpenMP threading "
        "within each rank."
    )
    page_id = PAGE_HYBRID_RES
    extra_page_ids = []

    def create_resource_page(self):
        return _ResourcePage()

    def get_sbatch_directives(self, wizard) -> List[str]:
        nodes          = wizard.field("hyb_nodes") or 4
        tasks_per_node = wizard.field("hyb_tasks_per_node") or 4
        threads        = wizard.field("hyb_threads") or 8
        memory         = wizard.field("hyb_memory") or "32"
        mem_unit       = wizard.field("hyb_memory_unit") or "GB"
        time_limit     = wizard.field("hyb_time_limit") or "08:00:00"

        return [
            f"#SBATCH --nodes={nodes}",
            f"#SBATCH --ntasks={nodes * tasks_per_node}",
            f"#SBATCH --ntasks-per-node={tasks_per_node}",
            f"#SBATCH --cpus-per-task={threads}",
            f"#SBATCH --mem={memory}{mem_unit}",
            f"#SBATCH --time={time_limit}",
        ]

    def get_preamble(self, wizard) -> List[str]:
        threads  = wizard.field("hyb_threads") or 8
        launcher = wizard.field("hyb_launcher") or "srun"
        lines    = [f"export OMP_NUM_THREADS={threads}"]
        if launcher == "srun":
            lines.append("export SRUN_CPUS_PER_TASK=$SLURM_CPUS_PER_TASK")
        return lines

    def get_job_body(self, wizard) -> str:
        launcher  = wizard.field("hyb_launcher") or "srun"
        script    = wizard.field("script_content") or "./my_hybrid_program"
        first     = script.splitlines()[0].strip() if script.strip() else ""
        launchers = ("srun", "mpirun", "mpiexec")
        if first and not any(first.startswith(l) for l in launchers):
            return f"{launcher} {script}"
        return script
