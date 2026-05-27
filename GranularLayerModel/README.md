# Spiking network model of the cerebellar granular layer

A large-scale, biologically grounded model of the cerebellar mossy-fibre → granule-cell microcircuit based on the physiological spiking neuron models and connectome data.

It accompanies the manuscript

> O. James and S. Hong (2026) Container-Based Framework for Large-Scale Spiking Network Simulation, *submitted*.

The container image (`*.sif`) is built from the `.def` files in `../def_files/` using `../build_container`; see the parent's `[README.md](../README.md)` for the full installation guide and HPC configuration notes. Once the image is built, this subproject supplies the model code, the EM-derived connectivity database, and a small set of helpers to scale it.

## What is in this subproject


| Folder | Contents |
| --------------- | ------- |
| `src/`| The simulation code: cell models, network driver, NEURON MOD files. Runs *inside* the container.|
| `scripts/` | Host-side helper(s); currently just `scale_db.py`, which replicates the bundled connectivity database N times.|
| `connectivity/` | The bundled connectivity database (`mf_grc.db`, 1070 MF + 3925 GrC; 4995 cells total) derived from the EM reconstruction of [Nguyen et al. 2023](https://github.com/htem/cb2_project_analysis). This is shipped as a data artifact. |
| `tests/`| A 50-ms smoke test used by CI.|


The container, the SLURM batch templates, the published benchmark CSVs, and the figure-generation script all live in the parent project:


| Topic | Parent path|
| ---- | ----------- |
| Container build pipeline      | `../build_container`, `../def_files/` |
| Benchmark CSVs (Fig 2, Fig 3) | `../results/` |
| Plot generation (R) | `../scripts/plots.R`|


## Running the Simulation

Run these commands from the parent repository root after building the container described in `../README.md`.

```bash
SIF=$HOME/containers/images/olaf.sif

# 1. Compile the NEURON mechanisms inside the container.
singularity exec --nv "$SIF" \
 nrnivmodl -coreneuron GranularLayerModel/src/mod

# 2. (Optional) scale the bundled connectivity database to the paper size.
# The base connectivity/mf_grc.db is shipped — there is no rebuild step.
python GranularLayerModel/scripts/scale_db.py \
 --input  GranularLayerModel/connectivity/mf_grc.db \
 --scale  280 \
 --output GranularLayerModel/connectivity/mf_grc_scaled_280.db

# 3. Run a 1-second simulation on a single GPU.
singularity exec --nv "$SIF" \
 mpiexec -n 4 python GranularLayerModel/src/network.py \
  --db GranularLayerModel/connectivity/mf_grc.db \
  -tstop 1000 -runtype coreneuron_gpu
```

## References

If you use this code or the container, please cite:

- O. James and S. Hong (2026) Container-Based Framework for Large-Scale Spiking Network Simulation, *submitted*.
- Nguyen et al. (2023) Structured cerebellar connectivity supports resilient pattern separation. Nature *613*, 543-9. (connectivity)
- Sudhakar et al. (2017). Spatiotemporal network coding of physiological mossy fiber inputs by the cerebellar granular layer. PLOS Comput Biol, *13*, e1005754. (cell models)


---
*Written by Oliver James and Sungho Hong, Center for Memory and Glioscience, Institute for Basic Science*

*May 2026*