"""Abstract base class for SLURM job-type plugins."""

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWizardPage


class JobPlugin(ABC):
    """
    A plugin describes one category of SLURM job (e.g. MPI, task farm …).

    Subclasses must supply:

    * ``name``        – short display name shown in the type-selection page.
    * ``description`` – one-sentence explanation shown as subtitle.
    * ``page_id``     – the wizard page-ID for this plugin's resource page.
    * ``create_resource_page()`` – factory that returns a QWizardPage.
    * ``get_sbatch_directives()`` – returns ``#SBATCH`` flag strings.

    Optional overrides:

    * ``extra_page_ids``        – additional page IDs (e.g. task list).
    * ``create_extra_pages()``  – factory for those extra pages.
    * ``get_preamble()``        – shell lines inserted before job commands.
    * ``get_job_body()``        – override default script-field body.
    """

    name: str = ""
    description: str = ""
    page_id: int = -1
    extra_page_ids: List[int] = []

    # ------------------------------------------------------------------ #
    # Abstract interface                                                   #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def create_resource_page(self) -> "QWizardPage":
        """Return the resource-configuration QWizardPage for this plugin."""

    @abstractmethod
    def get_sbatch_directives(self, wizard) -> List[str]:
        """
        Return a list of ``#SBATCH …`` directive strings (without newlines)
        specific to this job type.
        """

    # ------------------------------------------------------------------ #
    # Optional hooks                                                       #
    # ------------------------------------------------------------------ #

    def create_extra_pages(self) -> List["QWizardPage"]:
        """Return any additional QWizardPages needed (default: none)."""
        return []

    def get_preamble(self, wizard) -> List[str]:
        """
        Return shell lines inserted between the environment setup and the
        job commands (e.g. ``export OMP_NUM_THREADS=…``).
        """
        return []

    def get_job_body(self, wizard) -> str:
        """Return the main command(s) to run (default: the script field)."""
        return wizard.field("script_content") or "# your commands here"

    # ------------------------------------------------------------------ #
    # Navigation helpers                                                   #
    # ------------------------------------------------------------------ #

    def first_page_id(self) -> int:
        return self.page_id

    def next_page_after_resources(self) -> int:
        """Page to go to after the resource page (first extra page or env)."""
        from jobwizard.constants import PAGE_ENVIRONMENT
        if self.extra_page_ids:
            return self.extra_page_ids[0]
        return PAGE_ENVIRONMENT

    def next_page_id(self, current_id: int) -> int:
        """Navigate within the plugin's pages; return PAGE_ENVIRONMENT at end."""
        from jobwizard.constants import PAGE_ENVIRONMENT
        if current_id == self.page_id:
            return self.next_page_after_resources()
        # Walk extra pages
        try:
            idx = self.extra_page_ids.index(current_id)
            if idx + 1 < len(self.extra_page_ids):
                return self.extra_page_ids[idx + 1]
        except ValueError:
            pass
        return PAGE_ENVIRONMENT
