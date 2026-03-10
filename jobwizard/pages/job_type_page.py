"""Wizard page 0 – Job type selection."""

from qtpy.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QButtonGroup, QRadioButton,
    QGroupBox, QScrollArea, QWidget, QFrame,
)
from qtpy.QtCore import Qt

from jobwizard.constants import PAGE_JOB_INFO


class JobTypePage(QWizardPage):
    """First page: user picks the job type from all registered plugins."""

    def __init__(self, plugins, parent=None):
        super().__init__(parent)
        self._plugins = plugins
        self.setTitle("Select Job Type")
        self.setSubTitle(
            "Choose the type of SLURM job you want to create."
        )

        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setSpacing(4)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        for idx, plugin in enumerate(plugins):
            box = QGroupBox()
            box_layout = QVBoxLayout(box)

            radio = QRadioButton(plugin.name)
            radio.setStyleSheet("font-weight: bold;")
            self._button_group.addButton(radio, idx)
            if idx == 0:
                radio.setChecked(True)
            box_layout.addWidget(radio)

            desc = QLabel(plugin.description)
            desc.setWordWrap(True)
            desc.setContentsMargins(20, 0, 0, 0)
            box_layout.addWidget(desc)

            layout.addWidget(box)

        layout.addStretch()

        # Register the selection as a wizard field (int index)
        # We use a hidden QLabel trick; actual value read via _current_index()
        self._button_group.buttonToggled.connect(
            lambda *_: self.completeChanged.emit()
        )

    def _current_index(self) -> int:
        return self._button_group.checkedId()

    def isComplete(self) -> bool:
        return self._current_index() >= 0

    def initializePage(self):
        # Store initial selection
        self._sync_field()

    def validatePage(self) -> bool:
        self._sync_field()
        return True

    def _sync_field(self):
        # We write the index into the wizard directly since QWizard fields
        # work best with Qt property-based widgets.  We store it in the
        # wizard's dynamic property so other pages can read it.
        wiz = self.wizard()
        if wiz is not None:
            wiz.setProperty("_job_type_index", self._current_index())

    def nextId(self):
        return PAGE_JOB_INFO
