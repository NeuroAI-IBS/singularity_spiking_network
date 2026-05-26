# Version 2 — connectivity-based GID assignment (release layout)

from __future__ import annotations

import glob
import os
import socket
import sqlite3
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from neuron import h

_SRC_DIR = Path(__file__).resolve().parent
_SUBPROJECT_ROOT = _SRC_DIR.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from args import parser
from cells import GranuleCell, MossyFiber
from utils import (
    elapsed_time_string,
    equalize_sublists,
    make_synapse_dict,
    print_status,
    print_timings,
    remove_overlapping_gids,
    silently_remove_files,
)

timing_log: dict[str, float] = {}
start_time: float = 0.0


def _resolve_path(path_str: str, base: Path = _SUBPROJECT_ROOT) -> Path:
    p = Path(path_str)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _connectivity_uri(db_path: Path) -> str:
    return f"file:{db_path}?mode=ro&immutable=1"


def mark_time(label: str, rank: int) -> None:
    now = time.time()
    elapsed = now - start_time
    timing_log[label] = elapsed
    print(
        f"[Rank {rank} : Timing] {label} ==> +{elapsed:.3f} sec ("
        f"{elapsed_time_string(start_time, now)}) ... OK! \n"
    )


def fetch_in_batches(cursor, assigned_gids, kind="synapse", chunk_size=10000):
    res = []
    for i in range(0, len(assigned_gids), chunk_size):
        chunk = assigned_gids[i : i + chunk_size]
        placeholders = ",".join("?" for _ in chunk)
        if kind == "synapse":
            query = (
                f"SELECT * FROM synapse WHERE target_gid IN ({placeholders}) "
                "ORDER BY target_gid ASC, source_gid ASC"
            )
            cursor.execute(query, chunk)
            res.extend(list(row) for row in cursor.fetchall())
        elif kind == "cell_type":
            query = f"SELECT cell_type FROM cell WHERE gid IN ({placeholders})"
            cursor.execute(query, chunk)
            res.extend(row[0] for row in cursor.fetchall())
        else:
            raise ValueError(f"{kind} not a valid fetch_in_batches kind")
    return res


def _record_workers(run_db: Path, host_id_map: dict[str, int]) -> None:
    with sqlite3.connect(run_db) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS worker ("
            "worker_host_id INTEGER PRIMARY KEY, worker_name TEXT NOT NULL)"
        )
        cur.execute("DELETE FROM worker")
        for name, wid in host_id_map.items():
            cur.execute(
                "INSERT INTO worker (worker_host_id, worker_name) VALUES (?, ?)",
                (wid, name),
            )
        conn.commit()


