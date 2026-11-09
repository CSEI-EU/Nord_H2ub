# CLAUDE.md

## Working agreement

- The user runs and analyses everything themself. Do not run batches, analyses or long solves
  unless explicitly asked.
- Ask before changing code. Explain every change in plain language.
- Keep changes small enough to review in one commit.

## Purpose

Benchmark SpineOpt against PyPSA. The replica rebuilds the SpineOpt power-to-methanol model
(`paper_energy_2024`) in PyPSA, reading SpineOpt's own Excel input. It solves the model the same
way as SpineOpt and compares the results with SpineOpt's exported output.

## Where things are

- **Input cases:** `Spine_Projects/01_input_data/02_input_prepared/paper_energy_2024_inputs/`.
  There are 43 workbooks named `paper_energy_2024_input_<case>.xlsx`:
  - `base_1op` … `base_10op`, `base_15op`, `base_20op` (number of electrolyzer operating points)
  - years `2020_10op` … `2023_10op` and `2050_10op`
  - `only_PV_10op`
  - `sens_10op_<param>_{05,10}p{up,down}`, where `<param>` is one of `demand`, `dhprice`, `eff`,
    `elprice`, `elpricevar`, `invc`
  - `sens_10op_demand_05pdown_OLD.xlsx` is a stale duplicate.
- **Replica and validation case:** `Spine_Projects/06_thesis/benchmark_scenario/`
  - `benchmark/` is the replica, as an importable package (see below).
  - `replica.py` is a thin wrapper that runs one case and prints the benchmark tables.
  - `preflight.py` checks every input workbook's structure against base_10op and writes
    `preflight_report.csv`. It solves nothing.
  - `tests/test_base_10op.py` is the regression test.
  - `paper_energy_2024_input_base_10op.xlsx` is a copy of the base_10op input.
  - `Output_exported_paper_energy_2024_base_10op.xlsx` is the SpineOpt output for base_10op.
  - `spineopt_pypsa_replica.ipynb` is the older notebook version. Do not treat it as the reference.
- The replica has only been validated on `base_10op`.

## The benchmark package

Importing any module in `benchmark/` has no side effects: nothing is read and nothing is solved.
There is no module-level state, so several cases can run in one process.

**Entry point:**

```python
from benchmark import Settings
from benchmark.run_case import run_case
r = run_case(input_xlsx, spine_output_xlsx, solver="gurobi", solver_options=None,
             settings=Settings(), out_dir="benchmark_results", case=None, log=None)
```

CLI: `python -m benchmark.run_case --input <in.xlsx> --output <Output_exported.xlsx> --solver gurobi`
(see `--help`). Run it from `benchmark_scenario/`, or put that folder on `PYTHONPATH`.

`run_case` returns a `CaseResult` and writes it to `<out_dir>/<case>/`:

| File | Content |
|---|---|
| `per_window.csv` | Cost terms per window for both models, plus `diff_*` per term. SpineOpt exports only its investment terms and `total_costs`. `spine_fom` is derived from SpineOpt's own `units_invested` with the replica's formula, and `spine_slack` from `node_slack_pos/neg` × penalty (block-weighted on coarser-block nodes). `spine_variable_units_on` = total − investments − FOM − slack. |
| `investments.csv` | Units and storages invested (storages cumulative) |
| `flows.csv` | Per variable/object/node/direction: sums, max hourly diff, hourly correlation |
| `blocks.csv` | Deliveries per coarser temporal block, and storage levels at block ends |
| `meta.json` | Status, solver and options, achieved gap, solve time and model size per window, package versions, SHA-256 of input and output, settings, workarounds, ignored parameters, skipped comparisons, SpineOpt run timestamp |
| `classified_windows.csv` | Per window: class and rule (`benchmark/classify.py`: R1 exact, R2 degenerate, R3 solver_tolerance, R4 artefact_storage, R4b artefact_storage_timing, R5 artefact_units, R6 unexplained; `rule_origin` marks R4b as post-hoc), the gap- and slack-implied tolerances, evidence columns, `also_consistent_with`, and for slack cases every comparison without the slack term (`*_ex_slack`, `class_ex_slack`) |
| `network.nc` | The solved PyPSA network |

The case name is the input file stem after `_input_`, e.g. `base_10op`.

**Modules:**

- `spine_input.py`: `read_sheets`, `parse_sheets`, `read_input` → `SpineInput`. Pure workbook
  parsing. `DATA_START_ROW` holds the fixed row offsets of the positional sheets.
- `spine_output.py`: `read_output` → `SpineOutput`, with `has`, `series`, `object_series`,
  `per_window` and `run_timestamp`.
