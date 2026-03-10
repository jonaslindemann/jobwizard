"""Task-farm (SLURM array job) plugin."""

from typing import List
from qtpy.QtWidgets import (
    QWizardPage, QFormLayout, QHBoxLayout, QVBoxLayout,
    QSpinBox, QLineEdit, QLabel, QComboBox, QPlainTextEdit, QWidget,
)

from jobwizard.constants import PAGE_TASK_FARM_RES, PAGE_TASK_FARM_TASKS
from jobwizard.plugins.base import JobPlugin
from jobwizard.widgets.node_diagram import NodeDiagramWidget


class _ResourcePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Task Farm Resources")
        self.setSubTitle(
            "Configure the array range and per-task resource requirements."
        )

        root = QHBoxLayout(self)

        left = QWidget()
        layout = QFormLayout(left)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        root.addWidget(left, 3)

        self.diagram = NodeDiagramWidget()
        root.addWidget(self.diagram, 2)

        # Array specification
        self.array_edit = QLineEdit("1-100")
        self.array_edit.setToolTip(
            "SLURM array range, e.g. '1-100', '0-49', '1,3,5', '1-100:2'."
        )
        layout.addRow("Array range:", self.array_edit)

        # Concurrent tasks
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(0, 9999)
        self.concurrent_spin.setValue(0)
        self.concurrent_spin.setSpecialValueText("Unlimited")
        self.concurrent_spin.setToolTip(
            "Maximum simultaneously running tasks (0 = unlimited)."
        )
        layout.addRow("Max concurrent tasks:", self.concurrent_spin)

        # CPUs per task
        self.cpus_spin = QSpinBox()
        self.cpus_spin.setRange(1, 512)
        self.cpus_spin.setValue(1)
        layout.addRow("CPUs per task:", self.cpus_spin)

        # Memory per task
        self.mem_edit = QLineEdit("2")
        self.mem_unit = QComboBox()
        self.mem_unit.addItems(["MB", "GB"])
        self.mem_unit.setCurrentText("GB")
        mem_widget = QWidget()
        ml = QHBoxLayout(mem_widget)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.addWidget(self.mem_edit)
        ml.addWidget(self.mem_unit)
        layout.addRow("Memory per task:", mem_widget)

        # Wall time
        self.time_edit = QLineEdit("00:30:00")
        self.time_edit.setToolTip("Wall-clock time limit per task.")
        layout.addRow("Time limit:", self.time_edit)

        # array_range without * — completion driven by isComplete() override
        self.registerField("array_range", self.array_edit)
        self.registerField("array_concurrent", self.concurrent_spin)
        self.registerField("tf_cpus_per_task", self.cpus_spin)
        self.registerField("tf_memory", self.mem_edit)
        self.registerField("tf_memory_unit", self.mem_unit, "currentText")
        self.registerField("tf_time_limit", self.time_edit)

        self.array_edit.textChanged.connect(self.completeChanged)

        # Connect diagram updates
        self.cpus_spin.valueChanged.connect(self._update_diagram)
        self.mem_edit.textChanged.connect(self._update_diagram)
        self.mem_unit.currentTextChanged.connect(self._update_diagram)
        self._update_diagram()

    def isComplete(self) -> bool:
        return bool(self.array_edit.text().strip())

    def _update_diagram(self):
        self.diagram.set_layout(
            num_nodes=1,
            tasks_per_node=1,
            threads_per_task=self.cpus_spin.value(),
            mem=self.mem_edit.text(),
            mem_unit=self.mem_unit.currentText(),
        )

    def nextId(self):
        plugin = self.wizard().current_plugin()
        return plugin.next_page_id(PAGE_TASK_FARM_RES)


class _TaskListPage(QWizardPage):
    """Optional page to specify a per-task input file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Task Inputs")
        self.setSubTitle(
            "Optionally provide a list of per-task arguments or input files "
            "(one item per line).  Leave blank to rely on $SLURM_ARRAY_TASK_ID."
        )

        layout = QVBoxLayout(self)

        hint = QLabel(
            "Each line will be available as a positional parameter in your "
            "script via the helper variable <tt>TASK_INPUT</tt> "
            "(line number matches <tt>$SLURM_ARRAY_TASK_ID</tt>)."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.task_list_edit = QPlainTextEdit()
        self.task_list_edit.setPlaceholderText(
            "input_file_1.dat\ninput_file_2.dat\n..."
        )
        layout.addWidget(self.task_list_edit)

        self.registerField("task_inputs", self.task_list_edit, "plainText",
                           self.task_list_edit.textChanged)

    def nextId(self):
        plugin = self.wizard().current_plugin()
        return plugin.next_page_id(PAGE_TASK_FARM_TASKS)


class TaskFarmPlugin(JobPlugin):
    name = "Task Farm (Array Job)"
    description = (
        "Run many independent tasks with a single job submission "
        "using SLURM job arrays."
    )
    page_id = PAGE_TASK_FARM_RES
    extra_page_ids = [PAGE_TASK_FARM_TASKS]

    def create_resource_page(self):
        return _ResourcePage()

    def create_extra_pages(self):
        return [_TaskListPage()]

    def get_sbatch_directives(self, wizard) -> List[str]:
        array_range = wizard.field("array_range") or "1-1"
        concurrent  = wizard.field("array_concurrent") or 0
        cpus        = wizard.field("tf_cpus_per_task") or 1
        memory      = wizard.field("tf_memory") or "2"
        mem_unit    = wizard.field("tf_memory_unit") or "GB"
        time_limit  = wizard.field("tf_time_limit") or "00:30:00"

        array_spec = (f"{array_range}%{concurrent}"
                      if concurrent and concurrent > 0 else array_range)
        directives = [f"#SBATCH --array={array_spec}", "#SBATCH --ntasks=1"]
        if cpus > 1:
            directives.append(f"#SBATCH --cpus-per-task={cpus}")
        directives += [
            f"#SBATCH --mem={memory}{mem_unit}",
            f"#SBATCH --time={time_limit}",
        ]
        return directives

    def get_preamble(self, wizard) -> List[str]:
        lines = []
        task_inputs = wizard.field("task_inputs") or ""
        items = [l.strip() for l in task_inputs.splitlines() if l.strip()]
        if items:
            lines.append("# Select per-task input from the task list")
            lines.append("TASK_INPUTS=(")
            for item in items:
                lines.append(f'    "{item}"')
            lines.append(")")
            lines.append(
                "TASK_INPUT=${TASK_INPUTS[$SLURM_ARRAY_TASK_ID - 1]}"
            )
        return lines

    def get_job_body(self, wizard) -> str:
        return wizard.field("script_content") or "# your commands here"
