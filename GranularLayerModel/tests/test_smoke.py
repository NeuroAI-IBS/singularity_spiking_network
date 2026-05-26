"""Smoke test: short serial run and non-empty spike output."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_SUBPROJECT_ROOT = Path(__file__).resolve().parent.parent
_NETWORK = _SUBPROJECT_ROOT / "src" / "network.py"
_DB = _SUBPROJECT_ROOT / "connectivity" / "mf_grc.db"
_OUT = _SUBPROJECT_ROOT / "results" / "smoke_test"


def test_smoke_serial_run_produces_spikes():
    if not _DB.is_file():
        raise FileNotFoundError(_DB)
    if "pytest" in sys.modules and os.environ.get("SKIP_NEURON_SMOKE"):
        import pytest

        pytest.skip("NEURON smoke test skipped (set SKIP_NEURON_SMOKE=0 to run)")

    _OUT.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(_NETWORK),
        "-tstop",
        "50",
        "-runtype",
        "neuron_serial",
        "--db",
        str(_DB),
        "--out-dir",
        str(_OUT),
        "--fig_needed",
        "false",
    ]
    subprocess.run(cmd, cwd=_SUBPROJECT_ROOT, check=True, timeout=600)
    merged = _OUT / "all_spikes.csv"
    assert merged.is_file(), f"Missing {merged}"
    assert merged.stat().st_size > 0