- `units.py`: `flow_coefficients`, `unit_spec`, `unit_counts`, `operating_segments` → `Segments`,
  and `unit_specs`. No PyPSA dependency.
- `model.py`:
  - `check_supported` raises `UnsupportedStructure` for anything not reproduced exactly: unknown
    parameters, increasing marginal efficiencies, non-continuous investment, connection
    investment, and so on.
  - `build_network`, `block_ends`, `node_state_min`, `make_extra_functionality`.
- `accounting.py`: `window_costs`, which follows SpineOpt's cost conventions, plus `unit_flows`,
  `connection_flows`, `node_states` and `investments`.
- `compare.py`: data-driven comparison tables. Objects missing on either side are skipped and
  listed in `meta.json`.
- `classify.py`: window classification rules R1–R6 (written out in its docstring).
- `batch.py`: batch runner (see below). `output_scan.py`: scans SpineOpt outputs for negative states and slack.
- `reclassify.py`: re-classifies saved results from `network.nc` + CSVs (no solve) and re-collects the tables.
- `native.py`: optional cross-check of window 1 against PyPSA's native piecewise efficiency.
- `charts.py`: `plot_case(result)` returns matplotlib figures.
- `settings.py` / `results.py` / `errors.py`: `Settings`, `CaseResult`, `UnsupportedStructure`.

**Settings** (`benchmark.Settings`; defaults are the validated values):

| Field | Default | Meaning |
|---|---|---|
| `final_window_state_min` | `True` | Final-hour storage requirement (artefact 1), True for all cases. The rule lives only in `model.apply_final_window_state_min`. |
| `free_state_before_first_min` | `True` | Reproduce SpineOpt's data artefact 4: no state lower bound before the first `node_state_min` timestamp (physically invalid; `False` = e ≥ 0) |
| `include_slacks` | `True` | ±slack generators at `node_slack_penalty` |
| `n_windows` | `None` | `None` = all windows. Use `1` for a quick test (about 25 s with Gurobi). |
| `big` | `1e6` | Size of unbounded sources/sinks, demand buffers and loss links |
| `solver_options` | `None` | Merged over `DEFAULT_SOLVER_OPTIONS[solver]` (gap 1e-10, time limit 3000 s) |
| `native_piecewise_check` | `False` | Also run the native piecewise cross-check |

**How to run.** Use the `master_thesis` conda env, which has PyPSA 1.4, linopy 0.10, Gurobi and
HiGHS. On this machine `python` is not on the PATH, so call the interpreter directly:

```
C:\Users\kar.eco\AppData\Local\miniconda3\envs\master_thesis\python.exe Spine_Projects/06_thesis/benchmark_scenario/replica.py
```

`replica.py` keeps its environment variables: `INPUT_XLSX`, `SPINE_OUTPUT_XLSX`, `SOLVER`,
`MIPGAP` and `N_WINDOWS`. Relative paths resolve against the script's folder. It writes to
`benchmark_scenario/results/<case>/` and turns on the native check. `plt.show()` blocks until the
chart windows are closed; for headless runs, set `MPLBACKEND=Agg`.

**Batch runs.** `cases.csv` (in `benchmark_scenario/`) maps each case to its input and SpineOpt
output, relative to the CSV's folder. Its `enabled` column excludes four cases, leaving 39
enabled: 43 files → 42 (`sens_10op_demand_05pdown_OLD`, an identical duplicate) → 41
(`sens_10op_elprice_05pdown`, whose SpineOpt output is a copy of elpricevar_05pdown's) → 39
(`2022_10op` and `2050_10op`: negative `ch3oh_st` storage in the original SpineOpt run, excluded
per supervisor; a re-run with fixed input on the original SpineOpt version is pending, option A).
SpineOpt outputs live in
`Spine_Projects/03_output_data/03_runs_paper_energy_2024/01_output_raw/Output_exported_paper_energy_2024_<case>.xlsx`.

`python -m benchmark.batch --cases cases.csv [--only a,b] [--workers W] [--threads T]
[--max-gurobi-instances G] [--force] [--dry-run] [--collect-only] [--out-dir results]`

- Each case runs as its own `python -m benchmark.run_case` process. Failures are recorded in
  `batch_status.csv` and the batch continues.
- Logs go to `logs/<case>.log` and case results to `cases/<case>/`.
- It is resumable: a case whose `meta.json` status is `ok`/`ok_time_limit` is skipped unless
  `--force`.
- Threads default to CPUs // workers, and workers × threads may not exceed the CPU count (12 on
  this machine).
- At the end it writes tidy `per_window`, `investments`, `flows`, `blocks`, `classified_windows`
  and `cases` parquet tables to `--out-dir`. Each row carries `family` (base_op / year / only_PV /
  sens), `op_points`, `year`, `sens_parameter` and `sens_pct` (±%), parsed from the case name.
