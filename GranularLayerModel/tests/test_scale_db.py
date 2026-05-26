"""Tests for scripts/scale_db.py (connectivity database replication)."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

_SUBPROJECT_ROOT = Path(__file__).resolve().parent.parent
_INPUT_DB = _SUBPROJECT_ROOT / "connectivity" / "mf_grc.db"
_SCRIPTS = _SUBPROJECT_ROOT / "scripts"
_NETWORK = _SUBPROJECT_ROOT / "src" / "network.py"
_SCALE_4X_DIR = _SUBPROJECT_ROOT / "results" / "scale_4x"
_SCALED_4X_DB = _SCALE_4X_DIR / "mf_grc_scaled_4.db"

sys.path.insert(0, str(_SCRIPTS))
from scale_db import scale_database  # noqa: E402


def _counts(db_path: Path) -> dict[str, int]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM cell")
        cells = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM synapse")
        synapses = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM cell WHERE cell_type='mf'")
        mf = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM cell WHERE cell_type='grc'")
        grc = cur.fetchone()[0]
        cur.execute("SELECT MIN(gid), MAX(gid) FROM cell")
        min_gid, max_gid = cur.fetchone()
    return {
        "cells": cells,
        "synapses": synapses,
        "mf": mf,
        "grc": grc,
        "min_gid": min_gid,
        "max_gid": max_gid,
    }


def test_scale_database_replicates_cells_and_synapses(tmp_path: Path):
    if not _INPUT_DB.is_file():
        raise FileNotFoundError(_INPUT_DB)

    base = _counts(_INPUT_DB)
    scale = 2
    output = tmp_path / "scaled.db"

    scale_database(_INPUT_DB, output, scale)

    assert output.is_file()
    scaled = _counts(output)

    assert scaled["cells"] == base["cells"] * scale
    assert scaled["synapses"] == base["synapses"] * scale
    assert scaled["mf"] == base["mf"] * scale
    assert scaled["grc"] == base["grc"] * scale
    assert scaled["min_gid"] == base["min_gid"]
    gid_span = base["max_gid"] + 1
    assert scaled["max_gid"] == base["max_gid"] + (scale - 1) * gid_span


def test_scale_4x_writes_database_to_results():
    """Replicate mf_grc.db 4× into results/scale_4x/."""
    if not _INPUT_DB.is_file():
        raise FileNotFoundError(_INPUT_DB)

    scale = 4
    _SCALE_4X_DIR.mkdir(parents=True, exist_ok=True)

    base = _counts(_INPUT_DB)
    scale_database(_INPUT_DB, _SCALED_4X_DB, scale)
    scaled = _counts(_SCALED_4X_DB)

    assert _SCALED_4X_DB.is_file()
    assert scaled["cells"] == base["cells"] * scale
    assert scaled["synapses"] == base["synapses"] * scale
    assert scaled["mf"] == base["mf"] * scale
    assert scaled["grc"] == base["grc"] * scale


def test_scale_4x_serial_run_produces_spikes():
    """Run a short serial simulation on the 4× scaled database."""
    if not _SCALED_4X_DB.is_file():
        test_scale_4x_writes_database_to_results()
    if "pytest" in sys.modules and os.environ.get("SKIP_NEURON_SMOKE"):
        import pytest

        pytest.skip("NEURON smoke test skipped (set SKIP_NEURON_SMOKE=0 to run)")

    _SCALE_4X_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(_NETWORK),
        "-tstop",
        "50",
        "-runtype",
        "neuron_serial",
        "--db",
        str(_SCALED_4X_DB),
        "--out-dir",
        str(_SCALE_4X_DIR),
        "--fig_needed",
        "false",
    ]
    subprocess.run(cmd, cwd=_SUBPROJECT_ROOT, check=True, timeout=1800)

    merged = _SCALE_4X_DIR / "all_spikes.csv"
    assert merged.is_file(), f"Missing {merged}"
    assert merged.stat().st_size > 0
