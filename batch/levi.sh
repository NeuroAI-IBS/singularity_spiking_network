#!/bin/bash

# ==========================
# User-configurable parameters
# ==========================
MAX_GPUS=2    # Maximum number of GPUs and tasks to test
TSTOP=1000    # Simulation stop time
RUNTYPE="coreneuron_gpu"  # ["coreneuron_gpu", "coreneuron_cpu", "neuron_serial", "neuron_parallel"]
ITERATIONS=1  # Number of complete runs

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

APPTAINER_IMAGE="${APPTAINER_IMAGE:-/home/oliver/Apptain/v100.sif}"  # container location
LOCAL_PROJECT_DIR="$REPO_ROOT"                                      # parent release checkout
APPTAINER_MOUNT="/mnt/SingularityCoreNeuron"                        # mount point inside container
PYTHON_SCRIPT="GranularLayerModel/src/network.py"                   # canonical release runner
DB_FILE="GranularLayerModel/connectivity/mf_grc.db"
OUT_DIR="results"

CSV_FILE="$REPO_ROOT/results/benchmark.csv"

sys="v100"  # What type of system it is

# ============================
# CSV Header for storing files
# ============================
if [ ! -f $CSV_FILE ]; then
    echo "System,Backend,Resource,TASK,SOLVER_TIME,WALL_TIME" > $CSV_FILE 
fi

echo -e "Compiling the mod files"
rm -rf x86_64/
apptainer exec --nv --bind "$LOCAL_PROJECT_DIR:$APPTAINER_MOUNT" --pwd "$APPTAINER_MOUNT" \
    "$APPTAINER_IMAGE" nrnivmodl -coreneuron GranularLayerModel/src/mod

# ==========================
# Repeat the whole process ITERATIONS times
# ==========================
for iteration in $(seq 1 $ITERATIONS); do
    echo -e "\n===== Starting iteration $iteration ====="

    # ==========================
    # Run the simulations
    # ==========================
    for g in $(seq $MAX_GPUS $MAX_GPUS); do
        t=$g  # Match tasks to GPUs

 		ERR_FILE="$REPO_ROOT/results/b_${t}_80.err"
        OUT_FILE="$REPO_ROOT/results/b_${t}_80.out"

        OUTFILE=$OUT_FILE
        ERRFILE=$ERR_FILE

        echo -e "\nStarting simulation: GPUs=$g, Rank(s)=$t, tstop=$TSTOP"
        start=$(date +%s)
        echo "Start time: $(date -d @$start '+%Y-%m-%d %H:%M:%S')"

        apptainer exec --nv --bind "$LOCAL_PROJECT_DIR:$APPTAINER_MOUNT" --pwd "$APPTAINER_MOUNT" "$APPTAINER_IMAGE" \
            mpiexec -n $t --allow-run-as-root \
            python "$PYTHON_SCRIPT" \
            -tstop $TSTOP -runtype $RUNTYPE --db "$DB_FILE" --out-dir "$OUT_DIR" \
            > "$OUTFILE" 2> "$ERRFILE"

        end=$(date +%s)
        total_runtime=$((end - start))
        total_runtime_fmt=$(date -ud "@$total_runtime" +'%H:%M:%S')
        
        # ==========================
        # Extract results
        # ==========================
        solver_time=$(grep -oP 'Solver Time\s*:\s*\K[0-9.]+' "$OUTFILE")

        # ==========================
        # Save results as CSV
        # ==========================
        echo "${sys},CORENEURON_GPU,${g},${t},${solver_time},${total_runtime_fmt} (${total_runtime}s)" >> $CSV_FILE
        echo -e "Simulation for g=$g, t=$t complete. Results appended to benchmark.csv"
    done
done

