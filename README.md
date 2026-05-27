# Container-Based Framework for Large-Scale Spiking Network Simulation

This repository provides examples of how to build and use Singularity/Apptainer containers with GPU and MPI support for running large-scale spiking neuronal network simulations.

The top level repository has the container build script and example definition files for containers in different situations. An example spiking neural network model based on the cerebellar granular layer is in [`GranularLayerModel/`](GranularLayerModel/).

## Repository Contents

| Path | Purpose |
| --- | --- |
| `build_container` | Builds a sandbox and optional `.sif` image from one `.def` file. |
| `def_files/` | Example definition files and templates for different machines. |
| `batch/` | SLURM batch scripts for benchmark runs. |
| `results/` | Published benchmark CSVs used by `scripts/plots.R`. |
| `scripts/plots.R` | Recreates benchmark figure panels from committed CSVs. |
| `GranularLayerModel/` | Simulation runner, MOD files, connectivity DB, scaling helper, and tests. |

## Prerequisites

- Singularity or Apptainer on the machine that will build the image. The examples below use `apptainer`, which is the command called by `build_container`.

- For GPU-enabled builds, you also need an NVIDIA HPC SDK installer tarball compatible with the CUDA/NVHPC version used in your definition file. Some templates copy this installer from the host through the `%files` section.

- For HPC builds using SLURM-aware MPI, collect the host cluster's PMI/PMIx headers and libraries before building. These files are cluster-specific and must match the environment where the container will run.

## Definition Files

The files in `def_files/` are intentionally environment-specific. Start from the closest template, save it as a concrete `.def` file, then build that file with `build_container`.

| File | Use |
| --- | --- |
| `local.def.template` | Local workstation template. It builds OpenMPI inside the container without copying host PMI files. Edit the NVIDIA HPC SDK installer path and CUDA architecture. |
| `hpc.def.template` | HPC template with commented `%files` lines for host PMI libraries. Use this when the cluster requires SLURM PMI compatibility. |
| `olaf.def` | Concrete Olaf/IBS HPC example with copied SLURM PMI files and NVIDIA HPC SDK 25.1 / CUDA 12.6. |
| `levi.def` | Concrete Titan V example using NVIDIA HPC SDK 25.5 / CUDA 12.9, with CUDA architecture `70`. |

## Writing a Definition File

Each definition file has the same core sections:

- `%files` copies host files into the image before `%post` runs. Use this for local NVIDIA HPC SDK tarballs and, on HPC systems, SLURM PMI headers and libraries.
- `%post` installs system packages, Python packages, OpenMPI, NVIDIA HPC SDK components, NEURON, and CoreNEURON.
- `%environment` exports runtime paths so `python`, `nrnivmodl`, `mpiexec`, NEURON, CoreNEURON, CUDA, and OpenMPI are available when the container runs.
- `%labels` records metadata.
- `%runscript` defines the default command when the image is executed directly.

When adapting a `.def` file for a new machine, check these items carefully:

- `Bootstrap` and `From`: use `ubuntu:24.04` if the file installs NVHPC from a tarball, or an NVIDIA NVHPC base image if you want the SDK preinstalled.
- NVIDIA HPC SDK installer path in `%files`: the host path must exist on the build machine, for example `/path/to/nvhpc_2025_255_Linux_x86_64_cuda_12.9.tar.gz /opt/nvhpc_sdk.tar.gz`.
- `HPCSDK_VERSION` and `CUDA_VERSION`, or hard-coded paths such as `/opt/nvidia/hpc_sdk/Linux_x86_64/25.5/cuda/12.9`.
- OpenMPI version and configure flags. HPC builds commonly need `--with-pmi=/usr --with-pmi-libdir=/lib64`.
- `CMAKE_CUDA_ARCHITECTURES`: set this for your GPU generation, such as `70` for Titan V, `75` for Titan RTX, or `90` for H100.
- Python packages installed into `/opt/venv`. The model runner needs at least `numpy`, `pandas`, `matplotlib`, and `mpi4py`.
- Runtime exports in `%environment`: keep `PATH`, `LD_LIBRARY_PATH`, `PYTHONPATH`, `NMODLHOME`, and `NMODL_PYLIB` consistent with the install paths used in `%post`.

## Local Workstation Template

Use `def_files/local.def.template` when the image will run on a local workstation or a machine that does not require host SLURM PMI libraries inside the container.

1. Copy the template:
```bash
cp def_files/local.def.template def_files/my_workstation.def
```
2. Build the image:
```bash
./build_container def_files/my_workstation.def
```
This creates:
```text
$HOME/containers/images/my_workstation/
$HOME/containers/images/my_workstation.sif
```

## HPC Template With SLURM PMI

Use `def_files/hpc.def.template` when running MPI jobs through SLURM on an HPC cluster. The key difference from the local template is that host PMI headers and libraries are copied into the image and OpenMPI is configured with PMI support.

1. On the target cluster, identify the MPI launcher support:

```bash
srun --mpi=list
```