- Disabled cases appear only in `cases.parquet` (status `excluded`, with their note), never in the
  comparison tables.

**Keep the machine awake during long runs.** Modern Standby suspends background processes: the
pilot only_PV_10op window 6 took 2,691 s wall-clock, versus 7 s when awake. Recorded solve times
are wall-clock.

`results/spine_output_scan.csv` (`python -m benchmark.output_scan`) lists the min state per storage
and the slack per case. Negative states occur only in 2022/2050 (`ch3oh_st`, window 1, before the
first `node_state_min`). Slack occurs only in only_PV_10op (90,494 MWh).
`results/spine_output_hashes.csv` holds file and numeric-content hashes of all SpineOpt outputs.
The only identical pair by content is `sens_10op_elprice_05pdown` = `sens_10op_elpricevar_05pdown`.
The shared output belongs to elpricevar (its prices reconcile `total_costs` in 12/12 windows), so
elprice_05pdown is disabled until its output is re-exported.

The decision log is in `Spine_Projects/06_thesis/benchmark_scenario/README.md`.

A window stopped by the time limit with a feasible solution is kept, not treated as a failure. It
is flagged `time_limit` in `meta.json`, with its achieved gap, and the case status becomes
`ok_time_limit`.

**Regression test.** pytest is not installed in `master_thesis`, so run the test file directly:
`python tests/test_base_10op.py --solver gurobi` (or `--solver highs`). With pytest installed, use
`pytest tests` (env `BENCH_SOLVERS=gurobi,highs`).

**preflight.py** imports `benchmark.spine_input` and `benchmark.units`, so it parses the inputs
exactly as the replica does. Its `hardcoded_names_missing` column still checks the object names
that the pre-refactor `replica.py` hardcoded. The package no longer uses those names; the column
was kept so the report stayed byte-identical through the refactor.

## Model (DK1 e-methanol plant)

- Solar PV: 304 MW, existing.
- Grid import/export at spot price, plus an 11.70 €/MWh tariff on import.
- Electrolyzer with 10 operating-point segments. They use marginal efficiencies from the
  user_constraint `effcurve_electrolyzer`.
- CO2 vaporizer.
- Methanol reactor:
  - integer online variable
  - min down time 48 h
  - ramp, start-up and shut-down limits 0.5
  - `units_on_cost` = spot price
- Distillation tower and electric steam plant.
- H2 storage and methanol storage.
- District-heat sales.
- Methanol demand of 20.19 MW on a daily temporal block.
- Capacity expansion with continuous investment.
- Rolling horizon: `roll_forward = 730 h`, giving 12 windows.

## SpineOpt conventions (confirmed from the base_10op output; keep these exactly)

- `unit_investment_cost` and `storage_investment_cost` are charged per whole unit
  (fraction × cost), once, in the window the investment is made. There is no annuity.
- `fom_cost` [€/MW/h] is charged on installed unit capacity × hours in each window.
  SpineOpt does NOT apply `fom_cost` on connections.
- Daily blocks restart at each window start: 730 h = 30 × 24 h plus one 10 h block.
- Electrolyzer segment coefficients are marginal efficiencies. The full-load average is 0.742.
- `fix_ratio_X_Y(n1, n2)` means flow(n1) = R × flow(n2).
- `frac_state_loss` is applied to the end-of-step state. The replica uses an exact transform:
  `standing_loss = l/(1+l)`, plus charge/discharge links with efficiencies `1/(1+l)` and `1+l`.
- The committable reactor is effectively forced to the full 52 MW, so the replica fixes it at
  that size.

## Known SpineOpt artefacts

1. **Final-window storage minimum.** The base_10op run kept `ch3oh_st` ≥ 969.25 MWh at the last
   hour of window 12. The exported input only sets `node_state_min` at the ends of windows 1–11.
   `FINAL_WINDOW_STATE_MIN = True` reproduces this for base_10op. Where it comes from in the
   SpineOpt DB is unknown.
   **Decision (pilot step): always True, for now.** In all 42 SpineOpt runs `ch3oh_st` ends at
   exactly 969.2544 MWh. In 41 of them the stock fell during the final window and was rebuilt to
   that value at the last hour. only_PV_10op stays at 969.25 throughout the final window, so it is
   consistent but not conclusive. The real source is still being checked in the Spine DB (likely a
   `cyclic_condition` on `node__temporal_block` for ch3oh_st). The rule lives only in
   `benchmark.model.apply_final_window_state_min`, so it can be replaced by an end ≥ start rule
   without touching anything else.
