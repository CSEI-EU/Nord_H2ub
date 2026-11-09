# SpineOpt → PyPSA benchmark (paper_energy_2024)

## What this project does

SpineOpt was used to plan and operate a power-to-methanol plant in western Denmark (DK1): solar
PV, grid connection, electrolyzer, CO₂ vaporizer, methanol reactor, distillation, steam plant,
hydrogen and methanol storage, and district-heat sales. For one year it decides how much of each
unit to build and how to run the plant hour by hour. It solves the year in 12 rolling windows
of 730 hours each.

This project rebuilds exactly the same model in **PyPSA**, reading SpineOpt's own Excel input.
It solves it the same way and compares every result against SpineOpt's exported output: cost per
window, investments, hourly flows and storage levels. Every difference is then explained, using
a fixed set of rules (the classifier). The goal is a benchmark: where the two tools agree,
where they differ, and why.

There are 43 input cases: the base case with 1–20 electrolyzer operating points, the years
2020–2023 and 2050, a PV-only case, and ±5 / ±10 % sensitivities on six parameters. Four of them
are excluded, leaving 39 enabled cases (see the decision log).

More detail for developers (SpineOpt conventions, known SpineOpt artefacts, package internals)
is in `CLAUDE.md` in the repository root.

---

## Folder and file map

Paths are relative to `Spine_Projects/06_thesis/benchmark_scenario/` unless they start with
`Spine_Projects/`.

**Inputs and SpineOpt outputs (not in this folder)**

| Path | What it is |
|---|---|
| `Spine_Projects/01_input_data/02_input_prepared/paper_energy_2024_inputs/` | The 43 SpineOpt input workbooks, `paper_energy_2024_input_<case>.xlsx`. One per case. |
| `Spine_Projects/03_output_data/03_runs_paper_energy_2024/01_output_raw/` | SpineOpt's exported results, `Output_exported_paper_energy_2024_<case>.xlsx`. One sheet per file; the sheet name carries the SpineOpt run timestamp. |

**This folder**

| File | What it is |
|---|---|
| `README.md` | This file. |
| `cases.csv` | The case list used by the batch runner. One row per case: name, input path, SpineOpt output path, `enabled`, and a note explaining any exclusion. |
| `paper_energy_2024_input_base_10op.xlsx`, `Output_exported_paper_energy_2024_base_10op.xlsx` | Local copies of the base case input and output. The regression test and `replica.py` use them. The output is byte-identical to the one in `01_output_raw/`. |
| `replica.py` | Runs one case and prints the full benchmark to the screen: tables, charts and a summary. A convenient front end for looking at a single case. |
| `preflight.py` | Checks the structure of all input workbooks against base_10op without solving anything: sheets, row offsets, objects, parameters, time settings, operating points. Writes `preflight_report.csv`. |
| `preflight_report.csv` | Output of `preflight.py`, one row per input workbook (see "Results files"). |
| `spineopt_pypsa_replica.ipynb` | The original notebook version of the replica. Kept for history only; not the reference. |
| `tests/test_base_10op.py` | Regression test: base_10op must reproduce the validated SpineOpt result. |
| `results/` | Everything the runs produce (see "Results files"). |

**The `benchmark/` package** (the model and all tooling; importing it never runs anything)

| File | What it does |
|---|---|
| `spine_input.py` | Reads a SpineOpt input workbook into one `SpineInput` object: units, nodes, connections, parameters, time series, rolling windows. Pure parsing; no modelling. |
| `spine_output.py` | Reads a SpineOpt output workbook into a `SpineOutput` object, with helpers to fetch one series or the per-window values. |
| `units.py` | Turns each SpineOpt unit into PyPSA ports and efficiencies by following the `fix_ratio_*` relations. Also builds the electrolyzer's operating-point segments. No PyPSA needed. |
| `model.py` | Builds the PyPSA network and its extra constraints. `check_supported` first refuses anything the replica cannot reproduce exactly. This is the core of the model. |
| `accounting.py` | Recomputes SpineOpt's cost terms per window (investment, FOM, variable, units_on, slack) from the solved network. Also maps PyPSA results back to SpineOpt's variables (flows, storage levels, investments). |
| `compare.py` | Builds the comparison tables (per window, investments, flows, blocks), using only objects present on both sides. |
| `classify.py` | Classifies every window's cost difference with rules R1–R6 and R4b (see below). |
| `run_case.py` | Runs one case end to end: parse, check, build, solve all windows, compare, classify, write results. Also a command-line tool. |
| `batch.py` | Runs many cases from `cases.csv`: one process each, in parallel, resumable. Then collects everything into tidy tables. |
| `reclassify.py` | Re-runs the classifier on saved results without solving, then re-collects the tables. |
| `output_scan.py` | Scans all SpineOpt outputs for negative storage levels and non-zero slack. No solving. |
| `native.py` | Optional cross-check: re-solves window 1 with PyPSA's built-in piecewise efficiency instead of the segment links. |
| `charts.py` | The two charts `replica.py` shows. |
| `settings.py` | The `Settings` with all run options and their defaults (see "Settings"). |
| `results.py` | The `CaseResult` object and how it is written to disk. |
| `errors.py` | `UnsupportedStructure`, raised instead of silently building a wrong model. |

