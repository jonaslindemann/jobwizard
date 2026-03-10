"""Main SLURM Job Wizard (QWizard subclass)."""

from qtpy.QtWidgets import QWizard
from qtpy.QtCore import Qt

from jobwizard.constants import (
    PAGE_JOB_TYPE, PAGE_JOB_INFO,
    PAGE_ENVIRONMENT, PAGE_SCRIPT, PAGE_PREVIEW,
)
from jobwizard.plugins import PLUGINS
from jobwizard.pages.job_type_page import JobTypePage
from jobwizard.pages.job_info_page import JobInfoPage
from jobwizard.pages.environment_page import EnvironmentPage
from jobwizard.pages.script_page import ScriptPage
from jobwizard.pages.preview_page import PreviewPage


class SlurmJobWizard(QWizard):
    """
    A QWizard that guides the user through creating and submitting a
    SLURM batch script.

    Page layout
    -----------
    0   JobTypePage          – pick a job type
    1   JobInfoPage          – job name, partition, account, working dir
    10  GeneralJobPlugin     – resource page
    11  TaskFarmPlugin       – resource page
    12  MPIJobPlugin         – resource page
    13  OpenMPJobPlugin      – resource page
    14  HybridJobPlugin      – resource page
    20  TaskFarmPlugin       – task-list extra page
    100 EnvironmentPage      – modules + env vars
    101 ScriptPage           – commands to run
    102 PreviewPage          – generated script + submit
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SLURM Job Wizard")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setMinimumSize(720, 560)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)

        self._plugins = PLUGINS

        # Common pages
        self.setPage(PAGE_JOB_TYPE, JobTypePage(self._plugins))
        self.setPage(PAGE_JOB_INFO, JobInfoPage())
        self.setPage(PAGE_ENVIRONMENT, EnvironmentPage())
        self.setPage(PAGE_SCRIPT, ScriptPage())
        self.setPage(PAGE_PREVIEW, PreviewPage())

        # Register all plugin resource and extra pages
        for plugin in self._plugins:
            self.setPage(plugin.page_id, plugin.create_resource_page())
            for page_id, page in zip(
                plugin.extra_page_ids, plugin.create_extra_pages()
            ):
                self.setPage(page_id, page)

        self.setStartId(PAGE_JOB_TYPE)

    # ------------------------------------------------------------------
    # Public helpers used by pages
    # ------------------------------------------------------------------

    def current_plugin(self):
        """Return the JobPlugin instance selected by the user."""
        idx = self.property("_job_type_index")
        if idx is None:
            idx = 0
        idx = int(idx)
        if 0 <= idx < len(self._plugins):
            return self._plugins[idx]
        return self._plugins[0]
