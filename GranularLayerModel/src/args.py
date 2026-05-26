import argparse
from pathlib import Path

_SUBPROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB = _SUBPROJECT_ROOT / "connectivity" / "mf_grc.db"
_DEFAULT_OUT = _SUBPROJECT_ROOT / "results"


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "1"):
        return True
    if v.lower() in ("no", "false", "f", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


parser = argparse.ArgumentParser(
    description="MF→GrC granular-layer network driver (NEURON / CoreNEURON)."
)

parser.add_argument(
    "-runtype",
    choices=[
        "coreneuron_gpu",
        "coreneuron_cpu",
        "neuron_serial",
        "neuron_parallel",
    ],
    default="coreneuron_gpu",
    help="Simulation execution mode",
    dest="runtype",
)
parser.add_argument(
    "-tstop",
    metavar="float",
    help="Stop time (ms)",
    type=float,
    default=100.0,
)
parser.add_argument(
    "-trial",
    type=int,
    default=1,
    metavar="T",
    help="Trial number",
)
parser.add_argument(
    "--fig_needed",
    type=str2bool,
    default=True,
    help="Write raster plots (True/False)",
)
parser.add_argument(
    "--db",
    default=str(_DEFAULT_DB),
    help="Connectivity SQLite database (read-only during runs)",
)
parser.add_argument(
    "--out-dir",
    default=str(_DEFAULT_OUT),
    help="Output directory for spikes, run DBs, and optional plots",
)