---

## Data flow

```
  input workbook (.xlsx)                          SpineOpt output (.xlsx)
  paper_energy_2024_input_<case>.xlsx             Output_exported_paper_energy_2024_<case>.xlsx
            │                                                  │
            ▼                                                  ▼
   spine_input.read_input ──► SpineInput           spine_output.read_output ──► SpineOutput
            │                                                  │
            ▼                                                  │
   units.py      unit → PyPSA ports, segments                  │
   model.check_supported   (refuse what cannot be exact)       │
   model.build_network     PyPSA network + constraints         │
            │                                                  │
            ▼                                                  │
   run_case: solve window 1 … 12 (carry storage and capacity)  │
            │                                                  │
            ▼                                                  │
   accounting.py  SpineOpt cost terms, flows, investments ─────┤
            │                                                  │
            ▼                                                  ▼
   compare.py  per window / investments / flows / blocks  ◄────┘
            │
            ▼
   classify.py  class + rule per window
            │
            ▼
   results/cases/<case>/   per_window.csv, investments.csv, flows.csv, blocks.csv,
                           classified_windows.csv, meta.json, network.nc
            │
            ▼   (batch.py or reclassify.py, over all cases in cases.csv)
   results/*.parquet       one tidy table per kind, with case, family, parameter, ±%
```

---

## Commands you can run

**Environment.** Use the `master_thesis` conda environment (PyPSA 1.4, linopy 0.10, Gurobi,
HiGHS, pyarrow). `python` is not on the PATH on this machine, so either activate the environment
first (`conda activate master_thesis`) or call
`C:\Users\kar.eco\AppData\Local\miniconda3\envs\master_thesis\python.exe` directly.

Run every command below **from this folder** (`benchmark_scenario/`): the `benchmark` package is
found from here. Keep the laptop **awake and plugged in** during long runs, because Windows
Modern Standby suspends background work. Recorded solve times are wall-clock.

Durations below are those measured on this 12-core machine with Gurobi.

| Command | What it produces | Time |
|---|---|---|
| `python preflight.py` | `preflight_report.csv` and a printed summary of which inputs need special handling. No solving. | ~2 min |
| `python replica.py` | Runs base_10op, prints all comparison tables, shows two chart windows (close them to continue), runs the native piecewise check, and writes `results/base_10op/`. Environment variables: `INPUT_XLSX`, `SPINE_OUTPUT_XLSX` (relative to this folder), `SOLVER` (`gurobi`/`highs`), `MIPGAP`, `N_WINDOWS` (e.g. `1` for a quick test). For no chart windows, set `MPLBACKEND=Agg`. | ~3 min (1 window: ~1 min) |
| `python -m benchmark.run_case --input <in.xlsx> --output <out.xlsx> [--solver gurobi] [--out-dir benchmark_results] [--case NAME] [--threads N] [--mip-gap G] [--n-windows N] [--no-final-window-state-min] [--no-slacks] [--big X] [--native-check] [--quiet]` | One case into `<out-dir>/<case>/` (see "Results files"). | ~2–3 min alone; ~4 min when 3 run in parallel |
| `python -m benchmark.batch --cases cases.csv --dry-run [--workers 3]` | Lists every case with what it would do (run / skip / excluded), its family, and the thread allocation. Runs nothing. | seconds |
| `python -m benchmark.batch --cases cases.csv --workers 3 --max-gurobi-instances 3 --out-dir results` | Runs all enabled cases, one process each, 3 at a time with 4 solver threads each. Writes `results/cases/<case>/`, `results/logs/<case>.log`, `results/batch_status.csv`, then the tidy `results/*.parquet`. Re-running skips finished cases; add `--force` to redo them, `--only a,b` for a subset, `--threads N` to override the thread split. | ~56 min for 41 cases (the run of 2026-11-04) |
| `python -m benchmark.batch --cases cases.csv --out-dir results --collect-only` | Rebuilds only the `results/*.parquet` tables from what is already in `results/cases/`. | ~1 min |
| `python -m benchmark.reclassify --cases cases.csv --out-dir results [--only a,b]` | Re-classifies the saved results with the current rules: rewrites each `classified_windows.csv` and the classification in `meta.json`, then re-collects the parquet tables. No solving. | not timed; roughly 10–20 min for all cases (reads every workbook and network) |
| `python -m benchmark.output_scan --cases cases.csv --out results/spine_output_scan.csv` | The negative-storage and slack scan of all SpineOpt outputs. No solving. | a few minutes |
| `python tests/test_base_10op.py --solver gurobi` (or `--solver highs`) | Runs base_10op and prints PASS/FAIL for four checks: solved to optimality; exact windows within 0.01 €; artefact windows by the per-term rule; unit investments. With pytest installed, `pytest tests` runs the same checks (both solvers; choose with env `BENCH_SOLVERS`). | Gurobi ~3 min; HiGHS ~17 min |

