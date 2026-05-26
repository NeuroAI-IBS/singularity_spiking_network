# Connectivity database (`mf_grc.db`)

Bundled SQLite graph for the mossy-fibre → granule-cell microcircuit. **Not rebuilt** during a normal release checkout; use `scripts/scale_db.py` to replicate it for large-scale runs.

## Contents (base graph)

| Table / metric | Count |
| --- | --- |
| Mossy fibres (`cell_type = mf`) | 1070 |
| Granule cells (`cell_type = grc`) | 3925 |
| Total cells | 4995 |
| Synapses | 12387 |

## Provenance

- EM-derived binary graph `graph_mf_grc_binary_210519.gz` from [htem/cb2_project_analysis](https://github.com/htem/cb2_project_analysis) (Nguyen et al., 2023).
- During construction, **28 orphaned granule-cell GIDs** were removed (no valid incoming connectivity in the released graph). The one-shot builder script is archived on the `dev-archive` branch as `scripts/DatabaseMaking_mf_grc.py`.
- Schema includes `cell`, `synapse`, `gap`, `worker`, `synapse_type`, and `synapse_dynamics` with foreign keys and indexes on `synapse(source_gid)` and `synapse(target_gid)`.

## Scaling

```bash
python scripts/scale_db.py \
    --input connectivity/mf_grc.db \
    --scale 280 \
    --output connectivity/mf_grc_scaled_280.db
```

The scaler copies the full schema from the bundled database and replicates `cell` / `synapse` rows with contiguous GID offsets. It does **not** require the upstream NetworkX `.gz` file.

## Re-deriving from scratch

See `scripts/DatabaseMaking_mf_grc.py` on the internal `dev-archive` branch for the original NetworkX → SQLite pipeline.