def main() -> None:
    global start_time
    timing_log.clear()
    start_time = time.time()

    args, _unknown = parser.parse_known_args()
    run_type = args.runtype
    tstop = args.tstop
    fig_needed = args.fig_needed

    db_path = _resolve_path(args.db)
    if not db_path.is_file():
        raise FileNotFoundError(f"Connectivity database not found: {db_path}")

    out_dir = _resolve_path(args.out_dir)
    results_path = out_dir
    rank_database_path = out_dir / "run_databases"
    out_dir.mkdir(parents=True, exist_ok=True)
    rank_database_path.mkdir(parents=True, exist_ok=True)

    db_uri = _connectivity_uri(db_path)
    seed_value = 42
    wE = 5e-3

    if run_type in {"coreneuron_gpu", "coreneuron_cpu"}:
        from neuron import coreneuron

        coreneuron.enable = True
        if run_type == "coreneuron_gpu":
            coreneuron.gpu = True

    h.nrnmpi_init()
    pc = h.ParallelContext()
    rank = int(pc.id())
    nhost = int(pc.nhost())
    hostname = socket.gethostname()

    print(f"[Rank {rank} : Database file] ==> {db_path}\n")
    mark_time("START", rank)

    hostnames = pc.py_allgather(hostname)
    pc.barrier()
    unique_hostnames = sorted(set(hostnames))
    host_id_map = {name: idx for idx, name in enumerate(unique_hostnames)}
    worker_host_id = host_id_map[hostname]

    if rank == 0:
        _record_workers(rank_database_path / "run_meta.db", host_id_map)
        silently_remove_files(str(rank_database_path), "mpi*", "gid*", "synapse*")
        mark_time("GID assignment", rank)
        fname = rank_database_path / "gid.db"

        with sqlite3.connect(db_uri, uri=True) as conn:
            cursor = conn.cursor()
            if nhost > 1:
                print(
                    f"[Rank{rank} : Reading] : Reading synapse table for gid assignment \n"
                )
                cursor.execute("SELECT COUNT(*) FROM synapse")
                nrows = cursor.fetchone()[0]
                rows_per_rank = (nrows + nhost - 1) // nhost
                syn = []
                for i in range(nhost):
                    offset = i * rows_per_rank
                    cursor.execute(
                        """
                        SELECT source_gid, target_gid FROM synapse
                        ORDER BY target_gid ASC, source_gid ASC
                        LIMIT ? OFFSET ?
                        """,
                        (rows_per_rank, offset),
                    )
                    synapses = cursor.fetchall()
                    syn.append(list({num for tup in synapses for num in tup}))
                gids_cleaned = remove_overlapping_gids(syn)
                equalized_gids = equalize_sublists(gids_cleaned)
                with sqlite3.connect(fname) as gid_conn:
                    gid_cursor = gid_conn.cursor()
                    for idx, rank_gids in enumerate(equalized_gids):
                        table_name = f"rank{idx}"
                        gid_cursor.execute(
                            f"CREATE TABLE IF NOT EXISTS {table_name} "
                            "(gids INTEGER NOT NULL, PRIMARY KEY (gids))"
                        )
                        gid_cursor.executemany(
                            f"INSERT INTO {table_name} (gids) VALUES (?)",
                            [(v,) for v in rank_gids],
                        )
                    gid_conn.commit()
            else:
                print_status(
                    f"[Rank{rank}] : No extra synapse database as nhost is {nhost}"
                )
                with sqlite3.connect(fname) as gid_conn:
                    gid_cursor = gid_conn.cursor()
                    table_name = f"rank{rank}"
                    gid_cursor.execute(
                        f"CREATE TABLE IF NOT EXISTS {table_name} "
                        "(gids INTEGER NOT NULL, PRIMARY KEY (gids))"
                    )
                    cursor.execute("SELECT gid FROM cell")
                    gid_cursor.executemany(
                        f"INSERT INTO {table_name} (gids) VALUES (?)",
                        [(row[0],) for row in cursor.fetchall()],
                    )
                    gid_conn.commit()

        mark_time("Synapse headers", rank)
        for ran in range(nhost):
            print(
                f"[Rank{rank} : Table headers ] : Creating synapse table headers "
                f"for Rank{ran}"
            )
            db_temp_path = rank_database_path / f"synapse_rank{ran}.db"
            if db_temp_path.exists():
                db_temp_path.unlink()
            with sqlite3.connect(db_temp_path) as temp_conn:
                temp_conn.execute(
                    """CREATE TABLE synapse (
                    source_gid INTEGER NOT NULL,
                    target_gid INTEGER NOT NULL,
                    weight INTEGER NOT NULL DEFAULT 1,
                    delay REAL NOT NULL DEFAULT 0,
                    syn_type INTEGER NOT NULL DEFAULT 1,
                    syn_dynamics INTEGER NOT NULL DEFAULT 0,
                    target_seg_id INTEGER NOT NULL,
                    target_syn_loc REAL NOT NULL DEFAULT 0.5,
                    need_single_syn INTEGER NOT NULL CHECK (need_single_syn IN (0, 1)) DEFAULT 1,
                    syn_id INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (source_gid, target_gid))"""
                )

    pc.barrier()
    mark_time("Split db storing", rank)

    table_name = f"rank{rank}"
    gid_db = rank_database_path / "gid.db"
    with sqlite3.connect(gid_db, uri=True) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT gids FROM {table_name}")
        assigned_gids = [row[0] for row in cursor.fetchall()]

    print(f"[Rank{rank}] : No. of cells assigned ==> {len(assigned_gids)}")

    with sqlite3.connect(db_uri, uri=True) as conn:
        cursor = conn.cursor()
        assigned_cell_types = fetch_in_batches(
            cursor, assigned_gids, kind="cell_type"
        )
        synapses = fetch_in_batches(cursor, assigned_gids, kind="synapse")
        cursor.execute("PRAGMA table_info(synapse)")
        synapse_table_column_names = [names[1] for names in cursor.fetchall()]
        syn_id_idx = synapse_table_column_names.index("syn_id")

    synapses_dict = make_synapse_dict(synapses)
    synapse_db = rank_database_path / f"synapse_rank{rank}.db"
    with sqlite3.connect(synapse_db) as conn:
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO synapse VALUES (?,?,?,?,?,?,?,?,?,?)", synapses)
        conn.commit()
    print(f"[Rank{rank}] : DB path is {synapse_db} ...OK!")

    mpi_rank_db = rank_database_path / f"mpi_rank{rank}.db"
    with sqlite3.connect(mpi_rank_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS gid_run_info (
            gid INTEGER PRIMARY KEY,
            mpi_rank_id INTEGER NOT NULL,
            worker_host_id INTEGER NOT NULL)"""
        )
        for g in assigned_gids:
            cursor.execute(
                "INSERT INTO gid_run_info (gid, mpi_rank_id, worker_host_id) "
                "VALUES (?, ?, ?)",
                (g, rank, worker_host_id),
            )
        conn.commit()

    synapse_needed_cells = ["grc"]
    cells = {}
    nclist = []
    grc_count = 0
    mf_count = 0

    mark_time("Creating cells ", rank)
    for cell_type, gid in zip(assigned_cell_types, assigned_gids):
        cell_seed = seed_value + gid
        if cell_type == "mf":
            cell = MossyFiber(
                gid, seed=cell_seed, mode="random", tstop=tstop, rate_needed=5
            )
            mf_count += 1
        elif cell_type == "grc":
            cell = GranuleCell(gid, seed=cell_seed, tstop=tstop)
            grc_count += 1
        else:
            raise ValueError(f"Unknown cell type: {cell_type}")

        cells[gid] = cell
        pc.set_gid2node(cell.gid, rank)
        nc = cell.connect2target(None)
        pc.cell(cell.gid, nc)

        if cell_type in synapse_needed_cells:
            syn_id = cell.determine_synaptic_connections(
                synapses_dict[gid], synapse_table_column_names
            )
            for syn, syn_id_val in zip(synapses_dict[gid], syn_id):
                syn[syn_id_idx] = syn_id_val

    pc.barrier()
    mark_time("Establish synaptic links", rank)

    for tgt_gid in synapses_dict:
        for (
            source_gid,
            target_gid,
            weight,
            delay,
            _,
            _,
            _,
            _,
            _,
            syn_id,
        ) in synapses_dict[tgt_gid]:
            nc = pc.gid_connect(source_gid, cells[target_gid].synapses[syn_id])
            nc.delay = max(delay, 0.2)
            nc.weight[0] = weight * wE
            nclist.append(nc)

    pc.barrier()
    h.celsius = 34
    h.dt = 0.025
    h.finitialize()

    mark_time("Solving Equations", rank)
    print()
    tvec = h.Vector()
    idvec = h.Vector()
    pc.spike_record(-1, tvec, idvec)
    pc.set_maxstep(10)
    solver_t0 = time.time()
    pc.psolve(tstop)
    solver_elapsed = time.time() - solver_t0
    print(f"Solver Time : {solver_elapsed:.6f}")
    pc.barrier()

    if rank == 0 and not results_path.exists():
        results_path.mkdir(parents=True, exist_ok=True)
    pc.barrier()

    mark_time("Saving the spikes ", rank)
    print()
    rank_file = results_path / f"spikes_rank{rank}.csv"
    with open(rank_file, "w") as f:
        for i in range(len(tvec)):
            f.write(f"{tvec[i]},{int(idvec[i])},{rank}\n")

    pc.barrier()

    if rank == 0:
        mark_time("Merging spikes from all the rank", rank)
        print()
        merged_file = results_path / "all_spikes.csv"
        with open(merged_file, "w") as outfile:
            for rf in sorted(glob.glob(str(results_path / "spikes_rank*.csv"))):
                with open(rf) as infile:
                    outfile.writelines(infile)
        for rf in glob.glob(str(results_path / "spikes_rank*.csv")):
            os.remove(rf)
        print(f"[Rank 0] Merged spikes into {merged_file}")
        print(f"[Rank 0] No. of mf: {mf_count}; No. of grc: {grc_count}")

        if fig_needed:
            with sqlite3.connect(db_uri, uri=True) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT gid, cell_type FROM cell")
                rows = cursor.fetchall()
            mf_gids = [gid for gid, ct in rows if ct == "mf"]
            grc_gids = [gid for gid, ct in rows if ct == "grc"]
            df = pd.read_csv(
                merged_file, header=None, names=["time", "gid", "rank"]
            )

            def reindex_gids(frame, gid_list):
                gid_map = {gid: i for i, gid in enumerate(sorted(gid_list))}
                return frame.assign(gid=frame["gid"].map(gid_map))

            mf_spikes = reindex_gids(df[df["gid"].isin(mf_gids)], mf_gids)
            grc_spikes = reindex_gids(df[df["gid"].isin(grc_gids)], grc_gids)

            def plot_raster(spikes_df, title, filename, col):
                plt.figure(figsize=(12, 6))
                plt.scatter(spikes_df["time"], spikes_df["gid"], color=col, s=1)
                plt.xlabel("Time (ms)")
                plt.ylabel("GID")
                plt.title(title)
                plt.tight_layout()
                plt.savefig(filename, dpi=300)
                plt.close()
                print(f"Saved: {filename}")

            plot_raster(
                mf_spikes,
                "Mossy Fiber Raster Plot",
                results_path / "mf_raster.png",
                col="red",
            )
            plot_raster(
                grc_spikes,
                "Granule Cell Raster Plot",
                results_path / "grc_raster.png",
                col="green",
            )

    pc.barrier()
    pc.done()
    print_timings(rank, timing_log)
    h.quit()


if __name__ == "__main__":
    main()