---

## Settings

These are the fields of `benchmark.Settings`. Defaults are the values the replica was validated
with. From Python: `run_case(..., settings=Settings(n_windows=1))`. From the command line, only
the options listed in the `run_case` command above are available.

| Setting | Default | What it changes | Why it exists |
|---|---|---|---|
| `final_window_state_min` | `True` | Requires `ch3oh_st` to hold the largest `node_state_min` (969.25 MWh) also at the very last hour of the year. CLI: `--no-final-window-state-min`. | All 42 SpineOpt runs end at exactly that level, although the input only sets it at the ends of windows 1–11 (artefact 1). The true source in the Spine DB is still being checked; the rule lives in one function, `model.apply_final_window_state_min`. |
| `free_state_before_first_min` | `True` | Removes the storage lower bound (level ≥ 0) before the first `node_state_min` timestamp, i.e. in window 1. Python only. | Reproduces a SpineOpt **data artefact** (artefact 4): SpineOpt has no lower bound there and lets `ch3oh_st` go negative (2022, 2050). This is physically invalid. Set `False` for physically valid results. |
| `include_slacks` | `True` | Adds slack generators on every balanced node, at SpineOpt's `node_slack_penalty`. CLI: `--no-slacks`. | SpineOpt has them too. Without them, infeasible cases such as only_PV cannot be solved. |
| `n_windows` | `None` | Solves only the first N rolling windows (`None` = all 12). CLI: `--n-windows`. | Quick tests. |
| `big` | `1e6` | Size of the "unbounded" pieces: free sources/sinks on `balance_type_none` nodes, the daily-block demand buffer, the storage-loss links. CLI: `--big`. | PyPSA needs finite capacities; 1e6 is far above any real flow. |
| `solver_options` | `None` | Extra solver options, merged over the defaults. Defaults: Gurobi `MIPGap 1e-10, TimeLimit 3000, OutputFlag 0`; HiGHS `mip_rel_gap 1e-10, time_limit 3000, presolve on`. CLI: `--mip-gap`, `--threads`. | Same gap and time limit as SpineOpt's own `db_mip_solver_options`. |
| `native_piecewise_check` | `False` | Also re-solves window 1 with PyPSA's native piecewise efficiency, as a cross-check of the segment formulation. CLI: `--native-check`. | Confidence check; `replica.py` turns it on. |

Fixed values in the classifier (`benchmark/classify.py`, not settings): exact-cost tolerance
0.01 €, hourly-series tolerance 1e-3, dispatch tolerance 0.05 %, solver feasibility tolerance
1e-6 MWh, unit tolerance 1e-6.

---

## Results files

### Per case: `results/cases/<case>/`

**`per_window.csv`**: one row per rolling window. Costs in €. Prefix `pypsa_` = the replica,
`spine_` = SpineOpt, `diff_` = PyPSA − SpineOpt.

