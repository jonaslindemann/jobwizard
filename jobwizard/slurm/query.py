"""Query the local SLURM installation for available resources."""

import subprocess
from typing import List


def _run(cmd: List[str]) -> str:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_partitions() -> List[str]:
    """Return list of available partition names."""
    out = _run(["sinfo", "--noheader", "-o", "%P"])
    partitions = []
    for line in out.splitlines():
        name = line.strip().rstrip("*")
        if name:
            partitions.append(name)
    return sorted(set(partitions)) or []


def get_accounts() -> List[str]:
    """Return list of accounts the current user belongs to."""
    out = _run(["sacctmgr", "--noheader", "show", "user", "withassoc",
                "format=account", "--parsable2"])
    accounts = [line.strip() for line in out.splitlines() if line.strip()]
    return sorted(set(accounts)) or []


def get_qos_list() -> List[str]:
    """Return list of available QOS names."""
    out = _run(["sacctmgr", "--noheader", "show", "qos",
                "format=name", "--parsable2"])
    qos = [line.strip() for line in out.splitlines() if line.strip()]
    return sorted(set(qos)) or []


def get_default_partition() -> str:
    """Return the name of the default partition (marked with *)."""
    out = _run(["sinfo", "--noheader", "-o", "%P"])
    for line in out.splitlines():
        name = line.strip()
        if name.endswith("*"):
            return name.rstrip("*")
    partitions = get_partitions()
    return partitions[0] if partitions else ""
