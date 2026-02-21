Place evaluated GTAF artifacts here for local runtime enforcement.

Expected files:
- drc.json
- sb/SB-LOCAL-RACHEL.json
- dr/DR-COMMAND-EXEC.json
- rb/RB-TIM-LOCAL.json

Layout notes:
- JSON only (no YAML)
- SDK loader resolves references by category (`sb`, `dr`, `rb`) from subfolders.
- `drc.json` references artifact IDs in `refs`.
- artifact filenames are `<artifact_id>.json`.
