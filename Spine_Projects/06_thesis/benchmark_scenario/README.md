# SpineOpt → PyPSA benchmark (paper_energy_2024)

The PyPSA replica of the SpineOpt power-to-methanol model and the tooling that benchmarks it
against SpineOpt's exported results. CLAUDE.md in the repository root documents the package, the
SpineOpt conventions, and the known SpineOpt artefacts in detail.

- `benchmark/`: importable package (`run_case`, `batch`, `classify`, `reclassify`, `output_scan`, …)
- `replica.py`: thin wrapper that runs one case and prints the benchmark
- `preflight.py`: structure check of all input workbooks (`preflight_report.csv`)
- `cases.csv`: case → input / SpineOpt output mapping used by the batch runner
- `tests/test_base_10op.py`: regression test
- `results/`: batch results (`cases/<case>/`, `logs/`, tidy `*.parquet`, scans)

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-11-03 | Refactor `replica.py` into the `benchmark/` package; `replica.py` becomes a thin wrapper. | Several cases in one process, no module-level state, testable. |
| 2026-11-04 | Window 11 of base_10op is a storage-artefact window, not an exact one. Exact windows: 1, 2, 3, 5, 8, 12; artefact windows: 4, 6, 7, 9, 10, 11. | Both Gurobi and HiGHS give −0.0196 € in window 11; PyPSA carries more `ch3oh_st` capacity there. |
| 2026-11-04 | Artefact windows are tested with a per-term rule, not 0.05 % of the window total. | A relative limit on the total breaks down for windows whose total is close to zero (base_10op window 9). |
| 2026-11-04 | `final_window_state_min = True` for all cases, as one setting (`model.apply_final_window_state_min`). | All 42 SpineOpt runs end at exactly 969.2544 MWh. The true source (probably a `cyclic_condition`) is still being checked in the Spine DB; a cyclic rule will replace this function. |
| 2026-11-04 | `free_state_before_first_min = True` reproduces SpineOpt **data artefact 4** (no lower bound on `ch3oh_st` before the first `node_state_min`, so negative storage). | Needed to benchmark 2022_10op / 2050_10op window 1 against SpineOpt. It is physically invalid; set it to `False` for physically valid results. |
| 2026-11-04 | Windows stopped by the time limit are kept, flagged `time_limit`, with their achieved gap. | A time limit is not a failure; the gap is recorded and R3 uses it. |
| 2026-11-04 | Window classifier `benchmark/classify.py`, rules R1–R6 (rule_origin "design (pilot)"). | Explicit, reproducible classification of every window difference. |
| 2026-11-04 | **R4b artefact_storage_timing** added *post hoc* (rule_origin "post-hoc (2020_10op)"), with four strict conditions (see `classify.py`). | In 2020_10op windows 9–11, SpineOpt and PyPSA buy the same unit capacity in different windows, a knock-on of SpineOpt's storage re-buy. R4b was written after seeing this case, so it is flagged as post-hoc. |
| 2026-11-04 | `sens_10op_elprice_05pdown` disabled in `cases.csv`. | Its SpineOpt output is value-identical to `sens_10op_elpricevar_05pdown`'s (all 67 series). Pricing the shared output's flows reproduces `total_costs` only with elpricevar's prices (12/12 windows within bounds, vs 0/12 for elprice). So elpricevar's output is correct and elprice's is the copy. The correct output must be re-exported before re-enabling. |
| 2026-11-04 | `sens_10op_demand_05pdown_OLD` disabled (kept, not deleted). | Identical duplicate of `sens_10op_demand_05pdown` (cell by cell). |