| Column | Meaning |
|---|---|
| `window`, `start`, `hours` | Window number (1–12), first hour, length in hours. |
| `pypsa_unit_investment`, `pypsa_storage_investment`, `pypsa_connection_investment` | Investment cost paid in that window (connection investment is always 0). |
| `pypsa_fom` | Fixed O&M on installed unit capacity × hours of the window. |
| `pypsa_variable`, `pypsa_units_on`, `pypsa_slack` | Variable cost (grid, district heat, vom), cost of the reactor being online, slack penalty. |
| `pypsa_total`, `pypsa_operating` | Total; total minus investments. |
| `spine_unit_investment`, `spine_storage_investment`, `spine_connection_investment`, `spine_total` | SpineOpt's own exported values. |
| `spine_fom` | Derived: same formula as the replica, applied to SpineOpt's own installed capacities. |
| `spine_slack` | Derived: penalty × SpineOpt's exported slack (weighted by block length on daily-block nodes). |
| `spine_variable`, `spine_units_on` | Empty: SpineOpt does not export them separately. |
| `spine_operating` | SpineOpt total minus its investment terms. |
| `spine_variable_units_on`, `pypsa_variable_units_on` | Variable + units_on combined, for both. SpineOpt's is derived as total − investments − FOM − slack. |
| `diff_unit_investment`, `diff_storage_investment`, `diff_fom`, `diff_variable_units_on`, `diff_slack`, `diff_total` | PyPSA − SpineOpt per term. |
| `rel_diff_total_pct` | `diff_total` as % of SpineOpt's window total. |

**`investments.csv`**: one row per unit and storage.

| Column | Meaning |
|---|---|
| `variable` | `units_invested`, or `storages_invested (cum.)` for storages. |
| `object` | Unit or storage name. |
| `spine`, `pypsa`, `diff` | Units invested over the solved horizon, as a fraction of a candidate unit (storages: cumulative), and PyPSA − SpineOpt. |

**`flows.csv`**: one row per compared hourly series (unit flows, connection flows, storage levels).

| Column | Meaning |
|---|---|
| `variable`, `object`, `node`, `direction` | Which SpineOpt series (e.g. `unit_flow`, `electrolyzer`, `power`, `from`). |
| `spine_sum`, `pypsa_sum` | Sum over all solved hours (MWh, t or kg). |
| `max_abs_hourly_diff` | Largest single-hour difference. |
| `hourly_corr` | Correlation of the two hourly series (empty if one is constant). |
| `sum_rel_diff_pct` | Relative difference of the sums, %. |

**`blocks.csv`**: one row per daily block, for deliveries into the methanol demand node and for storage levels at block ends.

| Column | Meaning |
|---|---|
| `block_node`, `block`, `block_end` | The node on the daily block (`ch3oh_demand`), block number, last hour of the block. |
| `kind` | `delivery` (energy delivered in the block) or `node_state` (storage level at the block end). |
| `object`, `node` | Connection and source node for deliveries; the storage for levels. |
| `spine`, `pypsa`, `diff` | Values and PyPSA − SpineOpt. |

**`classified_windows.csv`**: one row per window: the class and the evidence behind it (rules below).

| Column | Meaning |
|---|---|
| `window`, `start`, `spine_total`, `pypsa_total`, `diff_total` | As in `per_window.csv`. |
| `gap_spine`, `gap_pypsa` | Relative MIP gaps used: SpineOpt's from its input, PyPSA's = max(option, achieved). |
| `gap_tolerance` | (gap_spine + gap_pypsa) × \|objective\|, in €. Differences below this are solver tolerance. |
| `slack_tolerance` | Max slack penalty × 1e-6 MWh × hours, in €. Slack noise below this is solver tolerance. |
| `max_hourly_series_diff`, `max_diff_series` | Largest hourly difference of any compared series in the window, and which series. |
| `spine_storage_rebuy`, `spine_unit_rebuy` | How much more SpineOpt spent on storage / units in the window than PyPSA (€). |
| `storage_peak_excess_MWh` | How much more PyPSA stores than SpineOpt's window peak, when SpineOpt's capacity had fallen. |
| `fom_skip_bound` | The most FOM SpineOpt can save on capacity it bought more of than PyPSA (€). |
| `class`, `rule`, `rule_origin` | The result, the rule that gave it, and whether that rule was designed up front ("design (pilot)") or added after seeing a case ("post-hoc (2020_10op)"). |
| `also_consistent_with` | Other rules the window also satisfies. |
| `shift_detail` | For R4b: which unit shifted, from which window to which, and by how much. |
| `termination_condition`, `window_status` | Solver result of the window (`optimal`, or `time_limit`). |
| `spine_total_ex_slack`, `pypsa_total_ex_slack`, `diff_ex_slack`, `rel_diff_ex_slack_pct`, `class_ex_slack`, `rule_ex_slack` | Only for cases with slack: the same comparison without the slack penalty term. |
| `diff_variable_units_on`, `diff_unit_investment`, `diff_storage_investment`, `diff_fom`, `diff_slack` | Only for cases with slack: the per-term differences, repeated for convenience. |

