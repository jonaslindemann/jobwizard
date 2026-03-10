"""Page ID constants for the SLURM Job Wizard."""

# Wizard page IDs
PAGE_JOB_TYPE = 0
PAGE_JOB_INFO = 1

# Plugin-specific resource pages (one per plugin)
PAGE_GENERAL_RES = 10
PAGE_TASK_FARM_RES = 11
PAGE_MPI_RES = 12
PAGE_OPENMP_RES = 13
PAGE_HYBRID_RES = 14

# Plugin extra pages
PAGE_TASK_FARM_TASKS = 20  # Task list / input file spec for task farm

# Common tail pages
PAGE_ENVIRONMENT = 100
PAGE_SCRIPT = 101
PAGE_PREVIEW = 102

# Mapping: plugin index → first page ID
PLUGIN_FIRST_PAGE = {
    0: PAGE_GENERAL_RES,
    1: PAGE_TASK_FARM_RES,
    2: PAGE_MPI_RES,
    3: PAGE_OPENMP_RES,
    4: PAGE_HYBRID_RES,
}
