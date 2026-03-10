"""Generate SBATCH scripts from wizard data."""

from typing import List


def _directive(flag: str, value) -> str:
    return f"#SBATCH {flag}={value}"


def build_script(plugin, wizard) -> str:
    """
    Assemble a complete SBATCH script.

    Parameters
    ----------
    plugin : JobPlugin
        The active job-type plugin (provides SBATCH directives and job body).
    wizard : SlurmJobWizard
        The wizard instance; fields are read via wizard.field().
    """
    lines: List[str] = ["#!/bin/bash"]
    lines.append("")

    # ------ Common job-info directives ------
    job_name = wizard.field("job_name") or "slurm_job"
    lines.append(_directive("--job-name", job_name))

    partition = wizard.field("partition")
    if partition:
        lines.append(_directive("--partition", partition))

    account = wizard.field("account")
    if account:
        lines.append(_directive("--account", account))

    qos = wizard.field("qos")
    if qos:
        lines.append(_directive("--qos", qos))

    # ------ Plugin-specific resource directives ------
    lines.extend(plugin.get_sbatch_directives(wizard))

    # ------ Output / error files ------
    output_file = wizard.field("output_file") or f"{job_name}_%j.out"
    error_file = wizard.field("error_file") or f"{job_name}_%j.err"
    lines.append(_directive("--output", output_file))
    lines.append(_directive("--error", error_file))

    # ------ Working directory ------
    working_dir = wizard.field("working_dir")
    if working_dir:
        lines.append(_directive("--chdir", working_dir))

    lines.append("")

    # ------ Environment: module loads ------
    modules_raw = wizard.field("modules") or ""
    modules = [m.strip() for m in modules_raw.splitlines() if m.strip()]
    if modules:
        lines.append("# Load modules")
        for mod in modules:
            lines.append(f"module load {mod}")
        lines.append("")

    # ------ Environment: env vars ------
    env_vars_raw = wizard.field("env_vars") or ""
    env_vars = [v.strip() for v in env_vars_raw.splitlines() if v.strip()]
    if env_vars:
        lines.append("# Environment variables")
        for var in env_vars:
            if "=" in var:
                lines.append(f"export {var}")
        lines.append("")

    # ------ Plugin preamble (e.g. OMP_NUM_THREADS) ------
    preamble = plugin.get_preamble(wizard)
    if preamble:
        lines.append("# Job setup")
        lines.extend(preamble)
        lines.append("")

    # ------ Job body ------
    lines.append("# Job commands")
    body = plugin.get_job_body(wizard)
    lines.append(body)
    lines.append("")

    return "\n".join(lines)