**`meta.json`**: everything needed to know how the case was run:
- `status`: `ok`, or `ok_time_limit` if some window stopped at the time limit (listed in `windows_at_time_limit`).
- `solver`: requested and used, and the options.
- `windows`: per window: status, solver result, solve time (s), objective, achieved gap, model size (variables, constraints, binaries).
- `solve_seconds_total`, `run_seconds_total`.
- `objective_sum`: Σ SpineOpt, Σ PyPSA and their difference.
- `packages`: Python and package versions.
- `input` / `spine_output`: path and SHA-256 of both files, plus the SpineOpt sheet name and run timestamp.
- `settings`.
- `workarounds`: every modelling workaround applied, in words.
- `ignored_parameters`: parameters present but deliberately not modelled, with the reason.
- `skipped_energy_price_columns`, `skipped_comparisons`: anything missing on one side.
- `spine_cost_terms`: which SpineOpt cost outputs were found or derived.
- `classification`: rule notes, class counts, and R4b details.
- `units_invested`, `storages_invested`.

**`network.nc`**: the solved PyPSA network (open with `pypsa.Network("network.nc")`).

**`native_piecewise_check.csv`**: only with `--native-check`. Window-1 operating cost and electrolyzer output for SpineOpt, the replica, and the native piecewise version.

### Over all cases: `results/`

| File | Content |
|---|---|
| `per_window.parquet`, `investments.parquet`, `flows.parquet`, `blocks.parquet`, `classified_windows.parquet` | The per-case CSVs above stacked into one table, each row with extra columns `case`, `family` (`base_op`, `year`, `only_PV`, `sens`), `op_points`, `year`, `sens_parameter` (e.g. `elprice`), `sens_pct` (e.g. −5). Disabled cases are left out. |
| `cases.parquet` | One row per case in `cases.csv`: `enabled`, family columns, `status` (`ok`, `excluded`, `not_run`, …), `note` and `has_saved_results` (excluded cases), solver, `n_windows`, `windows_at_time_limit`, `solve_seconds`, `run_seconds`, `objective_spine`, `objective_pypsa`, `objective_diff`, `max_achieved_gap`, model size (`variables`, `constraints`, `binaries`), `class_counts`, input and output SHA-256, `spine_run_timestamp`, `packages`, `settings`. |
| `batch_status.csv` | One row per case of the batch runs: `status`, `returncode` (0 = success), `seconds`, `threads`, `log` path, `error_tail` (last log lines if it failed), `finished`. |
| `logs/<case>.log` | Everything the case process printed. |
| `spine_output_scan.csv` | One row per case and storage: `min_state` and when it occurs (`min_state_time`, `min_state_window`), `negative_hours`, `negative_windows`, `first_node_state_min`, `negative_only_before_first_min`, and per case `slack_total_MWh` and `slack_by_node`. |
| `spine_output_hashes.csv` | Per case: SHA-256 of the SpineOpt output file and of its numeric content, and the sheet name. Identical content means the same run. |
| `pilot/`, `batch_test/`, `direct_check/`, `base_10op/` | Earlier one-off runs (pilot cases, the batch-vs-direct consistency check, `replica.py`). Not used by the tables. |

**`preflight_report.csv`** (in this folder): one row per input workbook:
- **Structure vs base:** whether it is structurally identical to base (only values differ) or needs special handling, and why. The differences are listed per category: sheets, header layout, data start rows, objects, relationships, parameter names, parameter assignments.
- **Time:** model start/end, hours, leap year, roll_forward, windows, last window length, temporal blocks, series years.
- **Operating points:** count, values, whether the marginal efficiencies are non-increasing.
- **Storage time series:** where `node_state_min` and `fix_node_state` are set.

---

## How to add a new case

1. Put the SpineOpt input workbook in
   `Spine_Projects/01_input_data/02_input_prepared/paper_energy_2024_inputs/` as
   `paper_energy_2024_input_<case>.xlsx`.
2. Put SpineOpt's exported output in
   `Spine_Projects/03_output_data/03_runs_paper_energy_2024/01_output_raw/` as
   `Output_exported_paper_energy_2024_<case>.xlsx`.