2. Locate the PMI/SLURM headers and libraries on the cluster:

```bash
find /usr/include /usr/local/include -name 'pmi*.h'
find /lib64 /usr/lib64 /usr/local/lib64 -name 'libpmi*.so*'
find /usr/lib64/slurm /usr/local/lib64 -name 'libslurm_pmi.so*'
```

3. Copy the required files into a local staging directory on the build machine, for example:

```text
slurm-pmi-for-container/
├── include/
│   ├── pmi.h
│   └── pmi2.h
└── lib64/
    ├── libpmi.so
    ├── libpmi.so.0
    ├── libpmi2.so
    ├── libpmi2.so.0
    └── libslurm_pmi.so
```

4. Copy the template:

```bash
cp def_files/hpc.def.template def_files/my_cluster.def
```

5. In `%files`, uncomment and edit the PMI paths so they point at your staging directory, then edit the NVIDIA HPC SDK installer path:

```text
/path/to/slurm-pmi-for-container/include/pmi.h /usr/include/slurm/pmi.h
/path/to/slurm-pmi-for-container/include/pmi2.h /usr/include/slurm/pmi2.h
/path/to/slurm-pmi-for-container/lib64/libpmi.so /lib64/libpmi.so
/path/to/slurm-pmi-for-container/lib64/libpmi.so.0 /lib64/libpmi.so.0
/path/to/slurm-pmi-for-container/lib64/libpmi2.so /lib64/libpmi2.so
/path/to/slurm-pmi-for-container/lib64/libpmi2.so.0 /lib64/libpmi2.so.0
/path/to/slurm-pmi-for-container/lib64/libslurm_pmi.so /usr/lib64/slurm/libslurm_pmi.so
```

6. Confirm OpenMPI is configured with PMI support:

```text
./configure --prefix=/opt/openmpi --with-pmi=/usr --with-pmi-libdir=/lib64
```

7. Set `CMAKE_CUDA_ARCHITECTURES` for the cluster GPUs and build:
```bash
./build_container def_files/my_cluster.def
```

The output name is derived from the definition filename, so `def_files/my_cluster.def` produces:

```text
$HOME/containers/images/my_cluster/
$HOME/containers/images/my_cluster.sif
```

## Building With `build_container`

`build_container` accepts exactly one definition file and creates output under an application directory. By default, that directory is `$HOME/containers`.

```bash
./build_container [OPTIONS] def_files/name.def
```

Options:

| Option | Description |
| --- | --- |
| `-a, --app-dir DIR` | Base output directory. Defaults to `$HOME/containers`. |
| `-s, --only-sandbox` | Build only the writable sandbox directory. |
| `--dry-run` | Print the `apptainer build` commands without running them. |
| `-h, --help` | Show command help. |

The script runs two stages:

1. Build a sandbox:
```bash
apptainer build --fix-perms --sandbox "$APP_DIR/images/name" def_files/name.def
```
2. Convert the sandbox to a `.sif` image unless `--only-sandbox` is used:

```bash
apptainer build --fix-perms "$APP_DIR/images/name.sif" "$APP_DIR/images/name"
```

Examples:

```bash
# Build with default output directory.
./build_container def_files/levi.def

# Build under a custom directory.
./build_container -a /scratch/$USER/containers def_files/my_cluster.def

# Inspect commands before building.
./build_container --dry-run def_files/my_cluster.def

# Build only a sandbox for debugging.
./build_container --only-sandbox def_files/my_cluster.def
```

## Granular Layer Model

The model used for the manuscript lives in `GranularLayerModel/`. This subproject owns the network runner, NEURON MOD files, bundled connectivity database, database scaling helper, and smoke tests.

After building a container, see [`GranularLayerModel/README.md`](GranularLayerModel/README.md) for compiling mechanisms, scaling the connectivity database, and running the simulation.

## Troubleshooting

- If the build cannot find a file listed in `%files`, use an absolute host path and confirm the file exists on the build machine.
- If MPI jobs fail on an HPC cluster, confirm the copied PMI libraries came from the same cluster environment and that OpenMPI was configured with the matching PMI flags.
- If GPU compilation fails, check that `CMAKE_CUDA_ARCHITECTURES` matches the target GPU and that `CUDA_HOME` points at the CUDA version installed by NVHPC.
- If `nrnivmodl` or Python imports fail at runtime, inspect `%environment` and confirm `PATH`, `LD_LIBRARY_PATH`, `PYTHONPATH`, `NMODLHOME`, and `NMODL_PYLIB` match the paths created in `%post`.

## References

- [CoreNEURON Documentation](https://github.com/BlueBrain/CoreNeuron)
- [Singularity / Apptainer Documentation](https://apptainer.org/docs/)
- [NVIDIA HPC SDK](https://developer.nvidia.com/hpc-sdk)
- [OpenMPI Documentation](https://www.open-mpi.org/doc/)

---
*Written by Oliver James and Sungho Hong, Center for Memory and Glioscience, Institute for Basic Science*

*May 2026*