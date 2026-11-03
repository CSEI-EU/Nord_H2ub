# CLAUDE.md

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
| `per_window.csv` | Cost terms per window for both models: unit, storage and connection investment, fom, variable, units_on, slack, total, operating. The SpineOpt side only has its investment terms and `total_costs`; its other terms are NaN. |
| `investments.csv` | Units and storages invested (storages cumulative) |
| `flows.csv` | Per variable/object/node/direction: sums, max hourly diff, hourly correlation |
| `blocks.csv` | Deliveries per coarser temporal block, and storage levels at block ends |
| `meta.json` | Status, solver and options, achieved gap, solve time and model size per window, package versions, SHA-256 of input and output, settings, workarounds, ignored parameters, skipped comparisons, SpineOpt run timestamp |
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
- `native.py`: optional cross-check of window 1 against PyPSA's native piecewise efficiency.
- `charts.py`: `plot_case(result)` returns matplotlib figures.
- `settings.py` / `results.py` / `errors.py`: `Settings`, `CaseResult`, `UnsupportedStructure`.

**Settings** (`benchmark.Settings`; defaults are the validated values):

| Field | Default | Meaning |
|---|---|---|
| `final_window_state_min` | `True` | Copy the last `node_state_min` onto the final hour (artefact 1; open per case) |
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
   **Open question, to be settled in the pilot step:** the pre-flight only shows that no input
   file contains a final-hour `node_state_min`. It does not show whether SpineOpt enforced one.
   Decide each case separately, from that run's output (the `ch3oh_st` level at the last hour).
   Do not assume `FINAL_WINDOW_STATE_MIN = True` holds for all cases.
2. **Storage capacity between windows.** SpineOpt lets storage capacity
   (`storages_invested_available`) fall between rolling windows at no cost, and then pays to
   re-invest. The replica keeps capacity cumulative, which makes it about €318 cheaper over the
   year in base_10op.
3. **Delivery timing.** Methanol delivery timing within a daily block is degenerate: different
   schedules have equal cost. Compare deliveries on block totals.

## Reference result (base_10op, HiGHS, gap 1e-10)

- Σ objective: SpineOpt 1,921,371.89 €, PyPSA 1,921,039.49 €.
- base_10op total Σ difference €332.40, of which ≈ €318 is the storage re-purchase artefact.
- Windows 1, 2, 3, 5, 8, 11 and 12 match to the cent.
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
