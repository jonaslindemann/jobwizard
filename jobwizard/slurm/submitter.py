"""Submit SBATCH scripts to SLURM."""

import subprocess
import tempfile
import os
from typing import Tuple


def submit_script(script_text: str) -> Tuple[bool, str]:
    """
    Write *script_text* to a temporary file and submit it with ``sbatch``.

    Returns
    -------
    (success, message)
        *success* is True if sbatch exited with code 0.
        *message* contains the stdout/stderr from sbatch.
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".sh",
        prefix="jobwizard_",
        delete=False,
    ) as fh:
        fh.write(script_text)
        tmp_path = fh.name

    try:
        result = subprocess.run(
            ["sbatch", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except FileNotFoundError:
        return False, "sbatch not found. Is SLURM installed and in PATH?"
    except subprocess.TimeoutExpired:
        return False, "sbatch timed out."
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def save_script(script_text: str, path: str) -> Tuple[bool, str]:
    """Save the script to *path* without submitting."""
    try:
        with open(path, "w") as fh:
            fh.write(script_text)
        return True, f"Script saved to {path}"
    except OSError as exc:
        return False, str(exc)