3. Run `python preflight.py`. It picks up every workbook in the inputs folder. Check the new
   row in `preflight_report.csv`: "structurally identical to base", or the listed reasons.
4. Add one row to `cases.csv`: `case,input,output,enabled,note`, with the paths relative to this
   folder, written like the existing rows. `enabled` is `True`.
5. Run it alone first:
   `python -m benchmark.batch --cases cases.csv --only <case> --out-dir results`.
   If the input uses something the replica cannot reproduce exactly, it stops with an
   `UnsupportedStructure` error that lists what is unsupported. It never builds a different
   model silently.
6. Check `results/cases/<case>/classified_windows.csv`. Any `unexplained` window needs a look.
7. Name the case like the existing ones if you want the family columns filled in: `base_<N>op`,
   `<year>_<N>op`, `only_PV_<N>op`, `sens_<N>op_<parameter>_<05|10>p<up|down>`. Other names get
   `family = other`.

---

## How differences are classified

Every window's total cost difference (PyPSA − SpineOpt) gets exactly one class. The rules are
tried in this order; the first one that fits wins. `also_consistent_with` shows other rules that
fit too. The background artefacts are described in `CLAUDE.md` ("Known SpineOpt artefacts").

| Rule | Class | In plain language | Evidence it needs |
|---|---|---|---|
| R1 | `exact` | Both models give the same cost and the same hour-by-hour schedule. | Cost difference ≤ 0.01 €, and every compared hourly series within 1e-3 in that window. |
| R2 | `degenerate` | Same cost, different schedule: there are several equally good solutions, and the two solvers picked different ones. Typical cases: when within a day the methanol is delivered, or which node unmet demand is booked on. | Cost difference ≤ 0.01 €, but some hourly series differ by more than 1e-3. |
| R3 | `solver_tolerance` | The difference is smaller than what the solvers are allowed to leave on the table. | Either the difference ≤ (SpineOpt gap + PyPSA gap) × \|window cost\|, where PyPSA's gap is the achieved gap if that is larger (so time-limited windows are covered). Or the whole difference is in the slack term and below penalty × 1e-6 MWh × hours (slack at the solver's feasibility tolerance). |
| R4 | `artefact_storage` | SpineOpt "forgets" storage capacity between windows and buys it again; PyPSA keeps what it bought. So PyPSA is cheaper (artefact 2). | PyPSA cheaper; unit investment, FOM and slack equal; dispatch cost within 0.05 %. And in that window either SpineOpt re-buys storage, or PyPSA stores more than SpineOpt's peak while SpineOpt's capacity had fallen below what it had bought. |
| R4b | `artefact_storage_timing` (added after seeing 2020_10op) | A knock-on of R4: because storage differs, the two models buy the same unit capacity, but in different windows. | All four must hold. (1) Before the shift, SpineOpt's storage purchases already differ from PyPSA's. (2) Per unit, total investment is equal at the end, and the only difference is one amount moved from window a to window b. (3) The FOM difference in between equals FOM on exactly that moved capacity. (4) Over windows a to b, PyPSA is not more expensive in total. PyPSA's per-window investments are rebuilt from the dispatch and used only if they reproduce PyPSA's investment € exactly. |
| R5 | `artefact_units` | The same capacity effect as R4, but for units. SpineOpt re-buys units it had already bought, or saves FOM on capacity that has "fallen away". Seen only in only_PV. It can't be fully verified, because SpineOpt doesn't export its available units. | In the case as a whole, SpineOpt's total unit purchases exceed PyPSA's. In the window: either SpineOpt re-buys units and PyPSA is cheaper, or PyPSA is dearer by at most the FOM on that extra capacity, with investments equal. |
| R6 | `unexplained` | None of the above. Needs investigating: a replica error, a data problem, or a new artefact. | — |

For cases with slack (only_PV, and 2050 at noise level), each window is also classified without
the slack penalty term (`class_ex_slack`).

---

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
| 2026-11-09 | `2022_10op` and `2050_10op` disabled in `cases.csv` (excluded per supervisor). Case count: 43 files → 42 (OLD duplicate) → 41 (elprice_05pdown output is a copy) → **39 enabled cases**. | Negative `ch3oh_st` storage in the original SpineOpt run (no lower bound before the first `node_state_min`, artefact 4). A re-run with fixed input on the original SpineOpt version is pending (option A). Their saved PyPSA results stay in `results/cases/` but are left out of the comparison tables. |
