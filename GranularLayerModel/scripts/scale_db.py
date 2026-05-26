#!/usr/bin/env python3
"""Replicate the bundled mf_grc connectivity database N times."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from pathlib import Path

_SUBPROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_INPUT = _SUBPROJECT_ROOT / "connectivity" / "mf_grc.db"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input",
        type=Path,
        default=_DEFAULT_INPUT,
        help="Base connectivity database",
    )
    p.add_argument("--output", type=Path, required=True, help="Scaled output database")
    p.add_argument("--scale", type=int, required=True, help="Replication factor (>= 1)")
    return p.parse_args()


def _fetch_cells(cur: sqlite3.Cursor) -> list[tuple]:
    cur.execute(
        "SELECT gid, cell_name, cell_type, x, y, z, mpi_rank_id, worker_host_id "
        "FROM cell ORDER BY gid"
    )
    return cur.fetchall()


def _fetch_synapses(cur: sqlite3.Cursor) -> list[tuple]:
    cur.execute(
        "SELECT source_gid, target_gid, weight, delay, syn_type, syn_dynamics, "
        "target_seg_id, target_syn_loc, need_single_syn, syn_id "
        "FROM synapse ORDER BY target_gid, source_gid"
    )
    return cur.fetchall()


def scale_database(input_path: Path, output_path: Path, scale: int) -> None:
    if scale < 1:
        raise ValueError("--scale must be >= 1")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    shutil.copy2(input_path, output_path)

    with sqlite3.connect(input_path) as src:
        src_cur = src.cursor()
        cells = _fetch_cells(src_cur)
        synapses = _fetch_synapses(src_cur)

    if not cells:
        raise RuntimeError(f"No cells found in {input_path}")

    n_cells = len(cells)
    max_gid = max(row[0] for row in cells)
    gid_span = max_gid + 1  # blocks offset by full GID range (gaps from removed cells)

    scaled_cells: list[tuple] = []
    scaled_synapses: list[tuple] = []
    for block in range(scale):
        offset = block * gid_span
        for row in cells:
            scaled_cells.append((row[0] + offset, *row[1:]))
        for row in synapses:
            scaled_synapses.append(
                (row[0] + offset, row[1] + offset, *row[2:])
            )

    with sqlite3.connect(output_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        cur.execute("DELETE FROM synapse")
        cur.execute("DELETE FROM gap")
        cur.execute("DELETE FROM cell")
        cur.executemany(
            "INSERT INTO cell (gid, cell_name, cell_type, x, y, z, "
            "mpi_rank_id, worker_host_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            scaled_cells,
        )
        cur.executemany(
            "INSERT INTO synapse (source_gid, target_gid, weight, delay, "
            "syn_type, syn_dynamics, target_seg_id, target_syn_loc, "
            "need_single_syn, syn_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            scaled_synapses,
        )
        conn.commit()

    _print_summary(output_path)


def _print_summary(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        print(f"Scaled database: {db_path}")
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        print("Tables:", ", ".join(r[0] for r in cur.fetchall()))
        for label, sql in (
            ("mf", "SELECT COUNT(*) FROM cell WHERE cell_type='mf'"),
            ("grc", "SELECT COUNT(*) FROM cell WHERE cell_type='grc'"),
            ("synapse", "SELECT COUNT(*) FROM synapse"),
            ("gap", "SELECT COUNT(*) FROM gap"),
        ):
            cur.execute(sql)
            print(f"  {label}: {cur.fetchone()[0]}")


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    scale_database(args.input.resolve(), args.output.resolve(), args.scale)


if __name__ == "__main__":
    main()