2. **Storage capacity between windows.** SpineOpt lets storage capacity
   (`storages_invested_available`) fall between rolling windows at no cost, and then pays to
   re-invest. The replica keeps capacity cumulative, which makes it about €318 cheaper over the
   year in base_10op. In base_10op this affects windows 4, 6, 7, 9, 10 and 11.
   It also applies to units: in only_PV_10op, units are invested in later windows. SpineOpt's
   `units_invested_available` falls between windows, so SpineOpt saves FOM (PyPSA is about 75 €
   dearer in windows 5, 7, 9, 12) and re-buys units (PyPSA cheaper in windows 6, 8, 10, 11). The
   cumulative SpineOpt `units_invested` then exceeds `candidate_units` (dist_tower 1.155 > 1).
   SpineOpt FOM derived from cumulative `units_invested` overstates SpineOpt's real FOM in that
   case, because `units_invested_available` is not exported.
   Knock-on via investment timing (2020_10op windows 9–11, rule R4b, added post hoc): the
   same unit capacity is bought two windows later in PyPSA (W9 → W11; Σ −124.59 €). R4b's four
   conditions are in `classify.py`. PyPSA's per-window unit investments are reconstructed from the
   dispatch and accepted only if they reproduce PyPSA's unit investment € (true for all 41 cases,
   mismatch ≤ 1e-9 €).
   Two signatures of this artefact: SpineOpt re-buys storage in a window, or PyPSA stores more
   than SpineOpt's window peak while SpineOpt's peak is below its cumulative purchases (its
   capacity fell without a re-buy, e.g. base_10op windows 4 and 11).
3. **Delivery timing.** Methanol delivery timing within a daily block is degenerate: different
   schedules have equal cost. Compare deliveries on block totals. Likewise, in slack-dominated
   cases (only_PV_10op) the split of unmet demand between `ch3oh` and `ch3oh_demand` is degenerate,
   since both carry the same 1e8 penalty. Compare total slack energy instead.
4. **No state lower bound before the first `node_state_min` (SpineOpt data artefact).**
   SpineOpt takes the storage lower bound from the `node_state_min` time series. Before its
   first timestamp (the end of window 1) the series has no value, so SpineOpt puts no lower
   bound on `ch3oh_st` and the storage can go negative. That is physically invalid. It happens in
   2050_10op (down to −643.9 MWh) and 2022_10op (−636.7 MWh).
   A physically correct model (e ≥ 0) is more expensive there: 2050 window 1 +22,819.66 €, 2022
   window 1 +6,788.33 €. To benchmark against SpineOpt, the replica *reproduces* the artefact with
   `free_state_before_first_min = True`, and both windows then match to the cent. Set it to `False`
   for physically valid results.
   **Decision (supervisor): 2022_10op and 2050_10op are excluded** (`enabled=False` in
   `cases.csv`) because their original SpineOpt runs have negative storage. A re-run with fixed
   input on the original SpineOpt version is pending (option A).
5. **Numerical noise from the 1e8 slack penalty.** Slack at the solver's feasibility tolerance
   (~1e-9 MWh) shows up as cents in the slack term (2050_10op window 1: −0.14 €). In slack-dominated
   windows (only_PV_10op, totals around 1e11–1e12 €) differences of tens of euros are within the
   tolerance.

## Reference result (base_10op, HiGHS, gap 1e-10)

- Σ objective: SpineOpt 1,921,371.89 €, PyPSA 1,921,039.49 €.
- base_10op total Σ difference €332.40, of which ≈ €318 is the storage re-purchase artefact.
- **Exact windows** (match to within 0.01 €): 1, 2, 3, 5, 8, 12.
- **Storage-artefact windows** (artefact 2: PyPSA carries more `ch3oh_st` capacity than SpineOpt, so
  PyPSA is cheaper): 4, 6, 7, 9, 10, 11. PyPSA − SpineOpt per window: −1.53, −50.49, −182.75,
  −63.26, −34.35, −0.02 €.
- Gurobi and HiGHS give the same per-window costs, to within 1.5e-8 €.
- Unit investments are identical:

  | Unit | Invested |
  |---|---|
  | electrolyzer | 0.82803 |
  | co2_vaporizer | 0.06176 |
  | dist_tower | 0.46896 |
  | reactor | 1 |
  | steam_plant | 0.01758 |

- `ch3oh_st` cumulative storage investment: 0.90738 in SpineOpt vs 0.64817 in PyPSA
  (artefact 2).

## Tooling

- PyPSA ≥ 1.4 and linopy ≥ 0.10.
- Gurobi preferred, HiGHS as the fallback.
- Always call `n.optimize(..., io_api="direct", include_objective_constant=False)`.
- Add custom constraints through `extra_functionality`.
