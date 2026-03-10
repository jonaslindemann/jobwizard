"""Job-type plugin registry."""

from .general import GeneralJobPlugin
from .task_farm import TaskFarmPlugin
from .mpi import MPIJobPlugin
from .openmp import OpenMPJobPlugin
from .hybrid import HybridJobPlugin

# Ordered list of all available plugins.  Index matches wizard field
# "job_type_index" and the PLUGIN_FIRST_PAGE mapping in constants.py.
PLUGINS = [
    GeneralJobPlugin(),
    TaskFarmPlugin(),
    MPIJobPlugin(),
    OpenMPJobPlugin(),
    HybridJobPlugin(),
]
