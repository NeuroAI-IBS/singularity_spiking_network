# Granular Layer Model

A large-scale, biologically grounded model of the cerebellar mossy-fibre → granule-cell microcircuit. This is a **subproject** of [SingularityCoreNeuron](https://github.com/NeuroAI-IBS/SingularityCoreNeuron), which provides the portable Singularity container the model runs in.

It accompanies the manuscript

> O. James and S. Hong, *Container-Based Framework for Large-Scale Computational Neuroscience*, IBS, 2026.

The container image (`*.sif`) is built from the `.def` files in `../def_files/` using `../build_container`; see the parent's [`README.md`](../README.md) for the full installation guide and HPC configuration notes. Once the image is built, this subproject supplies the model code, the EM-derived connectivity database, and a small set of helpers to scale it.

## What is in this subproject

| Folder | Contents |
| --- | --- |
| `src/` | The simulation code: cell models, network driver, NEURON MOD files. Runs *inside* the container. |
| `scripts/` | Host-side helper(s); currently just `scale_db.py`, which replicates the bundled connectivity database N times. |
| `connectivity/` | The bundled connectivity database (`mf_grc.db`, 1070 MF + 3925 GrC; 4995 cells total) derived from the EM reconstruction of [Nguyen et al. 2023](https://github.com/htem/cb2_project_analysis). This is shipped as a data artifact and is not rebuilt at release time; provenance details are in `connectivity/README.md`. |
| `notebooks/` | A single-cell sanity-check notebook (`Cell_test.ipynb`). |
| `tests/` | A 50-ms smoke test used by CI. |

The container, the SLURM batch templates, the published benchmark CSVs, and the figure-generation script all live in the parent project:

| Topic | Parent path |
| --- | --- |
| Container build pipeline | `../build_container`, `../def_files/` |
| SLURM templates | `../batch/` |
| Benchmark CSVs (Fig 2, Fig 3) | `../results/` |
| Plot generation (R) | `../scripts/plots.R` |

## Running the Simulation

Run these commands from the parent repository root after building the container described in `../README.md`.

```bash
SIF=$HOME/containers/images/olaf.sif

# 1. Compile the NEURON mechanisms inside the container.
singularity exec --nv "$SIF" \
    nrnivmodl -coreneuron GranularLayerModel/src/mod

# 2. (Optional) scale the bundled connectivity database to the paper size.
#    The base connectivity/mf_grc.db is shipped — there is no rebuild step.
python GranularLayerModel/scripts/scale_db.py \
    --input  GranularLayerModel/connectivity/mf_grc.db \
    --scale  280 \
    --output GranularLayerModel/connectivity/mf_grc_scaled_280.db

# 3. Run a 1-second simulation on a single GPU.
singularity exec --nv "$SIF" \
    mpiexec -n 1 python GranularLayerModel/src/network.py \
        --db GranularLayerModel/connectivity/mf_grc.db \
        -tstop 1000 -runtype coreneuron_gpu
```

## Reproducing the manuscript end-to-end

The full benchmark sweep behind Figures 2 and 3 is driven from the parent's `batch/` and the committed benchmark CSVs:

```bash
# In singularity_coreneuron/, with the model code at GranularLayerModel/.
sbatch batch/levi.sh             # Titan V (2 GPUs) × N trials
Rscript scripts/plots.R          # regenerate Figs 2 and 3
```

The benchmark CSVs we report in the paper are already committed at `../results/benchmark.csv`, `../results/benchmark_1M.csv`, and `../results/benchmark_model_building.csv`. These include Titan RTX (Karina) and Titan V (Levi) runs from the manuscript. The missing CPU-baseline batch/data artifacts are tracked in `../PARENT_REFACTOR.md`.

## Citing this work

If you use this code or the container, please cite:

- James O. & Hong S. (2026). *Container-Based Framework for Large-Scale Computational Neuroscience.* IBS, Daejeon, Korea. (See the parent repository's `CITATION.cff`.)
- Nguyen et al. (2023). *Electron-microscopy reconstruction of the cerebellar granule-cell layer.* (See `connectivity/README.md`.)
- Sudhakar et al. (2017). *Spatiotemporal patterns of granule-cell activity in the cerebellar cortex.* (Channel-mechanism source.)

## Acknowledgments

This model builds on prior open-source work:

1. [GranularLayerSolinasNieusDAngelo2010](https://github.com/OpenSourceBrain/GranularLayerSolinasNieusDAngelo2010)
2. [granular-layer-cerebellum](https://github.com/dbbs-lab/granular-layer-cerebellum)
3. [cb2_project_analysis](https://github.com/htem/cb2_project_analysis) (EM connectivity)
4. NEURON / CoreNEURON team, NVIDIA HPC SDK team, Sylabs (Singularity).

## License

This subproject inherits the parent project's licence; see [`../LICENSE`](../LICENSE) (MIT) at the root of `SingularityCoreNeuron`. If a different licence applies to files inherited from upstream projects (e.g. some `*.mod` files), it is noted in the file header.
