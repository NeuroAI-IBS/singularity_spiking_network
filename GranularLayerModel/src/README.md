# Simulation source (`src/`)

Python entry point, cell models, and NEURON MOD mechanisms. Intended to run **inside** the parent Singularity image after `nrnivmodl -coreneuron src/mod`.

Example (from the parent repository root):

```bash
singularity exec --nv "$SIF" \
    mpiexec -n 1 python GranularLayerModel/src/network.py \
        --db GranularLayerModel/connectivity/mf_grc.db \
        -tstop 1000 -runtype coreneuron_gpu
```

Container build, SLURM templates, and benchmark CSVs live in the parent project — see [`../README.md`](../README.md) and [SingularityCoreNeuron](https://github.com/NeuroAI-IBS/SingularityCoreNeuron).
